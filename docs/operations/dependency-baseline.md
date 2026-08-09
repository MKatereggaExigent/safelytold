# Dependency baseline

The foundation uses explicit major/minor baselines and automated dependency review. As of 5 August 2026, the local templates target FastAPI 0.139.2+, Next.js 16.2.11 Active LTS, React 19.2.7, RabbitMQ 4.3.4, Temporal Server 1.31.2, Prefect 3.7, and Keycloak 26.7.0.

Do not treat these pins as permanent. Renovate/Dependabot, release notes, CVE review, compatibility testing and signed image provenance are required. Temporal upgrades must include schema migration and should proceed sequentially across minor versions. Production image digests should replace mutable tags after qualification.
