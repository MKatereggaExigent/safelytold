from safelytold_common.generic import router
from safelytold_common.service import create_app
app=create_app('Notification Service','Privacy-safe notifications with no sensitive content.',[router('notification_service',None)])
