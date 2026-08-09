from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Security Monitor Service','Security alerts, privacy incidents and response triggers.',[router('security_monitor_service','privacy.security_incident.v1')])
