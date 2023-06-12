py -3 -m venv venv
venv\Scripts\activate

pip3 install -r requirements.txt

# $env:FLASK_DEBUG="0" 
# $env:FLASK_ENV="production" 
# $env:FLASK_APP="app/routes.py" 
flask run