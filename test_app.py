#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisc Module for easy Imports and Methods"""

import os
import sys
import cherrypy
import pytest
from cherrypy.test import helper

# Import Server Startup
from app import UserInterface


class TestClass(helper.CPWebCase):
    """Testen der Endpunkte und Basisfunktionen"""

    def setUp(self):
        self.do_gc_test = False
        #cherrypy.engine.subscribe('stop', finally_delete_files)
        #TODO: Delete Testfiles if any

    @staticmethod
    def setup_server():
        """Server start (wie originale App)"""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'testdata',
            'test_config.conf'
        )
        cherrypy.config.update(config_path)
        assert cherrypy.config.get('database.backend')

        cherrypy.quickstart(UserInterface(), "/", config_path)
        #cherrypy.tree.mount(UserInterface(), "/", config_path)
        #cherrypy.engine.start()
        #cherrypy.engine.block()
    
    def test_index(self):
        """/index"""
        self.getPage("/")
        self.assertStatus('200 OK')

    def test_view(self):
        """/view"""
        self.getPage("/view")
        self.assertStatus('200 OK')

    def test_view_iban(self):
        """/view"""
        self.getPage(f"/view?iban={cherrypy.config['iban']}")
        self.assertStatus('200 OK')


@pytest.fixture(scope='module', autouse=False)
def finally_delete_files(request):
    """Clean Up Testfiles"""
    #TODO: Server muss beim Shutdown die Datei (aktiv) freigeben (close Connection)
    #def delete_db():
    print("Deleting Database")
    os.remove(os.path.join(
            cherrypy.config['database.uri'],
            cherrypy.config['database.name']
    ))
    #request.addfinalizer(delete_db)