from math import inf

import dash
import dash_html_components as html
import dash_core_components as dcc
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
import requests
import pandas as pd
import plotly.graph_objects as go

app = dash.Dash(__name__)
PERIODS = 90
COUNTRY = "France"
TYPE = "confirmed"


def format_forecast():
    forecast = {'ds': [], 'y': []}
    r = requests.get(url="https://pomber.github.io/covid19/timeseries.json")
    result = r.json()
    for res in result[COUNTRY]:
        forecast['ds'].append(res['date'])
        forecast['y'].append(res[TYPE])
    return pd.DataFrame.from_dict(forecast)


def forecast_figure():
    m = Prophet()
    m.fit(format_forecast())
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
                         label="AAJ",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1a",
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
    html.H1(children=f'{COUNTRY} confirmed forecast'),
    dcc.Graph(id='forecast-graph', figure=forecast_figure())
])

if __name__ == '__main__':
    app.run_server(debug=True)
