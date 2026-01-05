#!/bin/bash

# Generate the .htpasswd file
htpasswd -cb /etc/apache2/.htpasswd "$AUTH_USER" "$AUTH_PASSWORD"

# Start Apache in the foreground
exec apachectl -D FOREGROUND
