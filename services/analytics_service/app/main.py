from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Analytics Service','Cohort-thresholded de-identified metrics and board summaries.',[router('analytics_service',None)])
