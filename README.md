# Easy DevOps Platform

A small **Task API** with a complete, understandable software delivery example. A code change runs tests and security checks, builds and scans a container, publishes it to GitHub Container Registry, then deploys it to Kubernetes through a progressive canary rollout.

> This is a learning project and deployment starter. The sample API keeps tasks in memory, so task data resets when a pod restarts. Before using it for real user data, add a managed database, backups, authentication, TLS/DNS values, and an approved production access policy.

## What is included

| Area | Included |
|---|---|
| Version control | Git repository and pull request workflow |
| CI | Pytest, Bandit, pip-audit, Gitleaks |
| Containerization | Small, non-root, multi-stage Docker image with health check |
| Image security | Trivy scan of published image; fails on high/critical findings |
| Kubernetes | Restricted namespace, probes, resource limits, NetworkPolicy, PDB |
| Progressive delivery | Argo Rollouts canary: 10%, 30%, 60%, then 100%; Prometheus error-rate analysis; rollback window |
| Infrastructure | Terraform example for AWS VPC + EKS managed nodes |
| Observability | Prometheus metrics, ServiceMonitor, alert rules, JSON logs to stdout |
| Recoverability | 3 replicas, disruption budget, rollout history, `kubectl argo rollouts undo` |

## Run locally

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\\Scripts\\activate
pip install -r requirements-dev.txt
pytest -q
python app.py
```

Try it in a second terminal:

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/tasks -H 'Content-Type: application/json' -d '{"title":"Learn CI/CD"}'
curl http://localhost:8080/tasks
curl http://localhost:8080/metrics
```

## Run with Docker

```bash
docker build -t easy-devops-task-api:local .
docker run --rm -p 8080:8080 easy-devops-task-api:local
```

## Delivery flow

1. Open a pull request: tests, static analysis, dependency audit, and secret scan run.
2. Merge to `main`: the same checks run, then Actions builds an immutable `sha-<commit>` image and pushes it to `ghcr.io/<owner>/<repository>`.
3. Trivy scans the published image. Deployment waits until the scan succeeds.
4. Actions updates the `task-api` Argo Rollout. Argo gradually shifts traffic and asks Prometheus to check the 5xx rate at the canary checkpoints.
5. A failed check aborts promotion and keeps the stable revision serving traffic. See [Operations](docs/operations.md) for rollback steps.

### One-time GitHub Actions configuration

Create a GitHub Environment named `production` and add these repository/environment secrets:

- `KUBE_CONFIG`: base64-encoded kubeconfig for the target cluster. Give this identity only the namespace-scoped permissions needed by the deployment workflow.
- `GHCR_USERNAME`: GitHub username allowed to read the package.
- `GHCR_PULL_TOKEN`: fine-grained token with read access to the package. Keep it private and rotate it.

The workflow deliberately does not create cloud resources or expose credentials. Apply Terraform and bootstrap cluster components as described below before enabling the `production` deployment environment.

## Infrastructure and cluster bootstrap

Terraform provisions an AWS VPC and EKS cluster. Review cost and security settings first. Configure a remote, encrypted Terraform state backend with locking before team use. Set `allowed_admin_cidrs` to your trusted public IP `/32` before applying; the default empty list intentionally leaves public API access unavailable.

```bash
cd infra/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
aws eks update-kubeconfig --region ap-south-1 --name easy-devops-task-api
```

Install the ingress controller, Argo Rollouts, and Prometheus stack (pin chart versions in a real environment):

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add argo https://argoproj.github.io/argo-helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace
helm upgrade --install argo-rollouts argo/argo-rollouts -n argo-rollouts --create-namespace
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
kubectl apply -f ../../k8s/namespace.yaml
kubectl apply -f ../../k8s/services.yaml
kubectl apply -f ../../k8s/analysis-template.yaml
kubectl apply -f ../../k8s/rollout.yaml
kubectl apply -f ../../k8s/monitoring/
```

Before applying `k8s/rollout.yaml`, replace `ghcr.io/OWNER/REPOSITORY:latest` with your image path and replace `task-api.example.com` plus the TLS secret reference in `k8s/services.yaml` with your actual DNS/TLS setup. Create the GHCR pull secret or allow anonymous package pulls. For the very first release, set the Rollout image to a tag that already exists in GHCR.

## Monitoring and logs

- Prometheus scrapes `/metrics` every 15 seconds through the ServiceMonitor.
- Alert rules flag a down target and sustained 5xx rate above 5%.
- The app writes one-line JSON events to stdout; container runtimes and the Kubernetes logging agent collect them. A simple Loki + Grafana stack can be added with Grafana's Helm charts; keep logs free of credentials and personal data.
- Canary analysis uses the same Prometheus metrics endpoint. Review alert routing and add request latency histograms before a real production workload.

## Security and recovery notes

- App runs as a non-root user; Kubernetes additionally enforces a restricted pod security profile, read-only root filesystem, dropped Linux capabilities, resource limits, and restricted network ingress.
- GitHub Actions uses read-only repository permissions for verification and the built-in package token only for image publishing.
- Pin third-party Actions to reviewed commit SHAs for a hardened production supply chain; the example uses version tags for readability.
- Recover from a bad deployment with `kubectl argo rollouts undo task-api -n task-api`, then inspect `kubectl argo rollouts get rollout task-api -n task-api`.
- Terraform state, application data, and cluster manifests should have independent backups in a real system. This demo's in-memory task state is intentionally disposable.

See [Architecture](docs/architecture.md) and [Operations](docs/operations.md).
