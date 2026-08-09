from __future__ import annotations

import asyncio
import os
import socket


def _scan(data: bytes) -> dict[str, str]:
    host = os.getenv('CLAMAV_HOST')
    if not host:
        return {'status': 'not_configured'}
    port = int(os.getenv('CLAMAV_PORT', '3310'))
    with socket.create_connection((host, port), timeout=15) as connection:
        connection.sendall(b'zINSTREAM\0')
        for offset in range(0, len(data), 65536):
            chunk = data[offset:offset + 65536]
            connection.sendall(len(chunk).to_bytes(4, 'big') + chunk)
        connection.sendall((0).to_bytes(4, 'big'))
        result = connection.recv(4096).decode('utf-8', errors='replace')
    if 'FOUND' in result:
        return {'status': 'malware_detected', 'engine': 'clamav'}
    if 'OK' in result:
        return {'status': 'clean', 'engine': 'clamav'}
    return {'status': 'scan_error', 'engine': 'clamav'}


async def scan_bytes(data: bytes) -> dict[str, str]:
    return await asyncio.to_thread(_scan, data)
