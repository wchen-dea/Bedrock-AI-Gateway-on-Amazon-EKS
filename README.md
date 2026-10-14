# Bedrock AI Gateway on Amazon EKS

A FastAPI gateway that routes chat requests to either a deterministic mock
provider or Amazon Bedrock. The repository includes a local Minikube workflow
running on Docker Desktop, a Helm chart, Argo CD manifests, and Terraform for the EKS, ECR,
and IAM foundation.

> **Status:** This is a production-oriented scaffold, not a complete
> production platform. Review the [production checklist](docs/production-checklist.md)
> and the deployment prerequisites before exposing the API to users.

## Architecture

```text
Local development:
  Docker Desktop -> Minikube (Docker driver) -> Helm -> FastAPI gateway -> mock provider

Production:
  Client -> ALB Ingress -> FastAPI gateway -> Amazon Bedrock Converse API
                          -> EKS service account -> IAM role

Delivery:
  Git -> CI validation/build -> immutable ECR image
      -> reviewed Helm values change -> Argo CD -> EKS
```

## Repository layout

| Path | Purpose |
| --- | --- |
| `app/` | FastAPI application, configuration, providers, and tests |
| `deploy/helm/ai-system/` | Reusable Helm chart and local/production values |
| `deploy/argocd/` | Argo CD project and production application |
| `infra/terraform/envs/prod/` | EKS, ECR, and Bedrock IAM foundation |
| `docs/production-checklist.md` | Operational and security follow-up items |
| `.github/workflows/ci.yaml` | CI validation workflow |

## Prerequisites

Install the tools required for the workflow you intend to use:

- Python 3.12
- uv
- Docker Desktop (Minikube Docker driver and image builds)
- `kubectl`
- Helm
- minikube (local Kubernetes)
- AWS CLI (for Bedrock and EKS)
- Terraform 1.7 or later (for infrastructure)
- Argo CD CLI (optional, for Argo CD inspection)

## Local development with Minikube on Docker Desktop

Start Docker Desktop before running the commands below. Local development
deploys to a Minikube cluster using Docker Desktop's Docker engine, the Helm
chart, and `values-local.yaml` (mock provider, no AWS credentials needed).
The Makefile explicitly selects Minikube's `docker` driver.

```bash
make minikube-up        # start minikube
make minikube-deploy    # build image in minikube and helm install
make minikube-forward   # port-forward svc/ai-system to localhost:8080
```

In another terminal:

```bash
curl -s http://localhost:8080/healthz

curl -s http://localhost:8080/v1/chat \
  -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explain Kafka offsets."}]}'
```

Expected mock response:

```json
{"output":"Mock response: Explain Kafka offsets."}
```

Re-run `make minikube-deploy` after code changes. Remove everything with
`make minikube-down`.

To use Bedrock locally, override the chart values. The chart does not inject
AWS credentials, so the pod needs credentials supplied separately (for
example a Kubernetes secret you add); the mock provider is recommended
locally.

```bash
helm upgrade --install ai-system deploy/helm/ai-system -n ai-system \
  -f deploy/helm/ai-system/values-local.yaml \
  --set config.aiProvider=bedrock \
  --set config.awsRegion=us-west-2 \
  --set config.bedrockModelId='<approved-model-id>'
```

## Tests and validation

Create the virtual environment and install the locked runtime and development
dependencies:

```bash
uv sync
```

Run the same checks used by CI:

```bash
uv run ruff check app
uv run pytest -q
helm lint deploy/helm/ai-system \
  -f deploy/helm/ai-system/values-local.yaml
docker build -t ai-system:dev .
```

The Makefile includes shortcuts for the application tests and Helm lint:

```bash
make sync
make test
make lint
make helm-lint
```

### GitHub Actions

The checked-in workflow at
`.github/workflows/ci.yaml` runs the validation and Docker build job only for:

- Pushes to the `dev` branch
- Pull requests targeting the `dev` branch

It does not run for pushes to other branches or pull requests targeting other
branches. The workflow installs the locked uv dependencies, runs Ruff and
pytest, lints the local Helm values, and builds the Docker image. It does not
push images to ECR or deploy to EKS.

## Terraform infrastructure

The Terraform configuration expects an existing VPC and private subnets. It
does not create a VPC. It provisions:

- An EKS cluster with private API access
- ECR with immutable image tags and scan-on-push enabled
- EKS managed node groups
- An IRSA-compatible IAM role scoped to the configured Bedrock model ARNs

Configure the backend and variables from the provided examples:

```bash
cd infra/terraform/envs/prod
cp backend.hcl.example backend.hcl
cp terraform.tfvars.example terraform.tfvars
```

Set the real S3 backend values in `backend.hcl` and the VPC, subnet, cluster,
region, and Bedrock model ARN values in `terraform.tfvars`. Then run:

```bash
terraform init -backend-config=backend.hcl
terraform validate
terraform plan
terraform apply
```

