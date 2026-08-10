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
 admin_superuser_emails:str="michael.kateregga@datasqan.com"
@lru_cache
def settings()->Settings:return Settings()
