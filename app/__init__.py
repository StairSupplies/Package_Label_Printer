from flask import Flask
from flask_socketio import SocketIO, send

app = Flask(__name__, static_url_path='/static')

# Adds a security key found in the config.py file for protection
# app.config.from_object(Config)
# CORS(app)
# app.config['SECRET_KEY'] = 'you-cannot-guess'

# Create the SocketIO object
socketio = SocketIO(app)

# Import views.py (or routes.py) under the previous code
from app import routes

if __name__ == "__main__":
    # Run the app using Gunicorn
    socketio.run(app, host='0.0.0.0', port=5000)