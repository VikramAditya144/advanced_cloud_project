# Submission record

Fill in the student and repository fields before submitting. Keep the baseline commit in Git history.

- Student name: **[fill in]**
- Student identifier: **[fill in]**
- Project: **Plain Todo API — FastAPI and Kubernetes delivery**
- Repository: **[add the published repository URL]**
- Baseline commit: `52a6193a042131befdda0d90081168527cd1cce2` (empty repository before project implementation)
- Pull request: **[add the single PR URL containing the baseline-to-final changes]**
- Final commit: **[record `git rev-parse HEAD` after the final project change]**

## Change summary

Added a FastAPI CRUD API backed by SQLite, container packaging, Kubernetes manifests with health probes and persistent storage, Prometheus metrics, automated API tests, dependency security auditing, CI checks and image builds, GHCR release publishing, and a manually dispatched Kubernetes deployment with rollout status. Design decisions, setup steps, rollback, security boundaries, and limitations are in [OPERATIONS.md](OPERATIONS.md).

## Run and access

See [README.md](README.md) for local setup and API examples. See [OPERATIONS.md](OPERATIONS.md) for container and Kubernetes deployment steps, pipeline configuration, and operational checks.

## Existing DevOps at baseline

The baseline was an empty repository with no application, deployment configuration, or delivery automation.
