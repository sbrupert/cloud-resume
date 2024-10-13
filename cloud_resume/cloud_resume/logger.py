import logging
from pythonjsonlogger import jsonlogger
import os
from datetime import datetime, timezone
from flask import request


def configure_logging(app):
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"}
    )
    logHandler.setFormatter(formatter)
    logger = logging.getLogger(app)
    logger.addHandler(logHandler)
    logger.setLevel(LOGLEVEL)
    return logger

class RequestLoggerMiddleware:
    def __init__(self, flask_app, wsgi_app):
        self.flask_app = flask_app
        self.wsgi_app = wsgi_app

    def __call__(self,environ, start_response):
        request_start_time = datetime.now(timezone.utc)

        def log_response(status, headers, exc_info=None):
            content_length = next((value for name, value in headers if name.lower() == 'content-length'), '0')
            log_data = {
                "network.client.ip": request.headers.get('X-Forwarded-For', request.remote_addr),
                "network.client.ip_fallback": request.remote_addr,
                "http.request_time": request_start_time.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3],
                "http.method": request.method,
                "http.url_details.path": request.path,
                "http.status_code": status.split(' ')[0],
                "network.bytes_written": content_length,
                "http.referrer": request.referrer,
                "http.user_agent": request.user_agent.string,
                "source": "access_log"
            }
            # Directly log the dictionary without converting it to a JSON string
            self.flask_app.logger.info(log_data)
            return start_response(status, headers, exc_info)

        return self.wsgi_app(environ, log_response)
