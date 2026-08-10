#!/usr/bin/env sh
set -eu
mc alias set local http://minio:9000 "${S3_ACCESS_KEY:-safelytold}" "${S3_SECRET_KEY:-safelytold_dev_only_change_me}"
mc mb --ignore-existing local/safelytold-evidence
mc version enable local/safelytold-evidence
# Production: create Object Lock-enabled buckets at creation time and enforce retention policies.
