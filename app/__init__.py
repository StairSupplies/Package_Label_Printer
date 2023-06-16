#Initializes Flask Server Parameters
import os
import globals
from flask import Flask
from flask_socketio import SocketIO, send
# from waitress import serve

app = Flask(__name__, static_url_path='/static')
print("Init! Shazam! Server")

socketio = SocketIO(app)

#adds a security key found in the config.py file for protection
#app.config.from_object(Config)
#CORS(app)
#app.config['SECRET_KEY'] = 'you-cannot-guess'

# @app.route('/api/v1/')
# def myendpoint():
#     return 'We are computering now'
# serve(app, host='0.0.0.0', port=8080, threads=1) #WAITRESS!

#import views.py under all things above
if __name__ == '__main__':
    globals.local = True
    globals.app = app
    os.environ['FLASK_ENV'] = 'production'
    import routes
else:
    from app import routes
