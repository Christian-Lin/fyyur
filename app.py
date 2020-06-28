#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO(DONE): connect to a local postgresql database
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO(DONE): replace with real venues data.
  #             num_shows should be aggregated based on number of upcoming shows per venue.
  locations = Venue.query.with_entities(func.count(Venue.id), Venue.state, Venue.city).group_by(Venue.state, Venue.city).all()
  data = []
  for loc in locations: # Nested for loop to loop over venues by location
    loc_venues = Venue.query.filter_by(state=loc.state).filter_by(city=loc.city).all()
    loc_data = []
    for venue in loc_venues:
      loc_data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": 0
      })
    data.append({
      "state": loc.state,
      "city": loc.city,
      "venues": loc_data
    })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO(DONE): implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike('%'+search_term+'%')).all()
  data = []
  for venue in venues:
    shows = Show.query.filter_by(venue_id=venue.id).all()
    num_upcoming = 0
    for show in shows:
      if show.start_time > datetime.now():
        num_upcoming += 1
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming
    })
  response = {
    "count": len(venues),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO(DONE): replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  past_shows = []
  past_shows_count = 0
  upcoming_shows = []
  upcoming_shows_count = 0
  for show in venue.shows:
    if show.start_time > datetime.now():
        upcoming_shows_count += 1
        upcoming_shows.append({
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        })
    if show.start_time < datetime.now():
        past_shows_count += 1
        past_shows.append({
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        })

  data = {
    "id": venue_id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count,
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO(DONE): insert form data as a new Venue record in the db, instead
  # TODO(DONE): modify data to be the data object returned from db insertion
  error = False
  form = VenueForm()
  try:
    name = request.form['name']
    state = request.form['state']
    city = request.form['city']
    address = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres') # Get the list of genres
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website']
    seeking_talent = True if 'seeking_talent' in request.form else False
    seeking_description = request.form['seeking_description']
    venue = Venue(name=name, state=state, city=city, address=address, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_talent=seeking_talent, seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  if error: # TODO(DONE): on unsuccessful db insert, flash an error instead. e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.'). see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + request.form['name']+ ' could not be listed.')
  if not error: #(DONE) on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO(DONE): Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash(f'An error occurred. Venue {venue_id} could not be deleted.')
  if not error:
    flash(f'Venue {venue_id} was successfully deleted.')
  return render_template('pages/home.html')
  # BONUS CHALLENGE(DONE): Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO(DONE): replace with real data returned from querying the database
  artists = Artist.query.order_by(Artist.name).all()
  data = []
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO(DONE): implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%')).all()
  data = []
  for artist in artists:
    shows = Show.query.filter_by(artist_id=artist.id).all()
    num_upcoming = 0
    for show in shows:
      if show.start_time > datetime.now():
        num_upcoming += 1
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": num_upcoming
    })
  response = {
    "count": len(artists),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO(DONE): replace with real venue data from the venues table, using venue_id
  artist = Artist.query.get(artist_id)
  if not artist: 
    return render_template('errors/404.html') # Artist not found
  past_shows = []
  past_shows_count = 0
  upcoming_shows = []
  upcoming_shows_count = 0
  for show in artist.shows:
      if show.start_time > datetime.now():
          upcoming_shows_count += 1
          upcoming_shows.append({
              "venue_id": show.venue_id,
              "venue_name": show.venue.name,
              "venue_image_link": show.venue.image_link,
              "start_time": format_datetime(str(show.start_time))
          })
      if show.start_time < datetime.now():
          past_shows_count += 1
          past_shows.append({
              "venue_id": show.venue_id,
              "venue_name": show.venue.name,
              "venue_image_link": show.venue.image_link,
              "start_time": format_datetime(str(show.start_time))
          })
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  if artist: 
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
  else:
    return render_template('errors/404.html')
  # TODO(DONE): populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO(DONE): take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  artist = Artist.query.get(artist_id)
  try:
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False 
    artist.seeking_description = request.form['seeking_description']
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  if error: 
    flash('An error occurred. Artist details did not change.')
    abort(500)
  if not error: 
    flash('Artist was successfully updated!')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  if venue:
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
  else:
    return render_template('errors/404.html')
  # TODO(DONE): populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO(DONE): take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  venue = Venue.query.get(venue_id)
  try:
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  if error: 
    flash('An error occurred. Venue details did not change.')
    abort(500)
  if not error: 
    flash('Venue was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO(DONE): insert form data as a new Venue record in the db, instead
  # TODO(DONE): modify data to be the data object returned from db insertion
  form = ArtistForm()
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = form.genres.data # Get the list of genres
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website']
    seeking_venue = True if 'seeking_venue' in request.form else False
    seeking_description = request.form['seeking_description']
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_venue=seeking_venue, seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  if error: # TODO(DONE): on unsuccessful db insert, flash an error instead e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + request.form['name']+ ' could not be listed.')
  if not error: # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  error = False
  try:
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash(f'An error occurred. Artist {artist_id} could not be deleted.')
  if not error:
    flash(f'Artist {artist_id} was successfully deleted.')
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO(DONE): replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows = Show.query.all()
  data = []
  for show in shows:
    data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
      })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO(DONE): insert form data as a new Show record in the db, instead
  error = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  if error: # TODO(DONE): on unsuccessful db insert, flash an error instead. e.g., flash('An error occurred. Show could not be listed.'). See: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Show could not be listed.')
  if not error: # on successful db insert, flash success
    flash('Show was successfully listed!')
  return render_template('pages/home.html')

@app.route('/shows/search', methods=['POST'])
def search_shows():
  search_term = request.form.get('search_term', '')
  shows = Show.query.join(Artist).filter(Artist.name.ilike('%'+search_term+'%')).all()
  data = []
  for show in shows:
    data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
      })
  response = {
    "count": len(shows),
    "data": data
  }
  return render_template('pages/search_show.html', results=response, search_term=search_term)

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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
