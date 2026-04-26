# Cloud Resume Challenge

My take on the Cloud Resume Challenge. The [Cloud Resume](https://cloudresumechallenge.dev/docs/the-challenge/) challenge is a resume project designed to build and demonstrate skills relevant to a career in cloud engineering.

I adjusted the project around a few practical goals:

1. Learn more Python.
2. Demonstrate Front to Back monitoring using Datadog.
3. Keep costs as low as possible.

The live site is available at [resume.sbrtech.xyz](https://resume.sbrtech.xyz). For project context, start with the high-level [project overview](https://resume.sbrtech.xyz/project_overview), then read the detailed [project write-up](https://resume.sbrtech.xyz/page/project). The subdirectory READMEs below describe the major implementation areas for engineers reviewing the repo.

## Live Website

- [Resume Site](https://resume.sbrtech.xyz)
- [Project Overview](https://resume.sbrtech.xyz/project_overview)
- [Detailed Project Write-Up](https://resume.sbrtech.xyz/page/project)

## Project Subdirectories

- [Python Application](/cloud_resume/) - Flask/Gunicorn resume site, visitor counter, local development, and containerized runtime notes.
- [Terraform](/terraform/) - GCP and Cloudflare infrastructure provisioning managed through HCP Terraform.
- [Ansible](/ansible/) - Host configuration, Docker deployment, Caddy reverse proxy setup, and operational automation.

## Technologies Used

- Google GCP
- Google Firestore
- Google IAM
- Python
- Ansible
- Terraform + HCP Terraform
- Docker
- Reverse Proxy (Caddy)
- Datadog
- Cloudflare
- Github Actions (CI/CD)

## Architecture

![Architecture Diagram](/.assets/website_architecture.png)
