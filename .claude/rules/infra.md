---
paths:
  - "infra/**/*"
  - ".github/workflows/**/*"
---

# Infrastructure and CI (LLD sections 16 to 18)

- Every Terraform cloud module (`modules/*/{aws,azure,gcp}`) exposes the same inputs and outputs. Change all three or none.
- Cloud specifics go only in `values-{aws,azure,gcp}.yaml` and the per-cloud module folders.
- Images run as non-root on a read-only root FS, with pinned tags. `latest` in the LLD Compose excerpt is illustration only.
- No secrets in files. Use the secret manager through workload identity or the CSI driver. CI uses OIDC federation, never static keys.
- NetworkPolicies are default-deny. MCP servers are reachable only from `agent-runtime` pods.
- The same image digest is promoted dev, then staging, then prod on every cloud.
- Don't read or print `*.tfvars`, `*.tfstate` or kubeconfig files.
