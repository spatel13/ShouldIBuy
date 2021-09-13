import json
import requests
import pandas as pd

from datetime import datetime
from flask import abort, Response
from flask import current_app as app
from models.model import StockDatapoint

BASE_URL = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
API_KEY = app.config.get("API_KEY")


def _get_data(ticker: str, outputsize: str):
    url = f"{BASE_URL}&outputsize={outputsize}&symbol={ticker.upper()}" \
        + "&apikey={API_KEY}&datatype=csv"
    response = requests.get(url)
    if "Error Message" not in response.content.decode('utf-8'):
        outerData = response.content.decode('utf-8').split('\n')
        for i in range(len(outerData)):
            outerData[i] = outerData[i].strip().split(",")

        data = pd.DataFrame(outerData[1:], columns=outerData[0])
        data = data.set_index(data.timestamp)
        data = data.drop("timestamp", axis=1)
        json_str = data.to_json(orient="index", indent=4)
        data_dict = json.loads(json_str)
        data_list = list(data_dict.items())
        datapoint_list = []
        for data in data_list[:-1]:
            app.logger.debug(f"{data[0]}")
            consolidated_data_dict = {
                'timestamp': datetime.strptime(data[0], "%Y-%m-%d")}
            consolidated_data_dict.update({"ticker": ticker})
            consolidated_data_dict.update({"open": data[1].get("open")})
            consolidated_data_dict.update({"close": data[1].get("close")})
            consolidated_data_dict.update({"high": data[1].get("high")})
            consolidated_data_dict.update({"low": data[1].get("low")})
            datapoint_list.append(StockDatapoint(**consolidated_data_dict))

        app.logger.debug(f"{datapoint_list}")

        return datapoint_list

    app.logger.error(f"Ticker {ticker} could not be found")
    abort(Response(f"Ticker {ticker} could not be found", 404))


def _update_db(ticker_coll, ticker, data):
    for item in data:
        found = ticker_coll.find_one({'timestamp': item.timestamp}, {'_id': 0})
        app.logger.debug(f"{found}")
        if found:
            found_datapoint = StockDatapoint(**found)
            app.logger.debug(f"{found_datapoint}")
            app.logger.info(f"Found a matching datapoint for Ticker {ticker}")
            if found_datapoint != item:
                app.logger.info(f"Updating a datapoint for Ticker {ticker}")
                app.logger.debug(f"{found_datapoint}")
                ticker_coll.update_one(
                    {'timestamp': item.get('timestamp')},
                    {'$set': found_datapoint.to_bson()})
        else:
            app.logger.info(f"Added a datapoint for Ticker {ticker}")
            ticker_coll.insert_one(item.to_bson())


def get_all_data(ticker):
    return _get_data(ticker, "full")


def get_newest_data(ticker):
    return _get_data(ticker, "compact")


def update_db(ticker_coll, ticker):
    data = get_newest_data(ticker)
    _update_db(ticker_coll, ticker, data)


def refresh_db(ticker_coll, ticker):
    data = get_all_data(ticker)
    _update_db(ticker_coll, ticker, data)
