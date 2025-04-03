#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisklasse mit Methoden für den Programmablauf."""

import os
import sys
import json
from logging.config import dictConfig
from flask import Flask

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(parent_dir))
from app.ui import UserInterface


def create_app(config_path: str) -> Flask:
    """Creating an instance from Flask with the UserInterface as Host
    Args:
        config_path (str): Path to the Config File
    Returns: FlaskApp
    """
    # Logging
    loglevel = 'DEBUG'
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

    app = Flask("PynanceParser",
                template_folder=os.path.join(parent_dir, 'app', 'templates'),
                static_folder=os.path.join(parent_dir, 'app', 'static')
    )

    # Global Config
    app.config.from_file(config_path, load=json.load)
    if app.config.get('DATABASE_BACKEND') is None:
        raise IOError(f"Config Pfad '{config_path}' konnte nicht geladen werden !")

    with app.app_context():
        app.host = UserInterface()

    return app

if __name__ == '__main__':
    config = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        ), 'configs', 'config_default.json'
    )
    application = create_app(config)
    application.run(host='0.0.0.0', port=8110, debug=True)
