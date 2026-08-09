from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Case Service','Cases, allegations, triage, assignments and closure metadata.',[router('case_service','case.assignment_changed.v1')])
