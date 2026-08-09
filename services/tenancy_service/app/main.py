from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Tenancy Service','Tenants, legal entities, regions, organisational units, deployment metadata.',[router('tenancy_service',None)])
