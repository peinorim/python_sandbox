# -*- coding: utf-8 -*-
# https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04
# https://flask-caching.readthedocs.io/en/latest/
from math import inf
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
from flask_caching import Cache
import redis
from redis import ConnectionError
import logging

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

TIMEOUT = 86400  # 1 day

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def get_cache():
    cache = Cache(app.server, config={
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_HOST': '127.0.0.1',
        'CACHE_REDIS_PORT': '6379',
        'CACHE_REDIS_DB': '0',
        'CACHE_REDIS_PASSWORD': 'root'
    })

    logging.basicConfig()
    rs = redis.StrictRedis(host="localhost", port=6379, db=0, password='root')

    try:
        rs.ping()
        return cache
    except ConnectionError:
        return Cache(app.server, config={
            'CACHE_TYPE': 'filesystem',
            'CACHE_DIR': 'cache-directory'
        })


cache = get_cache()


@cache.memoize(timeout=TIMEOUT)
def get_forecast():
    if os.name == 'nt':
        return None
    df = pd.read_csv('data.csv')
    m = Prophet()
    m.fit(df)
    future = m.make_future_dataframe(periods=365)
    forecast = m.predict(future)

    fig = plot_plotly(m, forecast, uncertainty=True, plot_cap=True, trend=True, changepoints=True,
                      changepoints_threshold=0.01, xlabel='ds', ylabel='y')

    fig['layout']['showlegend'] = True
    fig['layout']['width'] = inf
    return fig


app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    dcc.Graph(
        id='example-graph',
        figure=get_forecast()
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
