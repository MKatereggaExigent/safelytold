from safelytold_common.service import create_app
from .operations import router as operations_router
from .channels import router as channels_router

app=create_app('Integration Service','Signed, idempotent reporting-channel adapters and operational assurance.',[operations_router, channels_router])
