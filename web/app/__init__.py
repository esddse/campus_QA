from flask import Flask
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config['BOOTSTRAP_SERVE_LOCAL']=True
bootstrap = Bootstrap(app)
app.config.from_object('config')

from app import views

