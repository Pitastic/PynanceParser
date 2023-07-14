#!/usr/bin/python3 # pylint: disable=invalid-name
"""Basisc Module for easy Imports and Methods"""

import os
import cherrypy
import pytest
from cherrypy.test import helper

# Import Server Startup
from app import UserInterface


class TestClass(helper.CPWebCase):
    """Testen der Endpunkte und Basisfunktionen"""

    def setUp(self):
        # Pass GC Test from CherryPy (will fail otherwise)
        self.do_gc_test = False

    @staticmethod
    def setup_server():
        """Server start (wie originale App)"""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'testdata',
            'config.conf'
        )
        cherrypy.config.update(config_path)
        assert cherrypy.config.get('database.backend')

        cherrypy.tree.mount(UserInterface(), "/", config_path)
        cherrypy.engine.start()
        cherrypy.engine.exit()


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


@pytest.fixture(scope='session', autouse=True)
def cleanup_testfiles():
    """CleaUp"""
    yield
    print("CleanUp: Deleting Testdatabase....")
    os.remove(os.path.join(
            cherrypy.config['database.uri'],
            cherrypy.config['database.name']
    ))
