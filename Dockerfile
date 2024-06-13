FROM alpine
WORKDIR /app
COPY ./site /app/
RUN apk add python3 py3-pip
RUN pip install --break-system-packages -r /app/requirements.txt
EXPOSE 8080
CMD ["gunicorn", "main:app"]