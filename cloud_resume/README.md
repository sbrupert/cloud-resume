# Cloud Resume Application

This directory contains the Python web application for the resume site. It serves the public resume, project pages, static assets, and a visitor counter backed by Google Firestore.

The application can run locally with the Firestore emulator for development and testing, or against a real Firestore database in production. Docker Compose provides the quickest local path because it starts the app and emulator together.

## Features

- ***Visitor Tracking:*** Counts unique visitors using Google Firestore.
- ***Caching:*** Uses local IP caching to reduce database reads and preserve Firestore free tier limits.
- ***Flexible Logging:*** Emits JSON logs compatible with log analysis tools such as Datadog.

## How This Fits Into The System

Terraform provisions the GCP and Cloudflare infrastructure, Ansible configures the host and deploys the container, and this application provides the runtime service behind Caddy. In production, Caddy reverse proxies public traffic to the Gunicorn process running this Flask app.

## Responsive Layout Testing (Future Work)

Recommended follow-up options for automated viewport/layout coverage:

1. Add Playwright end-to-end tests with a breakpoint matrix (`375x667`, `393x852`, `768x1024`, `1280x800`).
2. Capture baseline screenshots of key pages at each breakpoint and fail CI on visual diffs.
3. Include smoke assertions for navigation behavior (mobile menu open/close, link visibility, and no overlap with page content).

## Configuration

### Environment Variables

- `LOGLEVEL`: Sets the logging level. Default is `INFO`. Can be set to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
- `FIRESTORE_EMULATOR_HOST`: If set, the application connects to the Firestore emulator instead of the production Firestore.
- `SITE_VERSION`: Optional version tag displayed in shared site chrome. Default is `Development`.
- `GUNICORN_THREADS`: Optional Gunicorn runtime override. Default is `1`.
- `GUNICORN_TIMEOUT`: Optional Gunicorn request timeout override (seconds). Default is `60`.

Gunicorn uses defaults from `cloud_resume/gunicorn.conf.py`. Only `GUNICORN_THREADS` and `GUNICORN_TIMEOUT` are intentionally exposed as runtime tunables. Other worker settings are fixed.

## Getting Started Guide

### Deployment Options

1. [Docker Compose](#1-docker-compose) (recommended for local development)
2. [Manual Deployment](#2-manual-deployment) (no Docker required)

#### 1. Docker Compose

Docker Compose is the quickest way to run the project locally. The compose file starts a Google Cloud Firestore emulator alongside the cloud-resume app. The Firestore emulator container's source code/Dockerfile can be found [here](https://github.com/ridedott/firestore-emulator-docker).

The application image is built from Ubuntu 24.04 LTS and installs Python dependencies into an in-container virtual environment at `/opt/venv`. This avoids installing application packages into the system Python environment.
Frontend CSS and fonts are also built during the Docker image build (via Tailwind) so runtime containers do not need Node tooling.

##### Requirements

1. Docker and Docker Compose

In order to launch the app without using a real Firestore database, you will need to install [Docker](https://docs.docker.com/get-started/) and [Docker Compose](https://docs.docker.com/compose/).

##### Steps

1. Clone the repository.

   ```bash
   git clone git@github.com:sbrupert/cloud-resume.git
   ```

2. Start the app with Docker Compose from the root project directory.

   ```bash
   docker-compose up
   ```

   The compose service still runs `gunicorn cloud_resume.app:app`, and that command resolves from `/opt/venv/bin` inside the container.
   Gunicorn defaults come from `cloud_resume/gunicorn.conf.py`; only `GUNICORN_THREADS` and `GUNICORN_TIMEOUT` are runtime overrides.

3. Open a browser to http://localhost:8080.
4. To stop the app:
   1. Press `Ctrl+C` in your terminal window where you ran `docker-compose up`.
   2. Run `docker-compose down` from the root project directory.

#### 2. Manual Deployment

##### Requirements

1. Python (<=3.12)
2. Node.js (for local Tailwind asset builds)
3. Google Cloud CLI
   - In order to launch the app without using a real Firestore database, you will need to install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install). Follow the official installation instructions and return here when done.

##### Steps

1. Clone the repository and enter the project directory.

   ```bash
   git clone https://github.com/sbrupert/cloud-resume.git
   cd cloud-resume
   ```

2. Change to the Python project directory.

   ```bash
   cd cloud_resume/
   ```

3. (Optional) Create a python virtual environment.

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies.

   ```bash
   pip install -r requirements.txt
   ```

5. Install and build frontend assets (Tailwind + self-hosted fonts).

   ```bash
   npm ci
   npm run build:assets
   ```

6. Start the firestore emulator.

   ```bash
   export FIRESTORE_EMULATOR_HOST='localhost:8181'
   gcloud emulators firestore start --host-port=$FIRESTORE_EMULATOR_HOST
   ```

7. Launch the app either with Gunicorn or Flask:
   1. Gunicorn: `gunicorn cloud_resume.app:app`
   2. Flask: `python -m cloud_resume`
8. Open a browser to http://localhost:8080.
