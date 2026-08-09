from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Integration Service','HRIS, SCIM, SSO, messaging, voice, EAP, regulators and webhooks.',[router('integration_service',None)])
