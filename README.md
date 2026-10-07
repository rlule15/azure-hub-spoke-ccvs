# azure-hub-spoke-ccvs

Automated 2-tier Azure hub-and-spoke network built with Terraform. Features an Apache reverse proxy, custom UDR routing, hardened multi-stage containers, and keyless GitHub Actions CI/CD via OIDC.

## Container Architecture & Hardening

The backend service runs as a hardened, multi-stage Docker container built on Python 3.13, utilizing Astral `uv` for deterministic dependency resolution and non-root runtime isolation:

- **High-Performance Multi-Stage Build:**
  - **Builder Stage:** Uses Astral `uv` for fast, deterministic dependency resolution against `uv.lock`. Utilizes BuildKit cache mounts (`--mount=type=cache`) and ephemeral bind mounts (`--mount=type=bind`) to avoid burning package caches or lock files into intermediate image layers.
  - **Runtime Stage:** Employs a stripped `python:3.13-slim` base containing only the pre-compiled virtual environment (`/app/.venv`) and application source code, omitting `uv` and build-time caches from production.
- **Non-Root Runtime Isolation:**
  - Executes under a dedicated system user (`appuser`, UID `1001`) with no login shell (`/sbin/nologin`) and `--no-log-init` enabled.
  - Explicitly drops `root` (UID `0`) execution privileges to mitigate container escape risks.
- **Storage & Persistence:**
  - Pre-configures `/app/data` with explicit `appuser:appgroup` ownership, enabling SQLite database creation, transactions, and Write-Ahead Logging (`WAL`) on mounted persistent volumes without root permissions.
- **Linting & Package Hygiene:**
  - Minimizes runtime OS footprint by using `--no-install-recommends` and clearing `/var/lib/apt/lists/*`.
  - Fully compliant with **Hadolint** standards, including documented inline exemptions (`DL3008`) for runtime system dependencies (`git`).

## Automated DevSecOps & Delivery Pipeline

The repository utilizes a modular, multi-stage GitHub Actions workflow enforcing static analysis, container vulnerability scanning, runtime integration testing, and automated image publishing to GitHub Container Registry (GHCR):

```text
Manual Dispatch (workflow_dispatch)
   │
   ├── 1. Lint & Scan Dockerfile (Job: lint_and_scan)
   │      ├── Static Linting (Hadolint) ──► SARIF Code Scanning Ingestion
   │      │      └── Enforces Dockerfile best practices and layer hygiene
   │      └── Config Security Scan (Trivy) ──► SARIF Code Scanning Ingestion
   │             └── Scans Dockerfile for misconfigurations and security risks
   │
   ├── 2. Build, Scan & Test (Job: build_and_test)
   │      ├── Syntax & Cache Verification ('docker build --check')
   │      ├── Local Image Build ('ghcr.io/<repo>:test')
   │      ├── Image Vulnerability Scan (Trivy) ──► SARIF Code Scanning Ingestion
   │      │      └── Scans image packages (CRITICAL, HIGH, MEDIUM)
   │      └── Runtime Health Check
   │             └── Runs container, validates 'GET :8080/health', and tears down
   │
   └── 3. Release & Publish (Job: push)
          ├── Authentication to ghcr.io via GITHUB_TOKEN
          ├── Metadata & Tag Generation ('${{ vars.IMAGE_VERSION }}' + 'latest')
          └── Production Build & Push to GitHub Container Registry
```
