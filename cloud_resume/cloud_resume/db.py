from cloud_resume.logger import *
import os
from datetime import datetime, timedelta, timezone
from flask import request
from google.cloud import firestore
import google.auth


# Initialize caches
ip_cache = {}
counter_cache = None

# Configure logging
logger = configure_logging("database_client")


class FirestoreClient():

    def __init__(self):
        self._db = None
        self._db = self.connect_to_firestore()
    
    def connect_to_firestore(self):
        if self._db is None:
            try:
                # Check if we are running in an emulator environment
                if os.getenv('FIRESTORE_EMULATOR_HOST'):
                    self._db = firestore.Client()
                    logger.warning("Detected Firestore Emualtor! Connecting to DB at: " + os.getenv('FIRESTORE_EMULATOR_HOST'))
                else:
                    # Initialize Firestore client with default credentials for production
                    logger.info("Connecting to Firestore DB")
                    credentials, project = google.auth.default()
                    self._db = firestore.Client(credentials=credentials, project=project)
            except Exception as e:
                logger.error(f"Error connecting to firestore database: {e}")
                return None
        return self._db
    
    def get_visitor_count(self) -> int:
        """
        Retrieves the current visitor count from Firestore.

        Parameters:
            self (FirestoreClient) - The instance of the FirestoreClient class.

        Returns:
            visitor_count (int) - The current visitor count in Firestore.
        """
        try:
            doc_ref = self._db.collection('counters').document('visitor_count')
            doc = doc_ref.get()
            if doc.exists:
                visitor_count = doc.to_dict().get('count')
                return visitor_count
            else:
                logger.error("Counter document does not exist!")
        except Exception as e:
            logger.error(f"Error retrieving visitor count from Firestore database: {e}")

    def update_visitor_count(self, count:int):
        """
        Updates the visitor_count document in Firestore.

        Parameters:
            self (FirestoreClient): The instance of the FirestoreClient class.
            count (int): The new value for the visitor counter field.
        
        """
        doc_ref = self._db.collection('counters').document('visitor_count')
        try:
            doc_ref.update({'count': count})
        except Exception as e:
            logger.error(f"Error updating counter document! {e}")

_db = None  

def get_firestore_client():
    global _db
    if _db is  None:
        try:
            # Check if we are running in an emulator environment
            if os.getenv('FIRESTORE_EMULATOR_HOST'):
                _db = firestore.Client()
                logger.warning("Detected Firestore Emualtor! Connecting to DB at: " + os.getenv('FIRESTORE_EMULATOR_HOST'))
            else:
                # Initialize Firestore client with default credentials for production
                logger.info("Connecting to Firestore DB")
                credentials, project = google.auth.default()
                _db = firestore.Client(credentials=credentials, project=project)
        except Exception as e:
            logger.error(f"Error connecting to firestore database: {e}")
    return _db

def init_db():
    global counter_cache
    try:
        _db = get_firestore_client()
        counter_doc_ref = _db.collection('counters').document('visitor_count')
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

        _db = get_firestore_client()
        ip_doc_ref = _db.collection('visitor_ips').document(client_ip)
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
    _db = get_firestore_client()
    counter_doc_ref = _db.collection('counters').document('visitor_count')

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