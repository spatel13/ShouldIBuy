import json
import os
import requests


API_KEY=os.environ['ALPHAVANTAGE_API_KEY']

def get_recent_5_datapoints(stock):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&outputsize=compact&symbol={stock.upper()}&apikey={API_KEY}"
    stock_data = get_data(url, 5)
    return stock_data

def get_data(url, days=-1):
    response = requests.get(url)
    json_stock_data = response.json()

    if "Error Message" not in list(json_stock_data.keys()):
        stock_data = json_stock_data.get(list(json_stock_data.keys())[1])
        recent_5_datapoints = list(stock_data.keys())[:days]

        rtn_data = {}
        for datapoint in recent_5_datapoints:
            daily = {}
            for section in list(stock_data.get(datapoint).keys()):
                section_name = section.split(" ")
                daily[section_name[1]] = float(stock_data.get(datapoint).get(section))
            rtn_data[datapoint] = daily

        return rtn_data
    return None

def check_3_days_rule(data):
    three_day_close = []
    for days in list(data.keys())[:4]:
        for key in list(data.get(days).keys()):
            if key == 'close':
                three_day_close.append(data.get(days).get(key))

    difference_in_days = []
    for i in range(len(three_day_close) - 1):
        difference_in_days.append(float(three_day_close[i]) - float(three_day_close[i+1]))

    time_to_buy = True
    for price_diff in difference_in_days:
        if price_diff > 0:
            time_to_buy = False
    
    return time_to_buy

if __name__ == '__main__':
    ticker = str(input("Enter a ticker to check: ")).upper()
    data = get_recent_5_datapoints(ticker)
    if not data:
        print(f"{ticker} could not be found.")
    else:
        print(f'TIME TO BUY {ticker}?: {check_3_days_rule(data)}')
