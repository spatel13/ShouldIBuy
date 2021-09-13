import os
import requests
import pandas as pd
from pymongo import MongoClient
import json


API_KEY = os.environ['ALPHAVANTAGE_API_KEY']
DBPASS = os.environ['DBPASS']

def get_newest_data(stock):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&outputsize=compact&symbol={stock.upper()}&apikey={API_KEY}&datatype=csv"
    response = requests.get(url)
    if "Error Message" not in response.content.decode('utf-8'):
        outerData = response.content.decode('utf-8').split('\n')
        for i in range(len(outerData)):
            outerData[i] = outerData[i].strip().split(",")

        # print(outerData)
        data = pd.DataFrame(outerData[1:], columns=outerData[0])
        data = data.set_index(data.timestamp)
        data = data.drop("timestamp", axis=1)
        result = data.to_json(orient="index", indent=4)
        result_dict = json.loads(result)
        # print(type(result_dict))
        result_list = list(result_dict.items())
        for i in range(len(result_list)):
            consolidated_data_dict = {'timestamp': result_list[i][0]}
            consolidated_data_dict.update(result_list[i][1])
            result_list[i] = consolidated_data_dict
        # return result
        return result_list[:-1]

    return None

def get_all_data(stock):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&outputsize=full&symbol={stock.upper()}&apikey={API_KEY}&datatype=csv"
    response = requests.get(url)
    if "Error Message" not in response.content.decode('utf-8'):
        outerData = response.content.decode('utf-8').split('\n')
        for i in range(len(outerData)):
            outerData[i] = outerData[i].strip().split(",")

        # print(outerData)
        data = pd.DataFrame(outerData[1:], columns=outerData[0])
        data = data.set_index(data.timestamp)
        data = data.drop("timestamp", axis=1)
        result = data.to_json(orient="index", indent=4)
        result_dict = json.loads(result)
        # print(type(result_dict))
        result_list = list(result_dict.items())
        for i in range(len(result_list)):
            consolidated_data_dict = {'timestamp': result_list[i][0]}
            consolidated_data_dict.update(result_list[i][1])
            result_list[i] = consolidated_data_dict
        # return result
        return result_list[:-1]

    return None

def check_3_days_rule(data):
    data = list(data.close)

    difference_in_days = []
    for i in range(len(data) - 1):
        difference_in_days.append(float(data[i]) - float(data[i+1]))

    time_to_buy = True
    for price_diff in difference_in_days:
        if price_diff > 0:
            time_to_buy = False
    
    return time_to_buy

def update_db(ticker_coll, data):
    for item in data:
        found = ticker_coll.find({'timestamp': item.get('timestamp')}, {'_id': 0}).limit(1)
        found = found[0]
        if found:
            diff_items = {k: item[k] for k in list(item.keys()) if k in list(found.keys()) and item[k] != found[k]}
            if diff_items:
                print(diff_items)
                ticker_coll.update_one({'timestamp': item.get('timestamp')}, {'$set': diff_items})
        else:
            print("Added a document")
            ticker_coll.insert_one(item)

if __name__ == '__main__':
    ticker = "QQQ"
    client = MongoClient(f"mongodb://root:{DBPASS}@localhost:27017")
    dbnames = client.list_database_names()
    data = get_all_data(ticker)
    compact_data = get_newest_data(ticker)
    print(len(data))
    print(len(compact_data))
    # if "stock_data" not in dbnames:
    #     print("DB Created")
    
    # db = client["stock_data"]

    # collection_names = db.list_collection_names()
    # if ticker not in collection_names:
    #     print(f"{ticker} Collection Created")

    # stock_data_coll = db[ticker]
    # if ticker not in collection_names:
    #     stock_data_coll.insert_many(data)
    # else:
    #     update_db(stock_data_coll, data)
    
    # update_db(stock_data_coll, [{ "timestamp": "2021-09-10", "open": "381.2300", "high": "382.9700", "low": "376.2450", "close": "379.5900", "volume": "40249405" }])

    # for datapoint in stock_data_coll.find({}, {"_id": 0})[:5]:
    #     print(datapoint)

    # print(stock_data_coll.find({'timestamp': '2021-09-10'}).limit(1)[0])
