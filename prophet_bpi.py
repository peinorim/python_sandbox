import dash
import dash_html_components as html
import dash_core_components as dcc
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
import pandas as pd
import requests
from datetime import datetime


def format_forecast():
    forecast = {'ds': [], 'y': []}
    PARAMS = {'start': '2010-07-17', 'end': datetime.now().strftime("%Y-%m-%d")}
    r = requests.get(url="http://api.coindesk.com/v1/bpi/historical/close.json", params=PARAMS)
    result = r.json()
    for res in result['bpi']:
        forecast['ds'].append(res)
        forecast['y'].append(result['bpi'][res])
    return {'forecast': forecast}


app = dash.Dash(__name__)

forecast = format_forecast()

df = pd.DataFrame.from_dict(forecast['forecast'])

m = Prophet()
m.fit(df)
future = m.make_future_dataframe(periods=365 * 2)
forecast = m.predict(future)

forecast_fig = plot_plotly(m, forecast, uncertainty=True, plot_cap=True, trend=True, changepoints=True,
                           changepoints_threshold=0.01)

forecast_fig['layout']['showlegend'] = True

app.layout = html.Div(children=[
    html.H1(children='BPI forecast'),
    dcc.Graph(id='forecast-graph', figure=forecast_fig)
])

if __name__ == '__main__':
    app.run_server(debug=True)
