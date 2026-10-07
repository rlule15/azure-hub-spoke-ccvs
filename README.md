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

The repository utilizes a security-first GitHub Actions workflow implementing static analysis, vulnerability scanning, and automated image publishing to GitHub Container Registry (GHCR):

```text
git push / manual dispatch
   │
   ├── 1. Static Linting (Hadolint)
   │      └── Enforces Dockerfile best practices and layer hygiene
   │
   ├── 2. Configuration Security Scan (Trivy)
   │      └── Scans build manifests for misconfigurations and privilege risks
   │
   ├── 3. SARIF Ingestion (GitHub Code Scanning)
   │      └── Uploads Hadolint & Trivy results directly to the repository Security tab
   │
   └── 4. Build, Validate & Push (Docker Buildx)
          ├── Executes 'docker build --check' syntax & cache verification
          ├── Generates dynamic image tags (version tag + latest)
          └── Pushes authenticated multi-platform image to GHCR via GITHUB_TOKEN
```
