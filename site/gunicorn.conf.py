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
access_log_format = '{"client_ip": "%(h)s", "request_time": "%(t)s", "method": "%(m)s", "path": "%(U)s", "status": "%(s)s", "bytes": "%(B)s", "referrer": "%(f)s", "user_agent": "%(a)s"}'
