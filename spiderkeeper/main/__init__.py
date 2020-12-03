# -*- coding: utf-8 -*-

from flask import Flask

from flask_bootstrap import Bootstrap

from flask_basicauth import BasicAuth

app = Flask(__name__)

Bootstrap(app)

app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = 'admin'
app.config['SECRET_KEY'] = 'root'

basic_auth = BasicAuth(app)

