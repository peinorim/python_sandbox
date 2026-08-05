import os
import pickle
from datetime import datetime, timedelta

import pandas as pd
import requests
import yfinance as yf
from dash import html, dcc

from forecast import Forecast
from redis_cache_client import RedisCache

DATE_FORMAT = "%Y-%m-%d"
EXPIRE_CACHE_SECONDS = 300
redis_conn = RedisCache()


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
        self.market_volatility_vix_data = self.data.get('market_volatility_vix').get('data')
        self.market_momentum_sp500_data = self.data.get('market_momentum_sp500').get('data')

    def get_data(self):
        try:
            resp = requests.get(
                url=f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/2021-01-01",
                headers={"user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
                         "content-type": "application/json"},
                proxies={"http": "http://localhost:3128", "https": "http://localhost:3128"} if os.getenv("OFFICE",
                                                                                                         "false") == "true" else None
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as err:
            print(err)
            raise err

    def format_indice_data(self, indice_name: str = None):
        try:
            indice_data = self.data.get(indice_name).get('data')
            forecast = {'ds': [], 'y': []}
            for item in indice_data:
                dt_object = datetime.fromtimestamp(round(int(item.get('x')) / 1000))
                forecast['ds'].append(dt_object)
                forecast['y'].append(int(item.get('y')))

            return pd.DataFrame.from_dict(forecast)
        except Exception as err:
            print(err)
            raise err


class StockAPI:

    def get_stock_figures(self, symbols: list = None, start_date=None, periods=None, to_html: bool = False):
        stocks = []
        for symbol in symbols:
            cache_key = f"{symbol}-{start_date}-{periods}"
            cached = redis_conn.get(cache_key)

            if not cached:
                info, data = self.get_stock_data(symbol=symbol, start_date=start_date)
                figure = Forecast().render_figure(symbol=symbol, info=info, data=data, periods=periods)
                redis_conn.set(cache_key, pickle.dumps(figure), ex=EXPIRE_CACHE_SECONDS)
            else:
                figure = pickle.loads(cached)

            if to_html:
                figure.write_html(f"offline/{symbol}.html", include_plotlyjs='cdn', full_html=False)

            stocks.append(
                html.Div(children=[
                    dcc.Graph(id=f'forecast-{symbol.lower()}', figure=figure)
                ], className='col-sm-12 col-md-6')
            )
        return stocks

    def get_stock_data(self, symbol: str = None, start_date: str = None):
        try:
            forecast = {'ds': [], 'y': []}

            if os.getenv("OFFICE", "false") == "true":
                from curl_cffi import requests
                yf.config.network.proxy = {'http': "http://localhost:3128", 'https': "http://localhost:3128"}

                with requests.Session(impersonate="chrome110") as session:
                    session.verify = False
                    info = yf.Ticker(ticker=symbol, session=session).info
                    data = yf.download(symbol, start=start_date,
                                       end=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                                       ignore_tz=True, session=session)

            else:
                info = yf.Ticker(ticker=symbol).info
                data = yf.download(symbol, start=start_date,
                                   end=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                                   ignore_tz=True)

            forecast['ds'] = data.index.tolist()
            forecast['y'] = data.Close.stack().tolist()
            return info, pd.DataFrame.from_dict(forecast)
        except Exception as err:
            print(err)
            raise err
