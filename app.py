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
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    if type(value) != datetime:
        date = dateutil.parser.parse(value)
    else:
        date = value

    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    start_time = db.Column(db.DateTime(timezone=True))

    def __repr__(self):
        return f'<Show {self.id}>'

    @property
    def serialize(self):
        return {
            'id': self.id,
            'venue_id': self.venue_id,
            'artist_id': self.artist_id,
            "venue_name": self.venue.name,
            "artist_name": self.artist.name,
            "artist_image_link": self.artist.image_link,
            "start_time": self.start_time.isoformat()
        }


class Venue(db.Model):
    __tablename__ = 'venue'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    website = db.Column(db.String(120))
    shows = db.relationship("Show", cascade="all,delete", backref="venue")

    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'

    @property
    def serialize(self):

        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'address': self.address,
            'genres': self.genres.split(","),
            'phone': self.phone,
            'image_link': self.image_link,
            'seeking_talent': self.seeking_talent,
            'facebook_link': self.facebook_link,
            'website': self.website
        }

    @property
    def serialize_list(self):
        return {
            'id': self.id,
            'name': self.name,
            'num_upcoming_shows': len(list(filter(lambda x: x.start_time > utc.localize(datetime.now()), self.shows)))
        }

    @property
    def group_by_city_state(self):
        return {'city': self.city,
                'state': self.state,
                'venues': [v.serialize_list
                           for v in Venue.query.filter(Venue.city == self.city,
                                                       Venue.state == self.state).all()]}


class Artist(db.Model):
    __tablename__ = 'artist'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    website = db.Column(db.String(120))
    shows = db.relationship("Show", cascade="all,delete", backref="artist")

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'

    @property
    def serialize(self):

        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'phone': self.phone,
            'genres': self.genres.split(","),
            'image_link': self.image_link,
            'seeking_venue': self.seeking_venue,
            'facebook_link': self.facebook_link,
            'website': self.website
        }

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
