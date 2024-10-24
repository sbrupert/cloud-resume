import pytest
from flask import Flask
from cloud_resume.db import get_client_ip

@pytest.fixture()
def app():
    app = Flask(__name__)
    app.config.update({
        'TESTING': True
    })

    yield app

@pytest.mark.parametrize("x_forwarded_for, remote_addr, expected_ip", [
    # Make sure remote_addr is used when X-Forwarded-For is missing
    (None, '127.0.0.1', '127.0.0.1'),
    
    # Use X-Forwarded-For by default    
    ('127.0.0.1', None, '127.0.0.1'),
    
    # X-Forwarded-For takes precedence over remote_addr
    ('127.0.0.1', '127.0.0.2', '127.0.0.1'),
    
    # Test for multiple X-Forwarded-For values, should use the first one. (Proxies append their IP to X-Forwarded-For.)
    ('127.0.0.1, 10.0.10.1, 192.168.1.1', None, '127.0.0.1'),
    
    # Test for all missing values. TO-DO: this should probably be an exception test.
    (None, None, None)
], ids=["x_forward_missing", "x_forward_default", "x_forward_precedence", "multiple_x_forward", "all_missing" ])


def test_get_client_ip(app,x_forwarded_for,remote_addr,expected_ip):
    """
    Test the get_client_ip() function.

    This test checks to see if the get_client_ip() function returns the correct IP address based on the availability of the X-Forwarded-For header
    or the request Remote Address (request.remote_addr).

    This test runs different scenarios to ensure the correct IP is returned for each scenario. Please see the pytest parameterization section above
    for all the tested scenarios and their expexted results.
    """
    _headers = {}
    _environ_base = {}

    # Configure request context config based on if we're testing the X-Forwarded-For header or the remote address property.
    _headers = {'X-Forwarded-For': x_forwarded_for} if x_forwarded_for else {}
    _environ_base = {'REMOTE_ADDR': remote_addr} if remote_addr else {}

    with app.test_request_context(headers=_headers, environ_base=_environ_base):
        ip = get_client_ip()
        assert ip == expected_ip
