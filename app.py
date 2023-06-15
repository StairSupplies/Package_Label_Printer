#Initializes Flask Server Parameters
from flask import Flask
from flask_socketio import SocketIO, send
from flask_cors import CORS



from api.application import create_app

if __name__ == '__main__':
    create_app = create_app()
    create_app.run()
else:
    gunicorn_app = create_app()

socketio = SocketIO(app)

#import views.py under all things above
from app import routes
