#!/usr/bin/env sh
set -eu
mc alias set local http://minio:9000 safelytold safelytold_dev_only_change_me
mc mb --ignore-existing local/safelytold-evidence
mc version enable local/safelytold-evidence
# Production: create Object Lock-enabled buckets at creation time and enforce retention policies.
