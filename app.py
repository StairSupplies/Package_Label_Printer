#Initializes Flask Server Parameters
from flask import Flask
from flask_socketio import SocketIO, send
from flask_cors import CORS



#app = Flask(__name__)

#adds a security key found in the config.py file for protection
#CORS(app)
#app.config.from_pyfile('config.py')

socketio = SocketIO(app)

#import views.py under all things above
from app import routes
