FROM alpine
WORKDIR /app
COPY ./site /app/
RUN apk add python3 py3-pip
RUN pip install --break-system-packages -r /app/requirements.txt
EXPOSE 8080
ENV DD_LOGS_INJECTION=true DD_PROFILING_ENABLED=true DD_APPSEC_ENABLED=true DD_APPSEC_SCA_ENABLED=true
CMD ["ddtrace-run", "gunicorn", "main:app"]