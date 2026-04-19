import sys
from pathlib import Path
from pycardano import ScriptAll, ScriptPubkey, VerificationKeyHash, ScriptNofK

parties = [
    "639db51a8544327d7dcb53716d50d89132e0ddf112a75da110ac4b60",
    "f44a82965bd613ae0c72fd0b4bb98cdb54e5611d18c42828f796be4f",
    "92494d751e507df3a9e59499268a3381eaaf1cd6323c0a0a3cbe603b",
    "217e2c9a1b6773228c6a126d660dc983a1017d39e74d96dd132867b0"
]

vkhs = [VerificationKeyHash.from_primitive(p) for p in parties]
pks = [ScriptPubkey(v) for v in vkhs]

# Config's script: Threshold 1, All parties
s_config = ScriptAll([ScriptNofK(1, pks)])
print(f"Config 1-of-4 multisig hash: {s_config.hash().payload.hex()}")

# User's address hash from logs was: 78014389e44a10e6c164b309aa1dff27bcd61e79ab832fc9fb995b3e
# Let's see if 7801... is just a 1-of-1 script of the FIRST party
s_1of1 = ScriptAll([ScriptPubkey(vkhs[0])])
print(f"1-of-1 ScriptAll([p1]) hash: {s_1of1.hash().payload.hex()}")

# Or maybe just the PKH itself?
print(f"PKH[0]: {vkhs[0].payload.hex()}")
