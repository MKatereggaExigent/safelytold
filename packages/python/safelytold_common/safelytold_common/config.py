from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
 model_config=SettingsConfigDict(env_file=".env",extra="ignore",case_sensitive=False)
 service_name:str="unnamed-service"; environment:str="development"; log_level:str="INFO"
 database_url:str="postgresql+asyncpg://safelytold:safelytold_dev_only@postgres:5432/postgres"
 rabbitmq_url:str="amqp://safelytold:safelytold_dev_only@rabbitmq:5672/%2F"
 jwt_issuer:str="http://keycloak:8080/realms/safelytold"; jwt_audience:str="safelytold-api"
 dev_auth_bypass:bool=False; dev_tenant_id:str="00000000-0000-0000-0000-000000000001"
 public_tenant_id:str="00000000-0000-0000-0000-000000000001"
 blockchain_anchor_token:str=""
 reporting_email_address:str=""
 toll_free_number:str=""
 receiving_provider_name:str=""
 channel_webhook_secret:str=""
 intake_service_url:str="http://intake-service:8014"
 reporter_identity_service_url:str="http://reporter-identity-service:8012"
 admin_superuser_emails:str="michael.kateregga@datasqan.com"
 # JSON list of tenants to auto-provision on tenancy-service boot, e.g.
 # [{"id":"<stable-uuid>","slug":"example-za","display_name":"Example ZA Tenant","home_region":"za"},
 #  {"id":"<stable-uuid>","slug":"example-ca","display_name":"Example CA Tenant","home_region":"ca"}]
 # The id is the tenant_id used by Keycloak claims and RLS; keep it stable.
 seed_tenants:str="[]"
@lru_cache
def settings()->Settings:return Settings()
