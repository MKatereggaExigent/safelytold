from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

ABI = [
    {
        'inputs': [
            {'internalType': 'bytes32', 'name': 'tenantCommitment', 'type': 'bytes32'},
            {'internalType': 'bytes32', 'name': 'batchCommitment', 'type': 'bytes32'},
            {'internalType': 'bytes32', 'name': 'merkleRoot', 'type': 'bytes32'},
            {'internalType': 'bytes32', 'name': 'rootKind', 'type': 'bytes32'},
            {'internalType': 'uint64', 'name': 'leafCount', 'type': 'uint64'},
        ],
        'name': 'anchor',
        'outputs': [],
        'stateMutability': 'nonpayable',
        'type': 'function',
    }
]


@dataclass(frozen=True)
class Receipt:
    transaction_hash: str
    chain_id: str
    block_number: int


def _evm_dependencies() -> tuple[Any, Any]:
    """Load the optional EVM client only when BLOCKCHAIN_MODE=evm is exercised."""
    try:
        from eth_account import Account
        from web3 import Web3
    except ImportError as exc:  # pragma: no cover - exercised only in EVM deployments
        raise RuntimeError(
            'EVM mode requires the declared web3 dependency; install the project dependencies first.'
        ) from exc
    return Account, Web3


def _bytes32_text(value: str, web3: Any) -> bytes:
    encoded = value.encode('utf-8')
    if len(encoded) > 32:
        return web3.keccak(encoded)
    return encoded.ljust(32, b'\0')


def _require_env(name: str) -> str:
    value = os.environ.get(name, '')
    if not value:
        raise RuntimeError(f'{name} is not configured; set it when BLOCKCHAIN_MODE=evm')
    return value


def _submit(tenant_hash: str, batch_id: str, root: str, kind: str, leaf_count: int) -> Receipt:
    Account, Web3 = _evm_dependencies()
    rpc = _require_env('BLOCKCHAIN_RPC_URL')
    try:
        address = Web3.to_checksum_address(_require_env('BLOCKCHAIN_CONTRACT_ADDRESS'))
    except ValueError as exc:  # pragma: no cover - invalid configuration
        raise RuntimeError('BLOCKCHAIN_CONTRACT_ADDRESS is not a valid EVM address') from exc
    private_key = _require_env('BLOCKCHAIN_SIGNER_PRIVATE_KEY')
    web3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 20}))
    if not web3.is_connected():
        raise RuntimeError('Ledger RPC is unavailable')
    account = Account.from_key(private_key)
    contract = web3.eth.contract(address=address, abi=ABI)
    transaction = contract.functions.anchor(
        bytes.fromhex(tenant_hash),
        Web3.keccak(text=batch_id),
        bytes.fromhex(root),
        _bytes32_text(kind, Web3),
        leaf_count,
    ).build_transaction(
        {
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address, 'pending'),
            'chainId': web3.eth.chain_id,
            'gas': int(os.getenv('BLOCKCHAIN_GAS_LIMIT', '250000')),
            'maxFeePerGas': web3.to_wei(os.getenv('BLOCKCHAIN_MAX_FEE_GWEI', '2'), 'gwei'),
            'maxPriorityFeePerGas': web3.to_wei(
                os.getenv('BLOCKCHAIN_PRIORITY_FEE_GWEI', '1'), 'gwei'
            ),
        }
    )
    signed = account.sign_transaction(transaction)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    if receipt.status != 1:
        raise RuntimeError('Integrity anchor transaction reverted')
    return Receipt(
        transaction_hash=tx_hash.hex(),
        chain_id=str(web3.eth.chain_id),
        block_number=receipt.blockNumber,
    )


async def submit_anchor(
    tenant_hash: str,
    batch_id: str,
    root: str,
    kind: str,
    leaf_count: int,
) -> Receipt:
    return await asyncio.to_thread(_submit, tenant_hash, batch_id, root, kind, leaf_count)
