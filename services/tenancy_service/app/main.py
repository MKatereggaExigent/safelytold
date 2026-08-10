from safelytold_common.generic import router as generic_router
from safelytold_common.service import create_app

from .admin import router as admin_router

app = create_app(
    'Tenancy Service',
    'Tenants, legal entities, regions, organisational units, deployment metadata.',
    [generic_router('tenancy_service', None), admin_router],
)
