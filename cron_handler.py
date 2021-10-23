#!/usr/bin/python3
'''Handler für den Bankenabruf'''


import sys
from datetime import datetime
from fetch import BankAPI
from db import DbInterface


def helpText():
    print("Usage: {} PATH-TO-CONFIG".format(sys.argv[0]))
    print()
    print("PATH-TO-CONFIG\tPfad zur Config mit den verschiedenen Zuagngsdaten")
    print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        helpText()
        sys.exit()
    
    # Load Config und Handler
    configpath = sys.argv[1]
    bank = BankAPI(configpath)
    db = DbInterface(configpath)

    # Fetch und Save
    print("[{}] Hole neue Umsätze".format(datetime.now().strftime('%Y-%m-%d %X')))
    for result in bank.fetchAll():
        if result[1]:
            db.insert(result)
        else:
            print("[{}] Keine Umsätze !")