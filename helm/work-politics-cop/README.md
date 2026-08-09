# Helm chart

The chart renders application workloads with non-root users, read-only filesystems, dropped Linux capabilities, separate runtime secrets and default-deny networking. Add explicit network policies, workload identity, external secrets, PodDisruptionBudgets, autoscaling and topology constraints per environment. Do not store secrets in `values.yaml`.
