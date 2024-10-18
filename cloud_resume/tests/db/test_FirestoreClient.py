from cloud_resume.db import FirestoreClient
from cloud_resume.logger import configure_logging
from datetime import datetime, timezone

logger = configure_logging(__name__)


def test_FirestoreClient_connection(setup_firestore_emulator,monkeypatch):
    """
    Tests FirestoreClient connect_to_firestore() method.
    
    This test checks to see if the connect_to_firestore() method is able to
    establish a connection to the firestore emulator. If the class var `_db`
    is not None, then the connection was successful.
    """
    firestore_port = setup_firestore_emulator
    monkeypatch.setenv('FIRESTORE_EMULATOR_HOST', f'localhost:{firestore_port}')
    database = FirestoreClient()
    assert database._db is not None

def test_FirestoreClient_get_visitor_count(setup_firestore_database):
    """
    Tests FirestoreClient get_visitor_count() method.
    
    This test checks to see if the get_visitor_count() method is able to
    retrieve the visitor count from the firestore emulator. If the method returns
    the same value as the one injected into the emulator, then the test passes.
    """
    database, database_visitor_count, _ = setup_firestore_database
    visitor_count = database.get_visitor_count()
    logger.info(f'Retrieved visitor count: {visitor_count}')
    assert visitor_count == database_visitor_count

def test_FirestoreClient_update_visitor_count(setup_firestore_database):
    """
    Test the FirestoreClient's update_visitor_count() method.

    This test checks if the update_visitor_count() method correctly updates the 
    visitor count in the Firestore emulator. It sets a new visitor count, and then
    retrieves the value directly from the Firestore database to check if it matches
    the updated value. The test passes if the stored value matches the expected one.
    """
    database = setup_firestore_database[0]
    visitor_count = 243
    logger.info(f'Setting new visitor count {visitor_count}')
    database.update_visitor_count(visitor_count)
    assert visitor_count == database._db.collection('counters').document('visitor_count').get().to_dict().get('count')

def test_FirestoreClient_get_visitor_ip(setup_firestore_database):
    """
    Tests FirestoreClient get_visitor_ip() method.
    
    This test checks to see if the get_visitor_ip() method is able to
    retrieve the visitor's ip address from the firestore emulator. If the method is able to 
    retrieve the injected IP address and the "timestamp" field in the document, then the test passes.
    """
    database, database_visitor_count, database_visitor_ips = setup_firestore_database
    visitor_ip = list(database_visitor_ips)[0]
    logger.info(f'Retrieving visitor ip {visitor_ip}')
    visitor_doc = database.get_visitor_ip(visitor_ip)

    assert visitor_doc[0] == True
    assert visitor_doc[1]['timestamp'] is not None

def test_FirestoreClient_get_visitor_ip_notfound(setup_firestore_database):
    """
    Tests FirestoreClient get_visitor_ip() method when IP address is not found in the emulator.
    
    This test checks if the get_visitor_ip() method correctly returns False and an empty document for a non-existent IP address.
    """
    database, database_visitor_count, database_visitor_ips = setup_firestore_database
    visitor_ip = "255.255.255.255"
    logger.info(f'Retrieving visitor ip {visitor_ip}')
    visitor_doc = database.get_visitor_ip(visitor_ip)

    assert visitor_doc[0] == False
    assert visitor_doc[1] is None

def test_FirestoreClient_update_visitor_ip(setup_firestore_database):
    """
    Test the FirestoreClient's update_visitor_ip() method.

    This test will check if we are able to successfully add a new IP address to Firestore with a timestamp.
    If the method returns True, and we can retrieve the newly created ip address document with the correct timestamp, then the test passes.
    """
    database = setup_firestore_database[0]
    visitor_ip = "255.255.255.255"
    visitor_timestamp = datetime.now(timezone.utc)

    logger.info(f'Attemping to add visitor ip {visitor_ip} with timestamp to firestore database.')
    method_success = database.update_visitor_ip(visitor_ip, visitor_timestamp)

    # Try to retrieve the new ip address document from Firestore.
    logger.info(f"Retrieving new ip {visitor_ip} from firestore.")
    doc = database._db.collection('visitor_ips').document(visitor_ip).get()

    assert method_success == True, "The method did not return True to indicate successful execution."
    assert visitor_ip == doc.id, f"The ip address retrieved from Firestore is {doc.id}, and should be {visitor_ip}."
    assert visitor_timestamp == doc.to_dict()['timestamp'], f"Timestamp mismatch: Expected {visitor_timestamp}, got {doc.to_dict()['timestamp']}"