# azure-hub-spoke-ccvs

Automated 2-tier Azure hub-and-spoke network built with Terraform. This project combines custom routing, a hardened containerized backend, and GitHub Actions CI/CD with OIDC-based Azure authentication.

## Container Architecture & Hardening

The backend runs in a multi-stage Docker container based on Python 3.13, using Astral uv for dependency management.

- **Multi-Stage Build:** Separates dependency installation from the runtime image to reduce image size and exclude unnecessary build tools.
- **Security:** Runs the application as a dedicated non-root user (appuser, UID 1001) to minimize runtime privileges.
- **Storage:** Configures /app/data with appropriate permissions for SQLite database operations.
- **Image Hygiene:** Uses a slim Python base image, removes unnecessary package files, and applies Hadolint checks to enforce Dockerfile best practices.

## Automated DevSecOps & Delivery Pipeline

The repository utilizes a modular, multi-stage GitHub Actions workflow enforcing static analysis, container vulnerability scanning, runtime integration testing, and automated image publishing to GitHub Container Registry (GHCR):

## Container CI Workflow

```mermaid
flowchart TD
    A(["Triggers"]) --> B["Push to main<br/>Dockerfile, .dockerignore, or app/** changes"]
    A --> C["Manual Dispatch<br/>workflow_dispatch"]

    B --> D["1. Lint and Scan Dockerfile<br/>(lint_and_scan)"]
    C --> D

    subgraph S1["Job 1: Lint and Scan Dockerfile"]
        D --> E["Hadolint<br/>Dockerfile best-practice linting"]
        E --> F["Upload Hadolint SARIF<br/>GitHub Code Scanning"]
        D --> G["Trivy Config Scan<br/>CRITICAL, HIGH, MEDIUM"]
        G --> H["Upload Trivy SARIF<br/>GitHub Code Scanning"]
    end

    F --> I["2. Build, Scan, and Test Image<br/>(build_and_test)"]
    H --> I

    subgraph S2["Job 2: Build, Scan, and Test"]
        I --> J["Docker Build Checks<br/>docker build --check"]
        J --> K["Build Local Test Image<br/>ghcr.io/&lt;repo&gt;:test"]
        K --> L["Trivy Image Vulnerability Scan<br/>CRITICAL, HIGH, MEDIUM<br/>Ignore unfixed vulnerabilities"]
        L --> M["Upload Trivy SARIF<br/>GitHub Code Scanning"]
        M --> N["Run Container and Test Health"]
        N --> O["GET /health<br/>localhost:8080 → container:8000"]
        O --> P["Stop and Remove Test Container"]
    end

    P --> Q["3. Build and Publish Image<br/>(push)"]

    subgraph S3["Job 3: Release and Publish"]
        Q --> R["Authenticate to GHCR<br/>GITHUB_TOKEN"]
        R --> T["Generate Image Metadata and Tags<br/>IMAGE_VERSION + latest"]
        T --> U["Build and Push Production Image<br/>GitHub Container Registry"]
    end

    U --> V(["Workflow Complete"])

    classDef trigger fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef scan fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef publish fill:#dcfce7,stroke:#16a34a,color:#14532d

    class A,B,C trigger
    class E,F,G,H,L,M scan
    class R,T,U,V publish
```

### Pipeline Stages
1. Lint and scan: Hadolint checks Dockerfile quality, and Trivy scans the Dockerfile configuration. Results are uploaded to GitHub Code Scanning in SARIF format.
2. Build, scan, and test: Docker Buildx validates the build, creates a local test image, and runs a Trivy image vulnerability scan. A runtime health check verifies the /health endpoint before the test container is removed.
3. Publish: After the required jobs succeed, GitHub Actions authenticates to GHCR, generates image tags and metadata, and builds and publishes the production image.

## Cloud Architecture

The architecture uses separate hub and spoke virtual networks, with the hub acting as the routing and internet-facing entry point.

<p>
  <img src="assets/architecture.png" alt="Cloud Architecture Runtime Diagram" width="850">
</p>

### Network Security Rules

The network security documentation describes the Network Security Group (NSG) rules governing permitted traffic between the hub, spoke, and external sources.

<p>
  <img src="assets/security-rules.png" alt="Cloud Architecture Runtime Diagram" width="850">
</p>

## Tech Stack
* **Cloud Platform:** Microsoft Azure, Azure Virtual Machines, Virtual Networks, VNet Peering, Network Security Groups, User-Defined Routes, Public IP Addresses
* **Infrastructure as Code:** Terraform
* **Containers:** Docker, multi-stage builds
* **CI/CD:** GitHub Actions, OIDC federation, GitHub Container Registry
* **Container security:** Hadolint, Trivy, GitHub Code Scanning