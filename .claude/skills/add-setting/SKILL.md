---
name: add-setting
description: Add a new configuration value to ACSRP end to end, covering the Settings field, .env example, Helm values per cloud, and a secret if sensitive. Use whenever code needs a new env var or config knob.
argument-hint: "[setting_name] [type] [default] [sensitive?]"
---

Add the setting described here: $ARGUMENTS

Follow LLD section 15 (12-factor, `pydantic-settings`, env prefix `ACSRP_`).

1. Add a typed field to `Settings`, using `AnyUrl`, `PostgresDsn`, `Literal[...]` and similar types instead of bare `str` where possible. Give a safe default only if one exists for every environment.
2. Add `ACSRP_<NAME>=` with a placeholder value to `infra/docker/.env.example`. Never use a real value.
3. Add the value to `infra/helm/acsrp/values.yaml`, plus any per-cloud override in `values-aws.yaml`, `values-azure.yaml` and `values-gcp.yaml`. All three clouds must stay in step.
4. If the value is sensitive:
   - don't put it in values files;
   - add it to the Terraform `secrets` list (LLD section 17.1);
   - mount it through the `SecretProvider` adapter / CSI driver / External Secrets.
5. If behaviour differs per cloud, read it through the cloud adapter selected by `settings.cloud`. Don't branch on the cloud in business code.
6. Add a unit test that `Settings` parses the new variable, and one that a missing required value fails at startup.
7. Never read `os.environ` directly. Code gets the value from the injected `Settings`.
