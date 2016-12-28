from flask import Flask

app = Flask(__name__)

"""
This is a simple implementation of a micro Command-and-Control Server using Flask. 
Its purpose is to provide a lightweight and simple interface to coordinate an attack carried
by multiple botnet instances, ideally deployed 'round-the-clock'

(please note that in this implementation the server handles just one request at a time - flask default)
"""

@app.route('/settings', methods=['GET'])

@app.route('/update', methods=['POST'])

@app.route('/logs', methods=['GET'])

if __name__ == "__main__": 
    app.run()