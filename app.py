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
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    city_states = Venue.query.distinct(Venue.city, Venue.state).all()
    data = [venue.group_by_city_state for venue in city_states]

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    venues = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()

    data = [v.serialize for v in venues]
    response = {'count': len(venues),
                "data": data}

    return render_template('pages/search_venues.html', results=response,
                           search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
    data = venue.serialize

    upcoming_shows = list(filter(lambda x: x.start_time >=
                                           utc.localize(datetime.now()), venue.shows))
    past_shows = list(filter(lambda x: x.start_time <
                                       utc.localize(datetime.now()), venue.shows))

    data['upcoming_shows'] = upcoming_shows
    data['past_shows'] = past_shows
    data['upcoming_shows_count'] = len(upcoming_shows)
    data['past_shows_count'] = len(past_shows)

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    data = request.form

    try:
        tmp_genres = request.form.getlist('genres')
        genres = ','.join(tmp_genres)

        tmp_seeking_artist = request.form.get('seeking_artist', default=False)
        seeking_artist = True if tmp_seeking_artist == 'y' else False

        new_venue = Venue(
            name=data['name'],
            city=data['city'],
            state=data['state'],
            address=data['address'],
            phone=data['phone'],
            genres=genres,
            seeking_talent=seeking_artist,
            image_link=data['image_link'],
            facebook_link=data['facebook_link'],
            website=data['website']
        )
        db.session.add(new_venue)
        db.session.commit()
        flash('Venue ' + data['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + data['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Delete Venue
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        venue_name = venue.name

        db.session.delete(venue)
        db.session.commit()

        flash('Venue ' + venue_name + ' was successfully deleted!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + venue_name + ' could not be updated.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.distinct(Artist.id, Artist.name).all()
    data = [a.serialize for a in artists]

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    artists = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()

    data = [a.serialize for a in artists]
    response = {'count': len(artists),
                "data": data}

    return render_template('pages/search_artists.html', results=response,
                           search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
    data = artist.serialize

    upcoming_shows = list(filter(lambda x: x.start_time >=
                                           utc.localize(datetime.now()), artist.shows))
    past_shows = list(filter(lambda x: x.start_time <
                                       utc.localize(datetime.now()), artist.shows))
    data['upcoming_shows'] = upcoming_shows
    data['past_shows'] = past_shows
    data['upcoming_shows_count'] = len(upcoming_shows)
    data['past_shows_count'] = len(past_shows)

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
    data = artist.serialize
    return render_template('forms/edit_artist.html', form=form, artist=data)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    data = request.form

    try:
        tmp_genres = request.form.getlist('genres')
        genres = ','.join(tmp_genres)

        tmp_seeking_venue = request.form.get('seeking_venue', default=False)
        seeking_venue = True if tmp_seeking_venue == 'y' else False

        artist = Artist.query.get(artist_id)
        artist.name = data['name']
        artist.city = data['city']
        artist.state = data['state']
        artist.phone = data['phone']
        artist.genres = genres
        artist.seeking_venue = seeking_venue
        artist.image_link = data['image_link']
        artist.facebook_link = data['facebook_link']
        artist.website = data['website']
        db.session.commit()
        flash('Artist ' + data['name'] + ' was successfully updated!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + data['name'] + ' could not be updated.')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
    data = venue.serialize
    return render_template('forms/edit_venue.html', form=form, venue=data)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    data = request.form

    try:
        tmp_genres = request.form.getlist('genres')
        genres = ','.join(tmp_genres)

        tmp_seeking_artist = request.form.get('seeking_artist', default=False)
        seeking_artist = True if tmp_seeking_artist == 'y' else False

        venue = Venue.query.get(venue_id)
        venue.name = data['name']
        venue.city = data['city']
        venue.state = data['state']
        venue.address = data['address']
        venue.genres = genres
        venue.phone = data['phone']
        venue.seeking_talent = seeking_artist
        venue.image_link = data['image_link']
        venue.facebook_link = data['facebook_link']
        venue.website = data['website']
        db.session.commit()
        flash('Venue ' + data['name'] + ' was successfully updated!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + data['name'] + ' could not be updated.')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    data = request.form

    try:

        tmp_genres = request.form.getlist('genres')
        genres = ','.join(tmp_genres)

        tmp_seeking_venue = request.form.get('seeking_venue', default=False)
        seeking_venue = True if tmp_seeking_venue == 'y' else False

        new_artist = Artist(
            name=data['name'],
            city=data['city'],
            state=data['state'],
            phone=data['phone'],
            genres=genres,
            image_link=data['image_link'],
            facebook_link=data['facebook_link'],
            seeking_venue=seeking_venue,
            website=data['website']
        )
        db.session.add(new_artist)
        db.session.commit()
        flash('Artist ' + data['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + data['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = Show.query.all()
    data = [show.serialize for show in shows]

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/search', methods=['POST'])
def search_shows():
    search_term = request.form.get('search_term', '')

    shows = db.session.query(Show).join(Artist).join(Venue) \
        .filter(or_(Artist.name.ilike(f'%{search_term}%'),
                    Venue.name.ilike(f'%{search_term}%'))).all()

    data = [show.serialize for show in shows]
    response = {'count': len(shows),
                "data": data}

    return render_template('pages/search_show.html', results=response,
                           search_term=search_term)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    data = request.form
    try:
        from dateutil.parser import parse
        new_show = Show(
            venue_id=data['venue_id'],
            artist_id=data['artist_id'],
            start_time=parse(data['start_time'])
        )
        db.session.add(new_show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

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
