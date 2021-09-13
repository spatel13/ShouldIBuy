import utils.utils as utils

from databases.database import mongo
from flask import Blueprint, jsonify, abort, Response
from flask import current_app as app
from models.model import StockDatapoint
from pymongo.errors import DuplicateKeyError


api_bp = Blueprint('api_bp', __name__)


@api_bp.errorhandler(404)
def ticker_not_found(e):
    return jsonify(error=str(e)), 404


@api_bp.errorhandler(DuplicateKeyError)
def resource_not_found(e):
    """
    An error-handler to ensure that MongoDB
    duplicate key errors are returned as JSON.
    """
    return jsonify(error="Duplicate key error."), 400


@api_bp.route('/stock/<string:ticker>', methods=['GET'])
def get_stock_data(ticker):
    collection_names = mongo.db.list_collection_names()
    ticker_collection = mongo.db[ticker]
    if ticker not in collection_names:
        app.logger.debug(f"{ticker} Collection Created")
        ticker_collection.insert_many(
            [doc.to_bson() for doc in utils.get_all_data(ticker)])
    else:
        app.logger.debug(f"Updating {ticker} collections")
        utils.update_db(ticker_collection, ticker)

    last_10 = ticker_collection.find().limit(10)
    list_to_return = []
    for doc in last_10:
        list_to_return.append(StockDatapoint(**doc).to_json())
    return jsonify(list_to_return)


@api_bp.route('/stock/<string:ticker>/refresh', methods=['GET'])
def refresh_stock_data(ticker):
    collection_names = mongo.db.list_collection_names()
    ticker_collection = mongo.db[ticker]
    if ticker not in collection_names:
        abort(Response(f"Ticker {ticker} not found in DB", 404))
    else:
        app.logger.debug(f"Updating {ticker} collections")
        utils.update_db(ticker_collection, ticker)

    last_10 = list(ticker_collection.find({}, {"_id": 0}).limit(10))
    return jsonify(last_10)


@api_bp.route('/stock/<string:ticker>/should_i_buy', methods=['GET'])
def should_i_buy(ticker):
    collection_names = mongo.db.list_collection_names()
    ticker_collection = mongo.db[ticker]
    if ticker not in collection_names:
        abort(Response(f"Ticker {ticker} not found in DB", 404))

    data = []
    recent_5 = ticker_collection.find().limit(5)
    for doc in recent_5:
        data.append(StockDatapoint(**doc))
    app.logger.debug(f"{data}")
    close_values = [v.close for v in data]
    app.logger.debug(f"{close_values}")

    difference_in_days = []
    for i in range(len(close_values) - 1):
        difference_in_days.append(close_values[i] - close_values[i+1])

    time_to_buy = True
    for price_diff in difference_in_days:
        if price_diff > 0:
            time_to_buy = False

    return {"time_to_buy": time_to_buy}
