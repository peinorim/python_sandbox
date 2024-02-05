from datetime import datetime
from math import inf

import pandas as pd
import requests
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import plotly.graph_objects as go

DATE_FORMAT = "%Y-%m-%d"


class FearGreed:

    def __init__(self, start_date: str = None):
        self.start_date = start_date
        self.data = self.get_data()
        self.fear_and_greed = self.data.get('fear_and_greed')
        self.fear_and_greed_historical = self.data.get('fear_and_greed_historical')
        self.fear_and_greed_historical = self.data.get('market_momentum_sp500')

        self.fear_and_greed_score = round(self.fear_and_greed.get('score'))
        self.fear_and_greed_rating = self.fear_and_greed.get('rating')
        self.fear_and_greed_previous_close = round(self.fear_and_greed.get('previous_close'))
        self.fear_and_greed_previous_1_week = round(self.fear_and_greed.get('previous_1_week'))
        self.fear_and_greed_previous_1_month = round(self.fear_and_greed.get('previous_1_month'))
        self.fear_and_greed_previous_1_year = round(self.fear_and_greed.get('previous_1_year'))

        self.fear_and_greed_historical_data = self.data.get('fear_and_greed_historical').get('data')

    def get_data(self):
        try:
            resp = requests.get(
                url=f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/2021-01-01",
                headers={"user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0", "content-type": "application/json"}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as err:
            print(err)
            raise err


class StockAPI:

    def get_stock_data(self, symbol: str = None, start_date: str = None):
        try:
            forecast = {'ds': [], 'y': []}
            data = yf.download(symbol, start=start_date, end=datetime.now().strftime("%Y-%m-%d"))
            forecast['ds'] = data.index.tz_localize(None).tolist()
            forecast['y'] = data.Close.tolist()
            return pd.DataFrame.from_dict(forecast)
        except Exception as err:
            print(err)
            raise err

    def forecast_figure(self, symbol=None, start_date=None, periods=None):
        m = Prophet()
        m.fit(self.get_stock_data(symbol=symbol, start_date=start_date))
        future = m.make_future_dataframe(periods=periods)
        forecast = m.predict(future)

        forecast_fig = plot_plotly(m, forecast, uncertainty=True, plot_cap=True, trend=False, changepoints=True)

        forecast_fig['layout']['showlegend'] = True
        forecast_fig['layout']['width'] = inf
        forecast_fig['layout']['title'] = symbol

        forecast_fig.update_layout(
            xaxis=go.layout.XAxis(
                tickformat="%d/%m/%Y",
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                             label="1m",
                             step="month",
                             stepmode="backward"),
                        dict(count=6,
                             label="6m",
                             step="month",
                             stepmode="backward"),
                        dict(count=1,
                             label="YTD",
                             step="year",
                             stepmode="todate"),
                        dict(count=1,
                             label="1y",
                             step="year",
                             stepmode="backward"),
                        dict(step="all", label="tout")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            ),
            yaxis=dict(showgrid=True),
        )
        return forecast_fig


if __name__ == "__main__":
    api = StockAPI()
    symbol = "SP5C.PA"
    start_date = "2020-01-01"

    data = StockAPI().get_stock_data(symbol=symbol, start_date=start_date)
