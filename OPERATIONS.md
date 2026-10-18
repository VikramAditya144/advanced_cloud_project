# Running the project

## Request path

The client calls the FastAPI app on port 8000. In Kubernetes, the `todo-api` Service forwards the request to the pod. The app reads or writes `/data/todos.db`, which is on a 1 GiB persistent volume. Uvicorn writes logs to standard output.

## Why one pod and SQLite

I used SQLite to keep the project easy to run. It works for a small app with one instance, but it is not a good choice for multiple API pods writing at the same time. The Deployment has one replica and uses the `Recreate` strategy. That avoids two pods using the same database file, but an update causes a short outage. If the app needed multiple replicas or reliable remote backups, I would move the data to PostgreSQL first.

## Run it in Kubernetes

You need Docker and a Kubernetes cluster with a default StorageClass that can create a 1 GiB `ReadWriteOnce` volume. Build the image and make it available in the cluster. With kind, load the image before applying the manifests:

```sh
docker build -t todo-api:local .
kind load docker-image todo-api:local
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/app.yaml
kubectl -n todo port-forward service/todo-api 8000:80
```

The `kind load` command is only for kind. Once port-forwarding is running, open [http://localhost:8000/docs](http://localhost:8000/docs).

The pod runs as UID 10001. It has a read-only root filesystem, no extra Linux capabilities, and no service account token. Startup, liveness, and readiness probes are configured in `k8s/app.yaml`, along with CPU and memory requests and limits. The Service is private to the cluster. Add an Ingress and TLS if outside access is needed.

## CI and deployment

The `CI` workflow runs for pull requests and pushes to `main`. It runs Ruff, the API tests, a Python dependency audit, a compile check, and a Docker build.

The `Release and deploy` workflow publishes an image to GHCR when a commit is pushed to `main`. The image tag includes the commit SHA. To deploy it, run the workflow manually. It applies the Kubernetes manifests, updates the Deployment to that image, and waits for the rollout.

For the deploy job, create a GitHub environment called `production` and add a `KUBECONFIG` Actions secret. The runner must be able to reach the cluster, and the cluster must be able to pull the image from GHCR. You can require approval for the environment in GitHub's settings.

If a deployment does not come up, check its status and logs:

```sh
kubectl -n todo rollout status deployment/todo-api
kubectl -n todo get pods
kubectl -n todo logs deployment/todo-api
```

To return to the previous Deployment revision:

```sh
kubectl -n todo rollout undo deployment/todo-api
```

Rollback is manual; the workflow does not do it automatically.

## Health and monitoring

`/health/live` checks that the process responds. `/health/ready` checks the database connection. Kubernetes uses these endpoints to decide whether to restart the pod or send it traffic.

`/metrics` reports request counts and durations. The Service has Prometheus scrape annotations, but this project does not install Prometheus or include a dashboard. Use `kubectl logs` or a cluster log collector to read the app logs. There is no tracing setup; this version has one API and one local database.

After port-forwarding, these commands provide a basic check:

```sh
curl -sS http://localhost:8000/health/ready
curl -sS -X POST http://localhost:8000/todos \
  -H 'Content-Type: application/json' \
  -d '{"title":"Check the release"}'
curl -sS http://localhost:8000/todos
curl -sS http://localhost:8000/metrics | head
```

## Limits and security

The API has no authentication or separate users. Keep it private. No credentials are stored in the app. GitHub uses its short-lived token to publish the image; the cluster credential is kept in the `production` environment secret.

CI checks Python dependencies for known vulnerabilities. It does not scan operating-system packages in the image or create a software bill of materials. A single SQLite volume is not a backup or a high-availability setup. Back it up separately if you need to keep the data.
