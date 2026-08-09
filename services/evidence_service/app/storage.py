from __future__ import annotations

import asyncio
import os
from io import BytesIO

import boto3


def _client():
    return boto3.client(
        's3',
        endpoint_url=os.getenv('S3_ENDPOINT_URL'),
        aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
        region_name=os.getenv('S3_REGION', 'us-east-1'),
    )


def _put(key: str, data: bytes, media_type: str, sha256: str) -> None:
    params = {
        'Bucket': os.getenv('S3_EVIDENCE_BUCKET', 'safelytold-evidence'),
        'Key': key,
        'Body': BytesIO(data),
        'ContentType': media_type,
        'Metadata': {'sha256': sha256, 'copy-kind': 'sealed-original'},
    }
    kms_key = os.getenv('S3_KMS_KEY_ID')
    if kms_key:
        params.update({'ServerSideEncryption': 'aws:kms', 'SSEKMSKeyId': kms_key})
    _client().put_object(**params)


async def store_sealed(key: str, data: bytes, media_type: str, sha256: str) -> None:
    await asyncio.to_thread(_put, key, data, media_type, sha256)
