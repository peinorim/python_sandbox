import os
from math import inf
import dash
from dash import html
from dash import dcc
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
import plotly.graph_objects as go
import pandas as pd
import csv
from datetime import datetime

from forecast import RedisCache

app = dash.Dash(__name__)

START_DATE = datetime.strptime("2019-03-25", "%Y-%m-%d")
PERIODS = 300
TIMEOUT_STANDARD = 30

cache = RedisCache(app=app).get_cache()


def format_ada_forecast(start_date=None):
    forecast = {'ds': [], 'y': []}
    # https://production.api.coindesk.com/v2/price/values/ADA?start_date=2018-05-30T22:00&end_date=2021-08-31T20:30&ohlc=true
    with open(f'{os.getcwd()}/shib.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in spamreader:
            date = datetime.strptime(row[0], "%Y-%m-%d")
            value = float(row[1])

            if date >= start_date and isinstance(value, float):
                forecast['ds'].append(date)
                forecast['y'].append(value)

    return {'forecast': forecast}


def forecast_ada_figure(start_date=None, periods=None):
    forecast = format_ada_forecast(start_date=start_date)
    df = pd.DataFrame.from_dict(forecast['forecast'])

    m = Prophet()
    m.fit(df)
    future = m.make_future_dataframe(periods=periods)
    forecast = m.predict(future)

    forecast_fig = plot_plotly(m, forecast, uncertainty=True, plot_cap=True, trend=True, changepoints=True,
                               changepoints_threshold=0.01)

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
    html.H1(children='SHIB forecast'),
    dcc.Graph(id='forecast-graph', figure=forecast_ada_figure(start_date=START_DATE, periods=PERIODS))
])

if __name__ == '__main__':
    app.run_server(debug=True)
