#!/usr/bin/python3 # pylint: disable=invalid-name
"""Testfile: Basics und Endpoints"""

import os
import sys
import cherrypy
from cherrypy.test import helper
import pytest

# Add Parent for importing from 'app.py'
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import Server Startup
from src.app import UserInterface # pylint: disable=wrong-import-position


class BasicTests(helper.CPWebCase):
    """Testen der Endpunkte und Basisfunktionen"""

    @staticmethod
    def setup_server():
        """Server start (wie originale App)"""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'test_config.conf'
        )
        cherrypy.config.update(config_path)
        assert cherrypy.config.get('database.backend')

        cherrypy.quickstart(UserInterface(), '/', config_path)

    def test_index(self):
        """/index"""
        self.getPage("/")
        self.assertStatus('200 OK')

    def test_view(self):
        """/view"""
        self.getPage("/view")
        self.assertStatus('200 OK')


@pytest.fixture(scope='session', autouse=True)
def finally_delete_files(request):
    """Clean Up Testfiles"""
    #TODO: Server muss beim Shutdown die Datei (aktiv) freigeben (close Connection)
    def delete_db():
        os.remove(os.path.join(
                cherrypy.config['database.uri'],
                cherrypy.config['database.name']
        ))
    request.addfinalizer(delete_db)
