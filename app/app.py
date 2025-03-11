#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisklasse mit Methoden für den Programmablauf."""

import os
from logging.config import dictConfig
from flask import Flask

from ui import UserInterface


def create_app() -> Flask:
    """Creating an instance from Flask with the UserInterface as Host

    Returns: FlaskApp
    """
    # Logging
    loglevel = 'INFO'
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '%(levelname)s (%(module)s): %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': loglevel,
            'handlers': ['wsgi']
        }
    })

    app = Flask("PynanceParser")

    # Global Config
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'config.py'
    )
    app.config.from_pyfile(config_path)
    if app.config.get('DATABASE_BACKEND') is None:
        raise IOError(f"Config Pfad '{config_path}' konnte nicht geladen werden !")

    with app.app_context():
        app.host = UserInterface()

    return app

if __name__ == '__main__':
    application = create_app()
    application.run(host='0.0.0.0', port=8080, debug=True)
