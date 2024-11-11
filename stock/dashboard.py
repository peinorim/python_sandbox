from datetime import datetime, timedelta

import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import dash_daq as daq

from stock.finance import StockAPI, FearGreed
from stock.forecast import Forecast

# https://dash.plotly.com/dash-core-components/graph
# https://bootswatch.com/darkly/
# https://dash-bootstrap-components.opensource.faculty.ai/docs/components/
# https://edition.cnn.com/markets/fear-and-greed


app = dash.Dash(external_stylesheets=[dbc.themes.DARKLY])
START_DATE = "2020-01-01"
# START_DATE = (datetime.today() - timedelta(days=200)).strftime("%Y-%m-%d")
PERIODS = 90
SYMBOLS = [
    "ACA.PA",
    "AASI.PA",
    "NDIA.AS",
    "GC=F",
    "TSLA",
    "NVDA",
    "EURUSD=X",
    "BTC-USD"
]
stocks = []
forecast = Forecast()

for symbol in SYMBOLS:
    api = StockAPI()

    data = StockAPI().get_stock_data(symbol=symbol, start_date=START_DATE)
    figure = forecast.render_figure(symbol=symbol, data=data, periods=PERIODS)

    stocks.append(
        html.Div(children=[
            dcc.Graph(id=f'forecast-{symbol.lower()}', figure=figure)
        ], className='col-md-6')
    )

fear_greed = FearGreed(start_date=START_DATE)
market_momentum_sp500_data = fear_greed.format_indice_data(indice_name="market_momentum_sp500")
market_momentum_sp500_forecast = forecast.render_figure(symbol="S&P500", data=market_momentum_sp500_data,
                                                        periods=PERIODS)
stocks.append(
    html.Div(children=[
        dcc.Graph(id=f'forecast-sp500', figure=market_momentum_sp500_forecast)
    ], className='col-md-6')
)
vix_data = fear_greed.format_indice_data(indice_name="market_volatility_vix")
vix_forecast = forecast.render_figure(symbol="VIX", data=vix_data, periods=PERIODS)
stocks.append(
    html.Div(children=[
        dcc.Graph(id=f'forecast-vix', figure=vix_forecast)
    ], className='col-md-6')
)

fear_greed_gauge = html.Div([
    daq.Gauge(
        value=fear_greed.fear_and_greed_score,
        label=fear_greed.fear_and_greed_rating.upper(),
        max=100,
        min=0,
        showCurrentValue=True,
        color={"gradient": True, "ranges": {"red": [0, 25], "yellow": [25, 75], "green": [75, 100]}},
    )
], className="col-md-4")

fear_and_greed_previous = html.Div([
    html.H4(["Previous Close", dbc.Badge(fear_greed.fear_and_greed_previous_close, className="ms-1")]),
    html.H4(["Previous 1 week", dbc.Badge(fear_greed.fear_and_greed_previous_1_week, className="ms-1")]),
    html.H4(["Previous 1 month", dbc.Badge(fear_greed.fear_and_greed_previous_1_month, className="ms-1")]),
    html.H4(["Previous 1 year", dbc.Badge(fear_greed.fear_and_greed_previous_1_year, className="ms-1")]),
], className="col-md-4")

app.layout = dbc.Container([
    dbc.Row(
        [html.Div(className="col-md-4"), fear_greed_gauge, fear_and_greed_previous, html.Div(className="col-md-4")]
    ),
    dbc.Row(stocks),
], fluid=True)

if __name__ == '__main__':
    app.run_server(debug=True)
