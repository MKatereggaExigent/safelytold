terraform { required_version = ">= 1.8.0" }

# Implement using the selected cloud provider. Do not collapse this module's
# trust boundary into a shared administrator, key or public network.
locals { component = "audit_store" }