The outputs include the EKS cluster name, ECR repository URL, and Bedrock IAM
role ARN.

After the cluster is available:

```bash
aws eks update-kubeconfig \
  --name ai-prod \
  --region us-west-2
kubectl get nodes
```

Cluster add-ons such as Argo CD, AWS Load Balancer Controller, External
Secrets Operator, metrics-server, an observability stack, and a policy
engine are platform prerequisites. They are not installed by this Terraform
configuration.

## Build and promote a production image

Use an immutable Git SHA tag and push it to the ECR repository created by
Terraform:

```bash
export AWS_REGION=us-west-2
export ECR_REPOSITORY='<account-id>.dkr.ecr.us-west-2.amazonaws.com/ai-system'
export IMAGE_TAG='<git-sha>'

aws ecr get-login-password --region "$AWS_REGION" |
  docker login --username AWS --password-stdin "$ECR_REPOSITORY"
docker build -t "ai-system:${IMAGE_TAG}" .
docker tag "ai-system:${IMAGE_TAG}" "${ECR_REPOSITORY}:${IMAGE_TAG}"
docker push "${ECR_REPOSITORY}:${IMAGE_TAG}"
```

Update the placeholders in
[`deploy/helm/ai-system/values-prod.yaml`](deploy/helm/ai-system/values-prod.yaml):

- `image.repository`
- `image.tag`
- `serviceAccount.roleArn`
- `config.bedrockModelId`
- `ingress.host`

Commit that reviewed values change. The checked-in CI workflow validates the
application, chart, and image for the `dev` branch workflow scope; it does
**not** authenticate to ECR, push an image, or open a GitOps pull request
automatically. Production GitOps changes must be promoted through the `prd`
branch.

## Deploy with Helm or Argo CD

For a direct Helm deployment, render and install the production values only
after replacing all placeholders:

```bash
helm lint deploy/helm/ai-system \
  -f deploy/helm/ai-system/values-prod.yaml
helm upgrade --install ai-system deploy/helm/ai-system \
  --namespace ai-system \
  --create-namespace \
  -f deploy/helm/ai-system/values-prod.yaml
```

For GitOps, replace `REPLACE_WITH_GIT_REPO` in both Argo CD manifests with the
repository URL, then apply the project and application:

```bash
kubectl apply -f deploy/argocd/project.yaml
kubectl apply -f deploy/argocd/application-prod.yaml
kubectl get applications -n argocd
argocd app get ai-system-prod
```

The Argo CD application tracks `prd`, renders
`deploy/helm/ai-system/values-prod.yaml`, and enables automated pruning and
self-healing. Argo CD production reconciliation is intentionally limited to
the `prd` branch. Confirm that branch protections and approval controls are in
place before relying on automated sync.

Verify the resulting resources:

```bash
kubectl get pods,svc,ingress -n ai-system
curl -s https://<configured-host>/healthz
curl -s https://<configured-host>/readyz
```

The production values enable an internal ALB. DNS, TLS, security groups, and
the AWS Load Balancer Controller must be configured by the platform.

## Rollback

The preferred GitOps rollback is to revert the values change that promoted the
image on the `prd` branch and push the revert:

```bash
git revert <promotion-commit>
git push origin prd
```

Argo CD will reconcile the reverted desired state. For a direct Helm release,
inspect available revisions and roll back the release:

```bash
helm history ai-system -n ai-system
helm rollback ai-system <revision> -n ai-system
```

## API

### `GET /healthz`

Returns `{"status":"ok"}` when the process is running.

### `GET /readyz`

Returns `{"status":"ready"}`. Readiness currently does not verify Bedrock
credentials or model availability.

### `GET /metrics`

Returns Prometheus metrics, including request counts and request latency.

### `POST /v1/chat`

Request body:

```json
{
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

`messages` accepts 1–50 messages. Each message role must be `user` or
`assistant`; content must be 1–20,000 characters. The endpoint returns:

```json
{"output":"..."}
```

## Security and production follow-up

The scaffold includes non-root containers, a read-only root filesystem,
dropped Linux capabilities, resource limits, probes, a PDB, HPA, NetworkPolicy,
immutable ECR tags, and model-scoped Bedrock permissions.

Before production use, complete the
[production readiness checklist](docs/production-checklist.md), especially:

- Authentication and authorization for the chat endpoint
- Prompt-injection and input/output safety controls
- Timeouts, retries, circuit breaking, and quota handling
- PII handling and retention policy
- TLS, DNS, ingress access controls, and secret delivery
- Cost, token, latency, throttling, and quality telemetry
- Image, dependency, IaC, SBOM, signing, and admission scans
- Backup, rollback, SLOs, and incident runbooks

## Promotion model

Promote the same immutable image digest through environments. CI validation
runs on `dev`, while production GitOps reconciliation runs only from `prd`.
Change environment configuration in Git, but do not rebuild the image between
development, staging, and production:

```text
build once -> dev -> prd -> production GitOps
```
