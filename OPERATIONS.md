# Operations and project decisions

## Architecture and request path

A client sends HTTP requests to the FastAPI process on port 8000. The Kubernetes ClusterIP Service forwards traffic to the single Deployment pod. FastAPI validates request bodies, executes parameterized SQL statements against SQLite, and returns JSON. The database file is on a 1 GiB PVC mounted at `/data`; API logs go to standard output and Prometheus metrics are exposed at `/metrics`.

SQLite keeps a learning project small and avoids operating a separate database. One replica and a `Recreate` deployment strategy suit a single-writer SQLite file. This is not a horizontally scalable or highly available database design. For concurrent replicas, stronger availability, or remote backups, move persistence to PostgreSQL and use multiple API replicas.

## Configuration and Kubernetes

Runtime configuration uses `TODO_DB_PATH`; the same variable works locally and in the container. Kubernetes resources are in `k8s/`. The Deployment uses startup, liveness, and readiness probes, CPU/memory requests and limits, a non-root UID, a read-only root filesystem, a dropped Linux capability set, and no service account token. The Service is private to the cluster. Add an Ingress and TLS termination only when an external endpoint is required.

Apply locally after building the image and making it available to your cluster:

```sh
docker build -t todo-api:local .
# For kind: kind load docker-image todo-api:local
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/app.yaml
kubectl -n todo port-forward service/todo-api 8000:80
```

Then use `http://localhost:8000/docs`. The cluster needs a default StorageClass that supports a 1 GiB `ReadWriteOnce` PVC.

## Delivery and release control

The pull request workflow installs pinned development dependencies, checks style, runs API tests, audits pinned dependencies, compiles the application, and builds a container image. Merges to `main` publish a commit-addressed image to GitHub Container Registry (GHCR). The `Release and deploy` workflow also supports manual dispatch: its deploy job uses the image for the triggering commit and waits for the Kubernetes rollout. Configure a protected GitHub `production` environment and a `KUBECONFIG` Actions secret containing the deployment kubeconfig. The cluster must allow the workflow runner to reach its API server, and the package must be pullable by the cluster.

Kubernetes tracks the previous Deployment revision. If rollout fails, inspect `kubectl -n todo rollout status deployment/todo-api` and pod events/logs, then use `kubectl -n todo rollout undo deployment/todo-api`. The immutable commit tag identifies what was released. A failed deployment does not automatically roll back; the operator performs the rollback.

## Signals and verification

`/health/live` reports process liveness. `/health/ready` checks that SQLite can answer a query, so Kubernetes only sends Service traffic to a usable pod. `/metrics` exposes request totals and request duration in Prometheus format; the Service has standard scrape annotations. Uvicorn writes request and error logs to stdout for `kubectl logs` or a cluster log collector. A dashboard or alerting stack is intentionally not bundled: install Prometheus-compatible collection to retain and visualize metrics.

A basic smoke check after port-forwarding:

```sh
curl -sS http://localhost:8000/health/ready
curl -sS -X POST http://localhost:8000/todos -H 'Content-Type: application/json' -d '{"title":"Check the release"}'
curl -sS http://localhost:8000/todos
curl -sS http://localhost:8000/metrics | head
```

## Security and known limitations

The API has no authentication or user separation. Keep the Service private and do not expose it to an untrusted network without authentication and TLS. No credentials are stored in the application. CI uses the short-lived GitHub token to publish; deployment cluster access is supplied through the protected environment secret and never committed. CI audits the pinned Python runtime and development dependencies for known vulnerabilities. It does not scan operating-system packages in the container image or generate a software bill of materials. SQLite on a single PVC is suitable for demonstration, not production backups or multi-replica failover.
