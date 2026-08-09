.PHONY: validate test lint up infra core down blockchain
validate:
	python -m compileall -q packages services workers scripts tests
	python scripts/validate_foundation.py
test:
	pytest -q
lint:
	ruff check .
infra:
	docker compose up -d postgres-core postgres-vault postgres-audit rabbitmq temporal-postgres temporal temporal-ui minio keycloak opa
core:
	docker compose up --build api-gateway reporter-identity-service intake-service mailbox-service case-service evidence-service protection-service audit-service
up:
	docker compose up --build
down:
	docker compose -f docker-compose.yml -f docker-compose.blockchain.yml down -v
blockchain:
	docker compose -f docker-compose.blockchain.yml up --build
