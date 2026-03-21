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
COPY ./cloud_resume/gunicorn.conf.py /app

EXPOSE 8080

ARG IMAGE_VERSION

# Set Environment Variables to Configure Datadog APM Tracing
ENV DD_LOGS_INJECTION=true DD_PROFILING_ENABLED=true DD_APPSEC_ENABLED=true DD_APPSEC_SCA_ENABLED=true DD_AGENT_HOST=host.docker.internal DD_VERSION=${IMAGE_VERSION} SITE_VERSION=${IMAGE_VERSION}
CMD ["ddtrace-run", "gunicorn", "cloud_resume.app:app"]
