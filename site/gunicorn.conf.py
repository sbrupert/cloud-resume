import logging
import os
from pythonjsonlogger import jsonlogger

bind = "0.0.0.0:8080"
accesslog = "-"
errorlog = "-"

# Configure logging level from environment or default to INFO
LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()

# Configure JSON formatter
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level"}
)

# Set up handlers
logHandler = logging.StreamHandler()
logHandler.setFormatter(formatter)

# Configure Gunicorn loggers
gunicorn_logger = logging.getLogger('gunicorn.error')
gunicorn_logger.addHandler(logHandler)
gunicorn_logger.setLevel(LOGLEVEL)
access_log_format = '{"network.client.ip": "%({x-forwarded-for}i)s","network.client.fallback_ip": "%(h)s" ,"http.request_time": "%(t)s", "http.method": "%(m)s", "http.url_details.path": "%(U)s", "http.status_code": "%(s)s", "network.bytes_written": "%(B)s", "http.referrer": "%(f)s", "http.user_agent": "%(a)s"}'
