#!/usr/bin/env python3
"""
main.py  -- ERC-20 Balance Checker

Example:
    python main.py \
        --token 0xe24e207c6156241cAfb41D025B3b5F0677114C81 \
        --addresses addresses.txt
"""
from __future__ import annotations

import argparse
import os
from decimal import Decimal, getcontext
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from web3 import Web3

# ───────── ERC-20 Minimal ABI ─────────
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
]
# ──────────────────────────────────────


def read_addresses(path: Path) -> List[str]:
    """Return non-empty / non-comment lines as wallet addresses."""
    if not path.exists():
        raise FileNotFoundError(f"Address file not found: {path}")
    with path.open() as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def get_rpc_url() -> str:
    """Load RPC_URL from environment (.env handled via python-dotenv)."""
    load_dotenv()
    rpc = os.getenv("RPC_URL")
    if not rpc:
        raise EnvironmentError("RPC_URL is missing! Set it in your .env file.")
    return rpc


def fetch_balance(
    w3: Web3,
    token_addr: str,
    wallet: str,
    decimals: int,
) -> Decimal:
    token = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)
    raw = token.functions.balanceOf(Web3.to_checksum_address(wallet)).call()
    return Decimal(raw) / Decimal(10**decimals)


def main() -> None:
    parser = argparse.ArgumentParser(description="ERC-20 Balance Checker")
    parser.add_argument(
        "--token",
        required=True,
        help="ERC-20 token contract address (e.g. INTMAX)",
    )
    parser.add_argument(
        "--addresses",
        default="addresses.txt",
        help="Path to text file containing wallet addresses",
    )
    args = parser.parse_args()

    w3 = Web3(Web3.HTTPProvider(get_rpc_url()))
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to RPC. Check RPC_URL.")

    token = w3.eth.contract(address=Web3.to_checksum_address(args.token), abi=ERC20_ABI)
    decimals: int = token.functions.decimals().call()
    symbol: str = token.functions.symbol().call()

    getcontext().prec = 40  # high precision
    total = Decimal(0)

    for addr in read_addresses(Path(args.addresses)):
        bal = fetch_balance(w3, args.token, addr, decimals)
        total += bal
        print(f"{addr} : {bal:,.4f} {symbol}")

    print(f"Total: {total:,.4f} {symbol}")


if __name__ == "__main__":
    main()
