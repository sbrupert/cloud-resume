from flask import Flask, render_template, request
from google.cloud import firestore
import google.auth
from datetime import datetime, timedelta, timezone
import os
import sys
import logging
from pythonjsonlogger import jsonlogger



app = Flask(__name__)

# Initialize caches
ip_cache = {}
counter_cache = None

# Configure logging
LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level"}
)
logHandler.setFormatter(formatter)
logger = logging.getLogger('cloud-resume')
logger.addHandler(logHandler)
logger.setLevel(LOGLEVEL)

webserver_logger = logging.getLogger('webserver')
webserver_logger.addHandler(logHandler)
webserver_logger.setLevel(LOGLEVEL)

app.logger = webserver_logger

class RequestLoggerMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
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
            app.logger.info(log_data)
            return start_response(status, headers, exc_info)

        return self.app(environ, log_response)

# Apply the middleware
app.wsgi_app = RequestLoggerMiddleware(app.wsgi_app)

# Check if we are running in an emulator environment
if os.getenv('FIRESTORE_EMULATOR_HOST'):
    db = firestore.Client()
    logger.warning("Detected Firestore Emualtor! Connecting to DB at: " + os.getenv('FIRESTORE_EMULATOR_HOST'))
else:
    # Initialize Firestore client with default credentials for production
    logger.info("Connecting to Firestore DB")
    credentials, project = google.auth.default()
    db = firestore.Client(credentials=credentials, project=project)

def init_db():
    global counter_cache
    try:
        counter_doc_ref = db.collection('counters').document('visitor_count')
        counter_doc = counter_doc_ref.get()
        if not counter_doc.exists:
            logger.info("Initializing counter in database.")
            counter_doc_ref.set({'count': 0})
            counter_cache = 0
        else:
            counter_cache = counter_doc.to_dict().get('count', 0)
            logger.debug(f"Counter retrieved from database: {counter_cache}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
    else:
        ip = request.remote_addr
    logger.debug(f"Request client IP: {ip}")
    return ip

def cache_ip():
    client_ip = get_client_ip()
    current_time = datetime.now(timezone.utc)

    try:
        if client_ip in ip_cache:
            cache_timestamp = ip_cache[client_ip]
            if cache_timestamp >= (current_time - timedelta(days=1)):
                logger.debug(f"IP {client_ip} found in cache and not expired.")
                return True
            else:
                logger.debug(f"IP {client_ip} found in cache but expired.")
                return False
        else:
            logger.debug(f"IP {client_ip} not found in cache. Checking database.")

        ip_doc_ref = db.collection('visitor_ips').document(client_ip)
        ip_doc = ip_doc_ref.get()

        if ip_doc.exists:
            db_timestamp = ip_doc.to_dict().get('timestamp')
            if db_timestamp >= (current_time - timedelta(days=1)):
                ip_cache[client_ip] = db_timestamp
                logger.debug(f"IP {client_ip} found in database and not expired.")
                return True
            else:
                ip_cache[client_ip] = current_time
                ip_doc_ref.set({'timestamp': current_time})
                logger.info(f"IP {client_ip} found in database but expired. Updating timestamp.")
                return False
        else:
            ip_cache[client_ip] = current_time
            ip_doc_ref.set({'timestamp': current_time})
            logger.info(f"IP {client_ip} not found in database. Adding new entry.")
            return False
    except Exception as e:
        logger.error(f"An error occurred while caching the IP: {e}")
        sys.exit(1) # Don't proceed further if we run into an exception.

def increment_counter():
    global counter_cache
    counter_doc_ref = db.collection('counters').document('visitor_count')

    try:
        cache_result = cache_ip()
        if cache_result:
            if counter_cache is not None:
                logger.debug(f"Using cached counter value: {counter_cache}")
                return counter_cache
            else:
                counter_doc = counter_doc_ref.get()
                if counter_doc.exists:
                    counter_cache = counter_doc.to_dict().get('count')
                    logger.info(f"Counter value retrieved from Firestore: {counter_cache}")
                    return counter_cache
                else:
                    logger.error("Counter document does not exist.")
                    return "Counter document does not exist."

        counter_doc = counter_doc_ref.get()
        if counter_doc.exists:
            count = counter_doc.to_dict().get('count', 0) + 1
            counter_doc_ref.update({'count': count})
            counter_cache = count
            logger.debug(f"Counter incremented to: {count}")
            return count
        else:
            counter_doc_ref.set({'count': 1})
            counter_cache = 1
            logger.debug("Counter document created with initial value 1.")
            return 1
    except Exception as e:
        logger.error(f"An error occurred while incrementing the counter: {e}")
        return "An error occurred while incrementing the counter."

@app.route('/')
def index():
    try:
        counter = increment_counter()
        return render_template('index.html', counter=counter)
    except Exception as e:
        logger.error(f"Error while incrementing counter: {e}")
        return "An error occurred", 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8080, debug=False)
