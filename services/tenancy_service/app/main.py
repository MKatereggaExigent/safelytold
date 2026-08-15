from safelytold_common.generic import router as generic_router
from safelytold_common.service import create_app

from .admin import router as admin_router
from .assurance_admin import router as assurance_admin_router
from .seeder import seed_tenants_from_env
from .reporting import router as reporting_router
from .sales import router as sales_router

app = create_app(
    'Tenancy Service',
    'Tenants, legal entities, regions, organisational units, deployment metadata.',
    [generic_router('tenancy_service', None), admin_router, assurance_admin_router, reporting_router, sales_router],
    on_ready=seed_tenants_from_env,
)
