# Cloud Resume Application

This python application showcases my resume, featuring a visitor counter powered by Google Firestore. The app can be deployed quickly using Docker Compose with a firestore emulator for testing. Or, with a real Firestore database for production.

## Features

- ***Visitor Tracking:*** Counts unique visitors in real time.
- ***Caching:*** Local IP caching to minimize database reads. (For helping stay within Firestore free tier.)
- ***Flexible Logging:*** Logs are formatted in JSON to provide compatibility with log analysis tools like Datadog.

## Configuration

### Environment Variables

- `LOGLEVEL`: Sets the logging level. Default is `INFO`. Can be set to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
- `FIRESTORE_EMULATOR_HOST`: If set, the application connects to the Firestore emulator instead of the production Firestore.

## Getting Started Guide

### Deployment Options

1. [Manual Deployment](#1-manual-deployment) (The Hard Way, No Docker Required)
2. [Docker Compose](#2-docker-compose) (**Recommended**, The Easy Way)

#### 1. Manual Deployment

##### Requirements

1. Python (<=3.12)
2. Google Cloud CLI
   - In order to launch the app without using a real Firestore database, you will need to install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install). Follow the official installation instructions and return here when done.

#### Steps

1. Clone the repository and enter the project directory.

   ```bash
   git clone https://github.com/sbrupert/cloud-resume.git
   cd cloud-resume
   ```

2. Change to the python project directory

   ```bash
   cd cloud_resume/
   ```

3. (Optional) Create a python virtual environment.

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

5. Start the firestore emulator.

   ```bash
   export FIRESTORE_EMULATOR_HOST='localhost:8181'
   gcloud emulators firestore start --host-port=$FIRESTORE_EMULATOR_HOST
   ```

6. Launch the app either with Gunicorn or Flask:
   1. Gunicorn: `gunicorn cloud_resume.app:app`
   2. Flask: `python -m cloud_resume`
7. Open a browser to http://localhost:8080 and check it out!

### 2. Docker Compose

Docker compose is the quickest way to check out the project. The docker compose file will deploy a Google Cloud Firestore emulator alongside our cloud-resume app. The Firestore emulator container's source code/Dockerfile can be found [here](https://github.com/ridedott/firestore-emulator-docker).

#### Requirements

1. Docker & Docker-Compose

In order to launch the app without using a real Firestore database, you will need to install [Docker](https://docs.docker.com/get-started/) and [Docker Compose](https://docs.docker.com/compose/).

#### Steps

1. Clone the repository.

   ```bash
   git clone git@github.com:sbrupert/cloud-resume.git
   ```

2. Start the app with Docker Compose.
   1. From the cloud_resume python project directory:

      ```bash
      docker-compose up
      ```

3. Open a browser to http://localhost:8080 and check it out!
4. To stop the app:
   1. Press `Ctrl+C` in your terminal window where you ran `docker-compose up`.
   2. Run `docker-compose down` from the root project directory.
