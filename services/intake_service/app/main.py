from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Intake Service','Private journals and anonymous, confidential or identified reports.',[router('intake_service','case.reported.v1',public_kinds={'report'})])
