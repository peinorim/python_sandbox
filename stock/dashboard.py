import os
from os import getenv

import dash
from dash import html
from dash import dcc
import dash_daq as daq

from finance import StockAPI, FearGreed
from forecast import Forecast
from offline import render_html_index

to_html = os.getenv('OFFLINE', 'false') == 'true'
DARKLY = "https://cdn.jsdelivr.net/npm/bootswatch@5.3.8/dist/darkly/bootstrap.min.css"
app = dash.Dash(external_stylesheets=[DARKLY])

START_DATE = "2020-01-01"

PERIODS = 90
SYMBOLS = {
    'my': [
        "NVDA",
        "ACA.PA",
        "CSPX.AS",
        "CNDX.AS",
        "CW8.PA",
        "ACWI.PA",
        "CSW.PA",
        "STAW.MI",
        "AEME.PA",
        "CMSE.PA",
        "COMO.PA",
        "GOLD.MI",
        "^SPX",
        "^NDX",
        "GC=F",
        "CL=F",
        "EURUSD=X",
        "BTC-USD"
    ],
    'dad': [
        "XGSD.DE",
        "WINC.DE",
        "EMHD.PA",
        "TDIV.AS",
        "IQQ0.DE"
    ]
}

stocks = StockAPI().get_stock_figures(
    symbols=SYMBOLS.get('my'),
    start_date=START_DATE,
    periods=PERIODS,
    to_html=to_html
)
dad_stocks = StockAPI().get_stock_figures(
    symbols=SYMBOLS.get('dad'),
    start_date=START_DATE,
    periods=PERIODS,
    to_html=to_html
)

fear_greed = FearGreed(start_date=START_DATE)
vix_data = fear_greed.format_indice_data(indice_name="market_volatility_vix")
vix_forecast = Forecast().render_figure(symbol="VIX", data=vix_data, periods=PERIODS)

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
    html.H4(["Previous Close", html.Span(fear_greed.fear_and_greed_previous_close, className="ms-1 badge bg-secondary")]),
    html.H4(["Previous 1 week", html.Span(fear_greed.fear_and_greed_previous_1_week, className="ms-1 badge bg-secondary")]),
    html.H4(["Previous 1 month", html.Span(fear_greed.fear_and_greed_previous_1_month, className="ms-1 badge bg-secondary")]),
    html.H4(["Previous 1 year", html.Span(fear_greed.fear_and_greed_previous_1_year, className="ms-1 badge bg-secondary")]),
], className="col-md-4")

app.layout = html.Div([
    html.Div(
        [html.Div(className="col-md-4"), fear_greed_gauge, fear_and_greed_previous, html.Div(className="col-md-4")],
        className="row"
    ),
    html.Div(stocks, id="stocks", className="row"),
    html.Div(dad_stocks, id="dad-stocks", className="row"),
], className="container-fluid")

if __name__ == '__main__':

    if to_html:
        print("OFFLINE")
        with open("dashboard.html", "w", encoding="utf-8") as f:
            f.write(render_html_index(symbols=SYMBOLS.get('my') + SYMBOLS.get('dad')))
    else:
        app.run(debug=True if getenv("DEBUG") else False)
