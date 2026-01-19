#!/usr/bin/python3
"""App Settings zum Zeitpunkt der Initalisierung von PynanceParser (Testinstanz)"""

import os

LOG_ACCESS_FILE = '/tmp/pynance_access.log'
LOG_ERROR_FILE = '/tmp/pynance_error.log'

# Options:

# - Login Password (overwrite to not use the system env variable)
PASSWORD = os.getenv('AUTH_PASSWORD', 'change_this_password')

# - Database Backend ('tiny' or 'mongo')
#DATABASE_BACKEND = 'mongo'
DATABASE_BACKEND = 'tiny'

#DATABASE_URI = 'mongodb://testuser:testpassword@localhost:27017' # For mongo (URI)
DATABASE_URI = '/tmp/pynance-test' # For tiny (/path/to/)

# For tiny: Filename ('testdata.json')
# For mongo: Collection name ('testdata')
#DATABASE_NAME = 'testdata'
DATABASE_NAME = 'testdata.json'
