from cloud_resume.db import FirestoreClient
from cloud_resume.logger import configure_logging

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
    database, database_visitor_count = setup_firestore_database
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
