#!/usr/bin/python3
'''Modul für die Kommunikation mit der Bank-API'''

import fintech


class BankAPI():
    def __init__(self):
        pass
    
    def auth(self, creds):
        self.logger.critical("NotImplemented: fintech(auth) not ready yet")

    def getEntries(self, bank):
        self.auth(self.config[bank])
        self.logger.critical("NotImplemented: fintech(fetch) not ready yet")
        return bank, []
    
    def fetchAll(self):
        for bank in self.config['DEFAULT']['Banken'].split(','):
            self.logger.info("Fetch: {}".format(bank))
            yield self.getEntries(bank)

