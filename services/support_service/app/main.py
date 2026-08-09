from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Support Circle Service','Consent-limited supporters and referral directory.',[router('support_service',None)])
