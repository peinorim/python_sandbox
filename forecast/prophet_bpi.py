from math import inf
import dash
import dash_html_components as html
import dash_core_components as dcc
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime

from forecast import RedisCache

app = dash.Dash(__name__)

START_DATE = "2018-03-25"
PERIODS = 200
TIMEOUT_STANDARD = 30

cache = RedisCache(app=app).get_cache()


@cache.memoize(timeout=TIMEOUT_STANDARD)
def format_forecast(start_date=None):
    forecast = {'ds': [], 'y': []}
    PARAMS = {'start': start_date, 'end': datetime.now().strftime("%Y-%m-%d")}
    r = requests.get(url="http://api.coindesk.com/v1/bpi/historical/close.json", params=PARAMS)
    result = r.json()
    for res in result['bpi']:
        forecast['ds'].append(res)
        forecast['y'].append(result['bpi'][res])
    return {'forecast': forecast}


def forecast_figure(start_date=None, periods=None):
    forecast = format_forecast(start_date=start_date)
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
    html.H1(children='BPI forecast'),
    dcc.Graph(id='forecast-graph', figure=forecast_figure(start_date=START_DATE, periods=PERIODS))
])

if __name__ == '__main__':
    app.run_server(debug=True)
