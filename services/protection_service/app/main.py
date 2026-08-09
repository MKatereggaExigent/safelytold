from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Protection Service','Protection plans, safe contact, retaliation check-ins and escalation.',[router('protection_service',None)])
