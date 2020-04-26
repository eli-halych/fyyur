# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import pdb

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from pytz import utc
from sqlalchemy import create_engine, ARRAY, or_
from sqlalchemy_utils import database_exists, create_database

from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
if not database_exists(engine.url):
    create_database(engine.url)



# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
