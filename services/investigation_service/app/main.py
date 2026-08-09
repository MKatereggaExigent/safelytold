from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Investigation Service','Plans, interviews, findings, decisions, remedies and appeals.',[router('investigation_service','case.finding_submitted.v1')])
