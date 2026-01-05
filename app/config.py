#!/usr/bin/python3
"""App Settings zum Zeitpunkt der Initalisierung von PynanceParser"""

# Logging (will also log in webserver logs if used via wsgi)
LOG_ACCESS_FILE = '/tmp/pynance_access.log'
LOG_ERROR_FILE = '/tmp/pynance_error.log'

# Options:
DATABASE_BACKEND = 'tiny' #  or 'mongo'

# For tiny: Path to the Folder (/path/to)
# For mongo: MongoDB URI
DATABASE_URI = '/tmp' # or 'mongodb://testuser:testpassword@localhost:27017'

# For tiny: Filename ('testdata.json')
# For mongo: Collection name ('testdata')
DATABASE_NAME = 'testdata.json' # or 'testdata'
