#Initializes Flask Server Parameters
from flask import Flask
from flask_socketio import SocketIO, send


app = Flask(__name__, static_url_path='/static')

#adds a security key found in the config.py file for protection
#app.config.from_object(Config)
#CORS(app)
#app.config['SECRET_KEY'] = 'you-cannot-guess'

if __name__ == "__main__":
    socketio = SocketIO(app)



#import views.py under all things above
from app import routes
