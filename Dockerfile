FROM ubuntu:22.04

ARG VERSION

WORKDIR /app
RUN apt-get update -y && apt-get install -y python3 python3-pip

COPY ./cloud_resume/cloud_resume /app/cloud_resume
COPY ./cloud_resume/requirements.txt /app/
COPY ./cloud_resume/gunicorn.conf.py /app

RUN pip install -r /app/requirements.txt

EXPOSE 8080

ARG IMAGE_VERSION

# Set Environment Variables to Configure Datadog APM Tracing
ENV DD_LOGS_INJECTION=true DD_PROFILING_ENABLED=true DD_APPSEC_ENABLED=true DD_APPSEC_SCA_ENABLED=true DD_AGENT_HOST=host.docker.internal DD_VERSION=${IMAGE_VERSION}
CMD ["ddtrace-run", "gunicorn", "cloud_resume.app:app"]