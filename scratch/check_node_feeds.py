import asyncio
import aiohttp
import json

async def check_node(url, policy_id):
    endpoint = f"{url.rstrip('/')}/odv/feed"
    payload = {
        "oracle_nft_policy_id": policy_id,
        "tx_validity_interval": {
            "start": 0,
            "end": 9999999999999 # Some future time
        }
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(endpoint, json=payload) as response:
                print(f"Node {url} Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Node {url} Response: {json.dumps(data, indent=2)}")
                else:
                    print(f"Node {url} Error: {await response.text()}")
        except Exception as e:
            print(f"Node {url} Failed: {e}")

async def main():
    # Gold Oracle Policy ID
    gold_policy = "63fb25158563dd7e45300fe997604f00579f14dacc3edc414e8d8755"
    print("Checking Gold Oracle Nodes...")
    await check_node("http://localhost:8000", gold_policy)
    await check_node("http://localhost:8001", gold_policy)

if __name__ == "__main__":
    asyncio.run(main())
