import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True
SQLALCHEMY_TRACK_MODIFICATIONS = False # Turn off warning

# Connect to the database
# Proxy password generated for project (Windows requirement)
# IMPORTANT: if migrate does not work ("target db not up to date"), run stamp head to update head:
            # $ flask db stamp head
            # $ flask db migrate
            # $ flask db upgrade
# TODO(DONE) IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = 'postgres://chris:admin@localhost:5432/fyyur'