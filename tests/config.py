#!/usr/bin/python3
"""App Settings zum Zeitpunkt der Initalisierung von PynanceParser (Testinstanz)"""


LOG_ACCESS_FILE = '/tmp/pynance_access.log'
LOG_ERROR_FILE = '/tmp/pynance_error.log'

# Options:
DATABASE_BACKEND = 'tiny'
#DATABASE_BACKEND = 'mongo'

#DATABASE_URI = 'mongodb://testuser:testpassword@localhost:27017' # For mongo (URI)
DATABASE_URI = '/tmp/pynance-test' # For tiny (/path/to/)

# For tiny: Filename ('testdata.json')
# For mongo: Collection name ('testdata')
DATABASE_NAME = 'testdata.json'

IBAN = 'DE89370400440532013000'
