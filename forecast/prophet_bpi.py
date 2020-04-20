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

START_DATE = "2018-03-25"
PERIODS = 365


def format_forecast():
    forecast = {'ds': [], 'y': []}
    PARAMS = {'start': START_DATE, 'end': datetime.now().strftime("%Y-%m-%d")}
    r = requests.get(url="http://api.coindesk.com/v1/bpi/historical/close.json", params=PARAMS)
    result = r.json()
    for res in result['bpi']:
        forecast['ds'].append(res)
        forecast['y'].append(result['bpi'][res])
    return {'forecast': forecast}


def forecast_figure():
    forecast = format_forecast()
    df = pd.DataFrame.from_dict(forecast['forecast'])

    m = Prophet()
    m.fit(df)
    future = m.make_future_dataframe(periods=PERIODS)
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


app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='BPI forecast'),
    dcc.Graph(id='forecast-graph', figure=forecast_figure())
])

if __name__ == '__main__':
    app.run_server(debug=True)
