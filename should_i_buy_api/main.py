"""Application entry point."""
import aiohttp
import json
import motor.motor_asyncio
import pandas as pd
import logging

from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from models.model import StockDatapoint
from pydantic import BaseSettings
from os import environ


class Settings(BaseSettings):
    """Base config."""
    app_name: str = "ShouldIBuy API"
    debug: bool = False
    mongo_url: str = f"mongodb://root:{environ.get('DBPASS')}" \
        + "@mongo:27017/admin"
    api_key: str = environ['ALPHAVANTAGE_API_KEY']


settings = Settings()
app = FastAPI(docs_url="/")
client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_url)
db = client.stock_data
BASE_URL = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
API_KEY = settings.api_key
logging.basicConfig(filename='/app/logs/api.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s : %(message)s')


async def _get_data(ticker: str, outputsize: str):
    url = f"{BASE_URL}&outputsize={outputsize}&symbol={ticker.upper()}" \
        + "&apikey={API_KEY}&datatype=csv"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            csv_response = await response.text()
            if "Error Message" not in csv_response:
                outerData = csv_response.split('\n')
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
                    logging.debug(f"{data[0]}")
                    consolidated_data_dict = {
                        'timestamp': datetime.strptime(data[0], "%Y-%m-%d")}
                    consolidated_data_dict.update({
                        "ticker": ticker})
                    consolidated_data_dict.update({
                        "open": data[1].get("open")})
                    consolidated_data_dict.update({
                        "close": data[1].get("close")})
                    consolidated_data_dict.update({
                        "high": data[1].get("high")})
                    consolidated_data_dict.update({
                        "low": data[1].get("low")})
                    datapoint_list.append(
                        StockDatapoint(**consolidated_data_dict))

                logging.debug(f"{datapoint_list}")

                return datapoint_list

            logging.error(f"Ticker {ticker} could not be found")
            raise HTTPException(status_code=404,
                                detail=f"Ticker {ticker} could not be found")


async def _update_db(ticker_coll, ticker, data):
    logging.debug(f"{ticker_coll}")
    for item in data:
        found = await ticker_coll.find_one({
            'timestamp': item.timestamp}, {'_id': 0})
        logging.debug(f"{found}")
        if found:
            found_datapoint = StockDatapoint(**found)
            logging.debug(f"{found_datapoint}")
            logging.info(f"Found a matching datapoint for Ticker {ticker}")
            if found_datapoint != item:
                logging.info(f"Updating a datapoint for Ticker {ticker}")
                logging.debug(f"{found_datapoint}")
                ticker_coll.update_one(
                    {'timestamp': item.get('timestamp')},
                    {'$set': found_datapoint.to_bson()})
        else:
            logging.info(f"Added a datapoint for Ticker {ticker}")
            ticker_coll.insert_one(item.to_bson())


async def get_all_data(ticker):
    return await _get_data(ticker, "full")


async def get_newest_data(ticker):
    return await _get_data(ticker, "compact")


async def update_db(ticker_coll, ticker):
    data = await get_newest_data(ticker)
    await _update_db(ticker_coll, ticker, data)


async def refresh_db(ticker_coll, ticker):
    data = await get_all_data(ticker)
    await _update_db(ticker_coll, ticker, data)


@app.get("/info")
async def info():
    return {
        "app_name": settings.app_name,
        "debug": settings.debug,
        "mongo_url": settings.mongo_url,
        "api_key": settings.api_key,
    }


@app.get('/stock/{ticker}')
async def get_stock_data(ticker: str):
    collection_names = await db.list_collection_names()
    ticker_collection = db[ticker]
    if ticker not in collection_names:
        logging.debug(f"{ticker} Collection Created")
        ticker_collection.insert_many(
            [doc.to_bson() for doc in await get_all_data(ticker)])
    else:
        logging.debug(f"Updating {ticker} collections")
        await update_db(ticker_collection, ticker)
    list_to_return = []
    async for doc in ticker_collection.find().limit(10):
        list_to_return.append(StockDatapoint(**doc).to_json())
    return jsonable_encoder(list_to_return)


@app.get('/stock/{ticker}/refresh')
async def refresh_stock_data(ticker: str):
    collection_names = await db.list_collection_names()
    ticker_collection = db[ticker]
    if ticker not in collection_names:
        raise HTTPException(status_code=404, detail="Ticker not found")
    else:
        logging.debug(f"Updating {ticker} collections")
        await refresh_db(ticker_collection, ticker)

    list_to_return = []
    async for doc in ticker_collection.find({}, {"_id": 0}).limit(10):
        list_to_return.append(StockDatapoint(**doc).to_json())
    return jsonable_encoder(list_to_return)


@app.get('/stock/{ticker}/should_i_buy')
async def should_i_buy(ticker: str):
    collection_names = await db.list_collection_names()
    ticker_collection = db[ticker]
    if ticker not in collection_names:
        raise HTTPException(status_code=404, detail="Ticker not in DB")

    data = []
    async for doc in ticker_collection.find().limit(5):
        data.append(StockDatapoint(**doc))
    logging.debug(f"{data}")
    close_values = [v.close for v in data]
    logging.debug(f"{close_values}")

    difference_in_days = []
    for i in range(len(close_values) - 1):
        difference_in_days.append(close_values[i] - close_values[i+1])

    time_to_buy = True
    for price_diff in difference_in_days:
        if price_diff > 0:
            time_to_buy = False

    return {"time_to_buy": time_to_buy}
