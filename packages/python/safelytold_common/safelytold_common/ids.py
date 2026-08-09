import secrets
def public_case_code()->str:return secrets.token_urlsafe(20)
def recovery_secret()->str:return secrets.token_urlsafe(32)
