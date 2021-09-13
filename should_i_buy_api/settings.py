# Flask Configuration
from os import environ

"""Base config."""
DEBUG = False
BASE_MONGO_URI = f"mongodb://root:{environ.get('DBPASS')}@mongo:27017"
DB_NAME = "stock_data"
API_KEY = environ['ALPHAVANTAGE_API_KEY']

if environ.get('FLASK_ENV') == "development":
    DEBUG = True
    BASE_MONGO_URI = "mongodb://mongo:27017"

MONGO_URI = f"{BASE_MONGO_URI}/{DB_NAME}"
