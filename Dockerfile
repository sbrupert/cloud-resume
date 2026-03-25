FROM node:22-alpine AS frontend-builder

WORKDIR /app/cloud_resume

COPY ./cloud_resume/package.json ./cloud_resume/package-lock.json ./cloud_resume/tailwind.config.js ./
COPY ./cloud_resume/assets ./assets
COPY ./cloud_resume/cloud_resume ./cloud_resume

RUN npm ci && npm run build:assets

FROM ubuntu:24.04

WORKDIR /app
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN python3 -m venv "${VIRTUAL_ENV}"

COPY ./cloud_resume/requirements.txt /app/
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

COPY ./cloud_resume/cloud_resume /app/cloud_resume
COPY --from=frontend-builder /app/cloud_resume/cloud_resume/static/css /app/cloud_resume/static/css
COPY --from=frontend-builder /app/cloud_resume/cloud_resume/static/fonts /app/cloud_resume/static/fonts
COPY ./cloud_resume/gunicorn.conf.py /app

EXPOSE 8080

ARG IMAGE_VERSION

# Set Environment Variables to Configure Datadog APM Tracing
ENV DD_LOGS_INJECTION=true DD_PROFILING_ENABLED=true DD_APPSEC_ENABLED=true DD_APPSEC_SCA_ENABLED=true DD_AGENT_HOST=host.docker.internal DD_VERSION=${IMAGE_VERSION} SITE_VERSION=${IMAGE_VERSION}
CMD ["ddtrace-run", "gunicorn", "cloud_resume.app:app"]
