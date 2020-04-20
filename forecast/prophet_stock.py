import os
from datetime import datetime

import redis
import yfinance as yf
import dash
import dash_html_components as html
import dash_core_components as dcc
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
from math import inf
import pandas as pd
import plotly.graph_objects as go
from flask_caching import Cache

app = dash.Dash(__name__)

STOCK = "ACA.PA"
START_DATE = "2018-03-25"
PERIODS = 200
TIMEOUT_STANDARD = 3600 * 8


def get_cache():
    try:
        rs = redis.StrictRedis(
            host=os.environ.get('REDIS_HOST', '127.0.0.1'),
            port=os.environ.get('REDIS_PORT', '6379'),
            db=os.environ.get('REDIS_DB', '0'),
            password=os.environ.get('REDIS_PASSWORD', '')
        )
        rs.ping()
        return Cache(app.server, config={
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_HOST': os.environ.get('REDIS_HOST', '127.0.0.1'),
            'CACHE_REDIS_PORT': os.environ.get('REDIS_PORT', '6379'),
            'CACHE_REDIS_DB': os.environ.get('REDIS_DB', '0'),
            'CACHE_REDIS_PASSWORD': os.environ.get('REDIS_PASSWORD', '')
        })
    except ConnectionError:
        return Cache(app.server, config={
            'CACHE_TYPE': 'filesystem',
            'CACHE_DIR': 'cache-directory'
        })


cache = get_cache()


@cache.memoize(timeout=TIMEOUT_STANDARD)
def format_forecast(start_date=None):
    forecast = {'ds': [], 'y': []}
    df = yf.download(STOCK, start=start_date, end=datetime.now().strftime("%Y-%m-%d"))

    forecast['ds'] = df.index.tolist()
    forecast['y'] = df.Close.tolist()
    return pd.DataFrame.from_dict(forecast)


@cache.memoize(timeout=TIMEOUT_STANDARD)
def forecast_figure():
    m = Prophet()
    m.fit(format_forecast(start_date=START_DATE))
    future = m.make_future_dataframe(periods=PERIODS)
    forecast = m.predict(future)

    forecast_fig = plot_plotly(m, forecast, uncertainty=True, plot_cap=True, trend=True, changepoints=True)

    forecast_fig['layout']['showlegend'] = True
    forecast_fig['layout']['width'] = inf

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


app.layout = html.Div(children=[
    html.H1(children=f'{STOCK} forecast for the next {PERIODS} days'),
    dcc.Graph(id='forecast-graph', figure=forecast_figure())
])

if __name__ == '__main__':
    app.run_server(debug=True)
