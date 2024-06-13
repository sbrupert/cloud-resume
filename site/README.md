# Cloud Resume Application

This flask application is designed to host a resume in html format from [`./templates/index.html`](templates\index.html). The resume contains a spot for a visitor counter which executes the [`increment_counter()`](https://github.com/sbrupert/cloud-resume/blob/12a9cd246dd8c619053356bbc771284454816511/site/main.py#L102) function. The application is designed to be deployed with Gunicorn and logs in JSON format so we can ingest them into logging tools like Datadog, Fluentd, etc.

## Features

- Track number of visitors to the site.
- Caches IPs locally to minimize database reads. (For helping stay within Firestore free tier.)
- Configurable logging level through environment variable
- Supports running with the Google Firestore emulator mode for local development/testing

## Configuration

### Environment Variables

- `LOGLEVEL`: Sets the logging level. Default is `INFO`. Can be set to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
- `FIRESTORE_EMULATOR_HOST`: If set, the application connects to the Firestore emulator instead of the production Firestore.

### Getting Started Guide
#### Pre-Requisites
In order to launch the app without using a real Firestore database, you will need to install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install). Follow the official installation instructions and return here when done.
#### Steps:
1. Clone the repository
   1. `git clone git@github.com:sbrupert/cloud-resume.git`
2. Change to the "site" directory
   1. `cd site`
3. Launch the app either with Gunicorn or Flask:
   1. Gunicorn: `gunicorn main:app`
   2. Flask: `python main.py`
4. Open a browser to http://localhost:8080 and check it out!

### Example Running with Firestore Emulator

```bash
gcloud emulators firestore start --host-port=localhost:8181
# In another terminal starting at the root of the repo.
cd site
export LOGLEVEL=DEBUG
export FIRESTORE_EMULATOR_HOST=localhost:8181
gunicorn -c gunicorn.conf.py main:app
```
