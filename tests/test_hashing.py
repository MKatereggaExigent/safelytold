from safelytold_common.hashing import MerkleProofStep, chained_hash, merkle_root, sha256_bytes, verify_proof


def test_hash_chain_changes_with_record() -> None:
    genesis = '00' * 32
    assert chained_hash(genesis, {'x': 1}) != chained_hash(genesis, {'x': 2})


def test_merkle_root_is_deterministic() -> None:
    leaves = [sha256_bytes(b'a'), sha256_bytes(b'b')]
    assert merkle_root(leaves) == merkle_root(leaves)
    assert merkle_root(leaves) != merkle_root(reversed(leaves))


def test_single_leaf_proof() -> None:
    leaf = sha256_bytes(b'a')
    assert verify_proof(leaf, [], leaf)
