import pytest
import docker
import time
from datetime import datetime, timezone
from cloud_resume.logger import configure_logging
from cloud_resume.db import FirestoreClient

logger = configure_logging(__name__)

@pytest.fixture(scope="module")
def monkeymodule():
    """
    Provides a fixture for patching modules using pytest's MonkeyPatch. Normally MonkeyPatch is scoped to the function level.

    Yields:
        A context manager that allows patching of individual modules.
    """
    with pytest.MonkeyPatch.context() as monkeypatch:
        yield monkeypatch

@pytest.fixture(scope="module")
def setup_firestore_emulator():
    """
    Sets up a Firestore emulator using Docker and returns the port on which it is running.

    This fixture waits for the emulator to start, then yields the port number. Finally,
    it stops and removes the emulator container once testing is complete.

    Yields:
        firestore_port (int): The port number on which the Firestore emulator is running.
    """
    docker_client = docker.from_env()
    container = docker_client.containers.run("ghcr.io/ridedott/firestore-emulator:latest", detach=True, publish_all_ports=True)
    while container.status != "running":
        logger.info("Waiting for firestore emulator to start")
        time.sleep(1)
        container.reload()
        if container.status == "running":
            for port, mappings in container.attrs['NetworkSettings']['Ports'].items():
                if mappings is not None:
                    firestore_port = mappings[0]['HostPort']
                    logger.info(f"Firestore emulator is ready on port {firestore_port}! Container ID: {container.id}")
            break
    yield firestore_port

    logger.info("Stopping and removing firestore emulator")
    container.kill()
    container.remove()

@pytest.fixture(scope="module")
def setup_firestore_database(setup_firestore_emulator, monkeymodule):
    """
    Sets up a Firestore database with test data.

    This fixture creates a Firestore database client using the Firestore emulator,
    then injects data into the database for testing.

    Parameters:
        setup_firestore_emulator (fixture): Fixture that manages the Firestore emulator. Uses the port number.
        monkeymodule (fixture): Module scoped monkeypatch fixture.

    Yields:
        tuple: A tuple containing:
            - database_client (object): The initialized Firestore database client.
            - visitor_count (int): The visitor count injected into the database.
    """
    firestore_port = setup_firestore_emulator
    monkeymodule.setenv('FIRESTORE_EMULATOR_HOST', f'localhost:{firestore_port}')
    database_client = FirestoreClient()
    database = database_client._db

    logger.info("Injecting test data into the database.")
    
    # Add in count data to the test database.
    visitor_count = 127
    database.collection('counters').document('visitor_count').set({'count': visitor_count})
    
    # Add visitor ip with timestamp to the test database.
    current_time = datetime.now(timezone.utc)
    visitor_ips = {
        '192.168.1.5': {'timestamp': current_time}
    }
    for key, value in visitor_ips.items():
        database.collection('visitor_ips').document(key).set({'timestamp': value['timestamp']})
    yield database_client, visitor_count, visitor_ips
