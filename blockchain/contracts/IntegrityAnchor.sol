// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.28;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";

/// @notice Stores content-free integrity commitments. Never submit personal or case data.
contract IntegrityAnchor is AccessControl, Pausable {
    bytes32 public constant ANCHOR_ROLE = keccak256("ANCHOR_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    struct AnchorRecord {
        bytes32 tenantCommitment;
        bytes32 batchCommitment;
        bytes32 merkleRoot;
        bytes32 rootKind;
        uint64 leafCount;
        uint64 anchoredAt;
        address submitter;
    }

    mapping(bytes32 => AnchorRecord) private anchors;

    error RootAlreadyAnchored(bytes32 merkleRoot);
    error EmptyRoot();
    error InvalidLeafCount();
    error AnchorNotFound(bytes32 merkleRoot);

    event RootAnchored(
        bytes32 indexed merkleRoot,
        bytes32 indexed tenantCommitment,
        bytes32 indexed batchCommitment,
        bytes32 rootKind,
        uint64 leafCount,
        uint64 anchoredAt,
        address submitter
    );

    constructor(address administrator, address anchorWriter) {
        _grantRole(DEFAULT_ADMIN_ROLE, administrator);
        _grantRole(ANCHOR_ROLE, anchorWriter);
        _grantRole(PAUSER_ROLE, administrator);
    }

    function anchor(
        bytes32 tenantCommitment,
        bytes32 batchCommitment,
        bytes32 merkleRoot,
        bytes32 rootKind,
        uint64 leafCount
    ) external onlyRole(ANCHOR_ROLE) whenNotPaused {
        if (merkleRoot == bytes32(0)) revert EmptyRoot();
        if (leafCount == 0) revert InvalidLeafCount();
        if (anchors[merkleRoot].anchoredAt != 0) revert RootAlreadyAnchored(merkleRoot);
        AnchorRecord memory record = AnchorRecord({
            tenantCommitment: tenantCommitment,
            batchCommitment: batchCommitment,
            merkleRoot: merkleRoot,
            rootKind: rootKind,
            leafCount: leafCount,
            anchoredAt: uint64(block.timestamp),
            submitter: msg.sender
        });
        anchors[merkleRoot] = record;
        emit RootAnchored(merkleRoot, tenantCommitment, batchCommitment, rootKind, leafCount, record.anchoredAt, msg.sender);
    }

    function getAnchor(bytes32 merkleRoot) external view returns (AnchorRecord memory) {
        AnchorRecord memory record = anchors[merkleRoot];
        if (record.anchoredAt == 0) revert AnchorNotFound(merkleRoot);
        return record;
    }

    function exists(bytes32 merkleRoot) external view returns (bool) {
        return anchors[merkleRoot].anchoredAt != 0;
    }

    function pause() external onlyRole(PAUSER_ROLE) { _pause(); }
    function unpause() external onlyRole(PAUSER_ROLE) { _unpause(); }
}
