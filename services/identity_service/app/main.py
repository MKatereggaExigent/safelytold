from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Staff Identity Service','Staff identities, roles, invitations, SCIM linkage, separation of duties.',[router('identity_service',None)])
