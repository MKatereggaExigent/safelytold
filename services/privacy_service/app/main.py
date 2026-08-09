from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Privacy Service','Consent, DSAR, retention, correction, residency and breach cases.',[router('privacy_service',None)])
