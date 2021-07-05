import os
import requests
import pandas as pd

from flask import Flask


API_KEY=os.environ['ALPHAVANTAGE_API_KEY']

app = Flask(__name__)

@app.errorhandler(404)
def ticker_not_found(e):
    return f"Sorry, we could not find the ticker"

@app.route('/stock/<string:ticker>', methods=['GET', 'POST'])
def get_stock_data(ticker):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&outputsize=compact&symbol={ticker.upper()}&apikey={API_KEY}&datatype=csv"
    response = requests.get(url)
    if "Error Message" not in response.content.decode('utf-8'):
        app.logger.debug(f"Found data")
        outerData = response.content.decode('utf-8').split('\n')
        for i in range(len(outerData)):
            outerData[i] = outerData[i].strip().split(",")

        app.logger.debug(f"Processing data")
        data = pd.DataFrame(outerData[1:], columns=outerData[0])
        data = data.set_index(data.timestamp)
        data = data.drop("timestamp", axis=1)
        data = list(data.head().close)

        difference_in_days = []
        for i in range(len(data) - 1):
            difference_in_days.append(float(data[i]) - float(data[i+1]))

        time_to_buy = True
        for price_diff in difference_in_days:
            if price_diff > 0:
                time_to_buy = False
        
        return {"Time to Buy?": time_to_buy}
    app.logger.error(f"Could not find ticker: {ticker}")
    return ticker_not_found(404)

if __name__ == '__main__':
    app.run(host='localhost', port=8080, use_reloader=True)