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
    
    def connect_to_firestore(self):
        """
        Establishes a connection to a Firestore database.

        If the environment variable `FIRESTORE_EMULATOR_HOST` is set, the client connects to the Firestore emulator
        at the specified address (usually used for local development and testing). Otherwise, the client connects
        to the Firestore database in the default Google Cloud Project, using the application's Google Cloud credentials.

        Once the connection is successfully established, it is stored in `self._db` for reuse across methods.

        ## Environment Variables:
            FIRESTORE_EMULATOR_HOST (str): The host address of the Firestore Emulator (e.g., 'localhost:8080').

        Returns:
            firestore.Client: A Firestore client instance representing the connection to the Firestore database.

        Raises:
            Exception: If there is an error during the connection process.
        """
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
            visitor_count (int) - The current visitor count in Firestore or None if the document doesn't exist.
        """
        try:
            self.connect_to_firestore()
            doc_ref = self._db.collection('counters').document('visitor_count')
            doc = doc_ref.get()
            if doc.exists:
                visitor_count = doc.to_dict().get('count')
                return visitor_count
            else:
                logger.error("Counter document does not exist!")
                return None
        except Exception as e:
            logger.error(f"Error retrieving visitor count from Firestore database: {e}")
            raise e

    def update_visitor_count(self, count:int):
        """
        Updates the visitor_count document in Firestore.

        Parameters:
            self (FirestoreClient): The instance of the FirestoreClient class.
            count (int): The new value for the visitor counter field.
        
        """
        try:
            self.connect_to_firestore()
            doc_ref = self._db.collection('counters').document('visitor_count')
            doc_ref.set({'count': count})
        except Exception as e:
            logger.error(f"Error updating counter document! {e}")
            raise e

    def get_visitor_ip(self, ip_address:str):
        """
        Retrieves the visitor document from Firestore based on IP address.

        Parameters:
            self (FirestoreClient): The instance of the FirestoreClient class.
            ip_address (str): The IP address of the visitor.

        Returns:
            tuple: A tuple containing:
                - bool: 'Whether visitor IP address exists in Firestore'
                - dict: 'The documents data if it exists, otherwise None.'
        """
        try:
            self.connect_to_firestore()
            doc_ref = self._db.collection('visitor_ips').document(ip_address)
            doc = doc_ref.get()
            if doc.exists:
                content = doc.to_dict()
                return True, content
            else:
                logger.warning(f"Visitor document does not exist for ip {ip_address}!")
                return False, None
        except Exception as e:
            logger.error(f"Error retrieving visitor ip address from Firestore database! {e}")
            raise e
        
    def update_visitor_ip(self, ip_address:str, timestamp:datetime) -> bool:
        """
        Updates the "visitor_ips" collection in Firestore with a document named after
        `ip_address` parameter. The document will be created with the "timestamp" field set to the 
        `timestamp` parameter.

        Note: This method will also create the document if it doesn't already exist. You may use this 
            method to update just the timestamp of an existing 

        Parameters:
            self (FirestoreClient): The instance of the FirestoreClient class.
            ip_address (str): The IP address of the visitor.
            timestamp (str): Timestamp of visit.

        Returns:
            bool: Whether the method completed successfully or not.
        """
        try:
            self.connect_to_firestore()
            doc_ref = self._db.collection('visitor_ips').document(ip_address)
            doc_ref.set({'timestamp': timestamp})
            return True
        except Exception as e:
            logger.error(f"Error adding or updating visitor ip {ip_address} in Firestore! {e}")
            return False


database = FirestoreClient()

def get_client_ip():
    """
    Retrieves the client's IP address from the request.

    If the 'X-Forwarded-For' header is present (commonly used when the client is 
    behind a proxy or load balancer), the first IP in the list will be returned.
    Otherwise, the direct client IP from the request is returned.

    Returns:
        str: The client's IP address.
    """
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
    else:
        ip = request.remote_addr
    logger.debug(f"Request client IP: {ip}")
    return ip

def cache_ip():
    """
    Checks and caches the visitor's IP address locally and in the database.

    This function first checks if the visitor's IP is stored in the local cache. If the IP is found 
    and was cached less than 24 hours ago, it is considered valid (not expired), and the function 
    returns `True`. If it has expired or isn't found locally, the function checks the Firestore 
    database. If found in Firestore and not expired, the cache is updated with the database timestamp. 
    If expired, the Firestore entry and the local cache are updated with the current timestamp.

    Returns:
        bool: True if the visitor's IP is found in the cache or database and is not expired; 
              False if the IP is expired or not found.
    """
    global database
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

        db_ip = database.get_visitor_ip(client_ip)

        if db_ip[0] == True:
            db_timestamp = db_ip[1]['timestamp']
            if db_timestamp >= (current_time - timedelta(days=1)):
                ip_cache[client_ip] = db_timestamp
                logger.debug(f"IP {client_ip} found in database and not expired.")
                return True
            else:
                ip_cache[client_ip] = current_time
                database.update_visitor_ip(client_ip, current_time)
                logger.info(f"IP {client_ip} found in database but expired. Updating timestamp.")
                return False
        else:
            ip_cache[client_ip] = current_time
            database.update_visitor_ip(client_ip, current_time)
            logger.info(f"IP {client_ip} not found in database. Adding new entry.")
            return False
    except Exception as e:
        logger.error(f"An error occurred while caching the IP: {e}")


def increment_counter():
    """
    Increments the visitor count in Firestore and caches the result.

    This function first checks if the visitor's IP is stored in the local cache. If it has expired 
    or isn't found locally, the function checks the Firestore database. The counter document will be 
    updated with the new value. If a cached value exists, it is returned instead of updating the DB.

    Returns:
        int: The incremented visitor count.
        str: "Unavailable" if the counter was not available in the cache or Firestore.
    """
    global counter_cache
    global database

    try:
        cache_result = cache_ip()
        if cache_result:
            if counter_cache is not None:
                logger.debug(f"Using cached counter value: {counter_cache}")
                return counter_cache
            else:
                visitor_count = database.get_visitor_count()
                if visitor_count is not None:
                    counter_cache = visitor_count
                    logger.info(f"Counter value retrieved from Firestore: {counter_cache}")
                    return counter_cache
                else:
                    database.update_visitor_count(1)
                    counter_cache = 1
                    logger.debug("Counter document created with initial value 1.")
                    return 1
        else:
            visitor_count = database.get_visitor_count()
            if visitor_count is not None:
                count = visitor_count + 1
                database.update_visitor_count(count)
                counter_cache = count
                logger.debug(f"Counter incremented to: {count}")
                return count
            else:
                database.update_visitor_count(1)
                counter_cache = 1
                logger.debug("Counter document created with initial value 1.")
                return 1
    except Exception as e:
        logger.error(f"An error occurred while incrementing the counter: {e}")
        return "Unavailable"