"""Setup for Pytests"""

import os
import sys
import pytest

# Add Parent for importing from Modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper import MockDatabase
from app.server import create_app


@pytest.fixture(scope="module")
def test_app():
    """Managing Test-Flask-App for Tests"""
    # Creating App
    #shutil.rmtree("/tmp/pihomie-test", ignore_errors=True)
    #os.makedirs("/tmp/pihomie-test", exist_ok=True)

    # Config
    root_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(
        root_path,
        'config.py'
    )

    # App Context
    app = create_app(config_path)
    with app.app_context():
        app.host.db_handler.truncate()
        yield app

    #if os.path.isdir("/tmp/pihomie-test"):
    #    shutil.rmtree("/tmp/pihomie-test")

@pytest.fixture(scope="module")
def mocked_db():
    """Special Instance with mocked DB"""
    # Creating App
    #shutil.rmtree("/tmp/pihomie-test", ignore_errors=True)
    #os.makedirs("/tmp/pihomie-test", exist_ok=True)

    # Config
    root_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(
        root_path,
        'config.py'
    )

    # App Context
    app = create_app(config_path)
    with app.app_context():
        app.host.db_handler = MockDatabase()
        yield app

    #if os.path.isdir("/tmp/pihomie-test"):
    #    shutil.rmtree("/tmp/pihomie-test")

def mock_method(*args, **kwargs):
    """Function for overwriting Method which return 'None'"""
    print(f"Mocked Method: {args} {kwargs}")
    return
