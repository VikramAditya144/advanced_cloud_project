# Running the project

## How requests are handled

Clients connect to the FastAPI app on port 8000. In Kubernetes, the `todo-api` Service sends traffic to the single pod. The app validates each request and reads or writes a SQLite database at `/data/todos.db`. That directory is backed by a 1 GiB persistent volume claim. Uvicorn logs go to standard output.

This project uses SQLite to avoid running a separate database. It is a good fit for one pod and a small demo. The Deployment uses `Recreate` so two pods do not write to the same database file at once. The trade-off is a short interruption during an update. For multiple replicas, remote backups, or higher availability, move the data to PostgreSQL before scaling the API.

## Run it in Kubernetes

You need Docker and a Kubernetes cluster with a default StorageClass that can provision a 1 GiB `ReadWriteOnce` volume. Build the image and make it available to the cluster. For kind, the extra load command copies the image into the cluster:

```sh
docker build -t todo-api:local .
kind load docker-image todo-api:local  # kind only
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/app.yaml
kubectl -n todo port-forward service/todo-api 8000:80
```

Open `http://localhost:8000/docs` to try the API. The Kubernetes Service is private to the cluster. Add an Ingress and TLS if you later need outside access.

The pod runs as UID 10001, drops Linux capabilities, has a read-only root filesystem, and does not receive a service account token. Startup, liveness, and readiness probes check the app and its database connection. CPU and memory requests and limits are set in `k8s/app.yaml`.

## Build and deploy workflow

The `CI` workflow runs on pull requests and pushes to `main`. It installs the pinned development dependencies, runs Ruff and the API tests, checks dependencies for known vulnerabilities, compiles the app, and builds the image.

The `Release and deploy` workflow publishes an image tagged with the commit SHA to GHCR when a commit reaches `main`. To deploy, run that workflow manually. Its deploy job applies the Kubernetes files, updates the Deployment to the SHA-tagged image, and waits for the rollout.

Before using the deploy job, set up a GitHub `production` environment and add a `KUBECONFIG` Actions secret. The cluster API must be reachable from the GitHub runner, and the cluster must be allowed to pull the GHCR image. Protect the environment with required reviewers if deployments should wait for approval.

If an update fails, check the rollout and pod logs:

```sh
kubectl -n todo rollout status deployment/todo-api
kubectl -n todo get pods
kubectl -n todo logs deployment/todo-api
```

To return to the previous Deployment revision, run:

```sh
kubectl -n todo rollout undo deployment/todo-api
```

Rollback is a manual step; the workflow does not do it automatically.

## Health, metrics, and logs

`/health/live` checks that the process responds. `/health/ready` checks that the database can answer a query. Kubernetes uses these endpoints before restarting a pod or sending it traffic.

`/metrics` exposes request totals and durations. The Service has Prometheus scrape annotations, but this repo does not install Prometheus or provide a dashboard. Uvicorn writes logs to stdout; use `kubectl logs` or a cluster log collector to read them. There is no tracing setup because this version is a single API with one local database.

After port-forwarding, try a quick check:

```sh
curl -sS http://localhost:8000/health/ready
curl -sS -X POST http://localhost:8000/todos \
  -H 'Content-Type: application/json' \
  -d '{"title":"Check the release"}'
curl -sS http://localhost:8000/todos
curl -sS http://localhost:8000/metrics | head
```

## Security and limits

The API has no authentication or user separation, so keep it private. It stores no credentials. CI uses GitHub's short-lived token to publish the image; the cluster credential stays in the protected GitHub environment secret.

CI audits Python dependencies. It does not scan operating-system packages in the image or create a software bill of materials. The SQLite file on one volume is not a backup or a high-availability plan. Back it up separately if the data matters.
