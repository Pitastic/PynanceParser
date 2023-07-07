#!/usr/bin/python3
"""Zunächst beispielhafter Programmablauf im prozedualen Stil (später Flask?)"""


import sys
import cherrypy
from handler.MainHandler import MainHandler


class WebFrontend(object):

    def __init__(self) -> None:
        self.Operator = MainHandler()
        return

    @cherrypy.expose
    def index(self):
        return """<html><body>
            <h2>Upload a file</h2>
            <form action="upload" method="post" enctype="multipart/form-data">
            filename: <input type="file" name="myFile" /><br />
            <input type="submit" />
            </form>
        </body></html>
        """

    @cherrypy.expose
    def upload(self, myFile):
        out = """<html>
        <body>
            myFile length: {size}<br />
            myFile filename: {filename}<br />
            myFile mime-type: {content_type}
        </body>
        </html>"""
        size = 0
        path = '/tmp/test.file'
        with open(path, 'w') as f:
            while True:
                data = myFile.file.read(8192)
                if not data:
                    break
                size += len(data)
                f.write(data)

        # Daten einlesen und in Object speichern (Bank und Format default bzw. wird geraten)
        self.Operator.read_input(path)
        self.Operator.parse()

        # Eingelesene Umsätze kategorisieren
        self.Operator.tag()

        # Verarbeitete Kontiumsätze in die DB speichern und vom Objekt löschen
        self.Operator.flush_to_db()

        return out.format(size=size, filename=myFile.filename, content_type=myFile.content_type)

    @cherrypy.expose
    def view(self, iban=None):
        if iban is None:
            iban = self.config['DEFAULT']['iban']
        rows = self.Operator.database.select()
        out = "<div>"
        for r in rows:
            out += f"<p>{r}"
        out += "</div>"
        return out

if __name__ == '__main__':
    cherrypy.quickstart(WebFrontend())
