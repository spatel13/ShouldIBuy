import os
import requests
import pandas as pd


API_KEY=os.environ['ALPHAVANTAGE_API_KEY']

def get_recent_5_datapoints(stock):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&outputsize=compact&symbol={stock.upper()}&apikey={API_KEY}&datatype=csv"
    response = requests.get(url)
    if "Error Message" not in response.content.decode('utf-8'):
        outerData = response.content.decode('utf-8').split('\n')
        for i in range(len(outerData)):
            outerData[i] = outerData[i].strip().split(",")

        # print(outerData)
        data = pd.DataFrame(outerData[1:], columns=outerData[0])
        return list(data.head().close)

    return None

def check_3_days_rule(data):
    difference_in_days = []
    for i in range(len(data) - 1):
        difference_in_days.append(float(data[i]) - float(data[i+1]))

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