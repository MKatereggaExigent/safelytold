# Terraform deployment interfaces

Cloud-neutral module interfaces make trust boundaries explicit without pretending one template is production-ready for every region or provider. Implement or replace each module for AWS, Azure, GCP or a sovereign/private cloud.

Modules: network, Kubernetes, PostgreSQL fleets, identity vault, audit store, object storage, messaging, Temporal, Prefect, KMS/HSM, observability and permissioned ledger. State must be remote, encrypted and separated by environment. Production changes require plan review and policy-as-code.
