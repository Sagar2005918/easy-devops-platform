# Operations runbook

## Check a rollout

```bash
kubectl argo rollouts get rollout task-api -n task-api --watch
kubectl get pods,svc,ingress -n task-api
kubectl logs -n task-api -l app=task-api --tail=100
```

## Roll back

If analysis fails, Argo aborts the canary and preserves traffic on the stable ReplicaSet. To restore the previous revision manually:

```bash
kubectl argo rollouts undo task-api -n task-api
kubectl argo rollouts status task-api -n task-api --timeout=5m
```

For an urgent incident, pause or abort an active rollout with the Argo Rollouts CLI and inspect logs/Prometheus before resuming.

## Recover infrastructure

1. Restore the encrypted Terraform state from its remote backend version history.
2. Re-run `terraform plan` and apply only after reviewing the plan.
3. Reinstall cluster add-ons from their pinned Helm configuration.
4. Apply the Kubernetes manifests and redeploy the last known good immutable image tag.

This starter does not create the remote Terraform state bucket, backups, log retention policy, or alert notification channel. Add these for a real service.
