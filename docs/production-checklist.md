# Production readiness checklist

## Platform
- Private EKS API endpoint with controlled operator access
- Multi-AZ private subnets and approved egress path/VPC endpoints
- Managed add-ons and version policy documented
- Argo CD HA, SSO/RBAC, repository credentials, backup, and audit logging
- AWS Load Balancer Controller, External Secrets, metrics-server, OTel, policy engine

## AI runtime
- Ollama is intended for local development; production deployments use Bedrock
- Bedrock model access approved per region/account
- Explicit model allowlist in IAM
- Prompt-injection controls, input/output validation, request limits
- PII classification and redaction policy
- Model timeout, retry, circuit breaker, and fallback behavior
- Token, latency, error, throttling, and cost telemetry
- Evaluation suite and release gates for quality/safety regressions

## Delivery
- Immutable digest promotion
- Signed images and admission verification
- SBOM, dependency/container/IaC scans
- Pull-request approval for production GitOps changes
- Canary/blue-green strategy and tested rollback

## Reliability
- SLOs for availability, latency, and model error rate
- HPA based on CPU plus request/concurrency metrics where appropriate
- PodDisruptionBudget and topology spread constraints
- Bedrock quota and throttling alarms
- Runbooks for model outage, bad response, cost spike, and EKS failure
