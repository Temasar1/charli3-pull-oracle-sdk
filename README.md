# ODV Multisig Charli3 Offchain Core

> **Fork Notice:** This is a fork of the official [Charli3 Pull Oracle SDK](https://github.com/Charli3-Official/charli3-pull-oracle-sdk) by Charli3-Official. For the original project description, full documentation, and upstream releases, visit the [original repository README](https://github.com/Charli3-Official/charli3-pull-oracle-sdk#readme). This fork adapts the SDK to run with BlockFrost as the sole chain backend (no local Kupo/Ogmios required), adds an automated price-feed pull script for Cardano Preprod, and includes fixes for deterministic feed ordering and clock-skew alignment between the SDK and oracle nodes.

## Automated Price Feed Updates (Auto-Pull)

This fork ships `scripts/auto_pull.sh` — a shell loop that pushes fresh Gold (XAU) and Silver (XAG) prices on-chain every 8 minutes using the ODV client flow.

### Prerequisites

- Oracle node(s) running and accessible (e.g. `http://localhost:8000`, `http://localhost:8001`)
- `pull_gold.yaml` and `pull_silver.yaml` configured at the project root (see examples below)
- Poetry environment installed (`poetry install`)

### Pull configuration files

Create `pull_gold.yaml` and `pull_silver.yaml` at the project root. These are standard ODV client configs pointing to your running oracle nodes:

```yaml
# pull_gold.yaml
network:
  network: "testnet"
  blockfrost:
    project_id: "preprod<YOUR_BLOCKFROST_PROJECT_ID>"

oracle_address: "addr_test1..."        # Script address holding C3RA/C3AS UTxOs
policy_id: "<GOLD_ORACLE_POLICY_ID>"   # Policy ID minted at oracle deploy time

wallet:
  mnemonic: "your 24 word mnemonic phrase here"
  # OR use key files:
  # payment_skey_path: "keys/payment.skey"

odv_validity_length: 120000  # 2 minutes — must be <= time_uncertainty_aggregation on-chain

nodes:
  - root_url: "http://localhost:8000"   # Gold oracle node
    pub_key: "<NODE_FEED_VKH_HEX>"      # 28-byte feed verification key hash (hex)

reference_script:
  address: "addr_test1..."              # Address where reference script UTxO lives
  utxo_reference:
    transaction_id: "<SCRIPT_UTXO_TX_HASH>"
    output_index: 0
```

```yaml
# pull_silver.yaml — same structure, different policy_id and node endpoint
network:
  network: "testnet"
  blockfrost:
    project_id: "preprod<YOUR_BLOCKFROST_PROJECT_ID>"

oracle_address: "addr_test1..."
policy_id: "<SILVER_ORACLE_POLICY_ID>"

wallet:
  mnemonic: "your 24 word mnemonic phrase here"

odv_validity_length: 120000

nodes:
  - root_url: "http://localhost:8001"   # Silver oracle node
    pub_key: "<NODE_FEED_VKH_HEX>"

reference_script:
  address: "addr_test1..."
  utxo_reference:
    transaction_id: "<SCRIPT_UTXO_TX_HASH>"
    output_index: 0
```

### Running the auto-pull loop

```bash
# Start the loop (runs until killed — use screen/tmux for long-running sessions)
bash scripts/auto_pull.sh
```

What the script does each cycle:

1. Calls `charli3 client send --config pull_gold.yaml --no-wait` — contacts the Gold node for a signed feed, builds the ODV transaction, collects node signatures, and submits to chain without waiting for confirmation.
2. Waits 30 seconds for mempool propagation.
3. Calls `charli3 client send --config pull_silver.yaml --no-wait` for Silver.
4. Sleeps 8 minutes, then repeats.

The `--no-wait` flag means the script does not block on-chain confirmation before proceeding. If you need confirmed-state guarantees between pulls, remove it.

### Running a single pull manually

```bash
# Gold
poetry run charli3 client send --config pull_gold.yaml

# Silver
poetry run charli3 client send --config pull_silver.yaml
```

---

## Changes from Upstream

The following changes were made to the [original Charli3 Pull Oracle SDK](https://github.com/Charli3-Official/charli3-pull-oracle-sdk) to make it work with BlockFrost as the sole chain backend and to fix correctness issues discovered during Preprod testing.

### `chain_query.py` — BlockFrost UTxO reference lookup + clock alignment

**Added `get_utxo_by_ref()`:** The original SDK only had `get_utxo_by_ref_kupo()`, which requires a running Kupo indexer. A new unified `get_utxo_by_ref()` async method was added that tries Kupo first and falls back to the BlockFrost API, enabling reference script UTxO lookups without a local node.

**`use_wall_clock: bool = False`:** Changed from `True`. When `True`, the SDK computes `validity_start` from the machine's wall clock, which can be ~30–60 seconds ahead of Cardano's chain time (the time oracle nodes use for their feed timestamps). This caused the node to reject feed requests with `TimestampError: Timestamp outside validity interval`. Setting this to `False` derives the current time from the latest chain slot, keeping the SDK and node clocks in sync.

### `oracle/utils/common.py` — BlockFrost compatibility + deterministic feed ordering

**`get_reference_script_utxo`:** Changed `chain_query.get_utxo_by_ref_kupo(...)` to `await chain_query.get_utxo_by_ref(...)` so the reference script lookup works with BlockFrost.

**`build_aggregate_message` sort key:** Changed from `key=lambda x: x[1]` (sort by feed value only) to `key=lambda x: (x[1], x[0].payload)` (sort by feed value, then VKH bytes as tie-breaker). The on-chain Aiken validator requires a fully deterministic ordering; when two nodes submit the same price the previous sort was non-deterministic and could cause script evaluation failures.

### `oracle/utils/rewards.py` — Reward distribution correctness

**`calculate_reward_distribution`:** Refactored from iterating the full allowed-nodes set (which added zero-reward entries for every node not submitting this round) to starting from a `deepcopy` of `in_distribution` and incrementing only nodes that passed IQR/divergency consensus. This matches on-chain accounting and avoids polluting the reward map with zero entries.

### `oracle/aggregate/builder.py` — Redeemer fix + diagnostic output

**Account redeemer fix:** Changed `Redeemer(OdvAggregateMsg.create_sorted(sorted_feeds))` to `Redeemer(OdvAggregate.create_sorted(sorted_feeds))`. `OdvAggregateMsg` (CONSTR_ID 1, no fields) does not have a `create_sorted` method; the account UTxO redeemer must be `OdvAggregate` (CONSTR_ID 0, carries the sorted feed map).

**Diagnostic print blocks:** Added `=== [DIAGNOSTIC] ===` console output showing on-chain settings, current account/agg-state values, and node feed ordering at transaction build time. These aid debugging without requiring a full trace.

### `platform/auth/token_script_builder.py` — Single-key native script support

`_create_multisig` now returns a bare `ScriptPubkey` when `threshold == 1` and there is only one signer, instead of wrapping it in `ScriptNofK(1, [...])`. `get_script_config` was also extended to parse `ScriptPubkey` directly (both at the top level and nested inside `ScriptAll`), covering scripts produced by TypeScript tooling that omit the N-of-K wrapper for single signers.

### `cli/oracle.py` — Platform script local reconstruction

Added `_get_platform_script_with_fallback()`: when the multisig config lists the parties locally, the platform native script is reconstructed in-process and its hash is verified against the configured platform address. This avoids an on-chain lookup that can fail when the script has not yet been revealed to the chain, while still falling back to the chain query if the local hash does not match.

### New files

| File | Purpose |
|---|---|
| `scripts/auto_pull.sh` | Shell loop that pushes Gold and Silver price feeds on-chain every 8 minutes |
| `pull_gold.yaml` | ODV client config for the Gold (XAU) oracle on Preprod |
| `pull_silver.yaml` | ODV client config for the Silver (XAG) oracle on Preprod |

---

## License

This repository is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**, inherited from the upstream Charli3 Pull Oracle SDK. See the [LICENSE](LICENSE) file for the full terms.

Full commercial licenses available upon request by contacting sales@charli3.io.
