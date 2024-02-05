import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from stock.finance import StockAPI, FearGreed

# https://dash.plotly.com/dash-core-components/graph
# https://bootswatch.com/darkly/
# https://dash-bootstrap-components.opensource.faculty.ai/docs/components/
# https://edition.cnn.com/markets/fear-and-greed


app = dash.Dash(external_stylesheets=[dbc.themes.DARKLY])
START_DATE = "2020-01-01"
PERIODS = 90
SYMBOLS = [
    "ACA.PA",
    "AC.PA"
    "AI.PA",
    "BN.PA",
    "RI.PA",
    "SU.PA",
    "SW.PA",
    "TTE.PA",
    "SP5C.PA"
]
stocks = []

for symbol in SYMBOLS:
    api = StockAPI()
    figure = StockAPI().forecast_figure(symbol=symbol, start_date=START_DATE, periods=PERIODS)

    stocks.append(
        html.Div(children=[
            dcc.Graph(id=f'forecast-{symbol.lower()}', figure=figure)
        ], className='col-md-6')
    )

fear_greed = FearGreed(start_date=START_DATE)

fear_greed_gauge = html.Div([
    go.Figure(go.Indicator(
        mode="gauge+number",
        value=fear_greed.fear_and_greed_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': fear_greed.fear_and_greed_rating},
        gauge={'axis': {'range': [None, 100]}}
    )),
], className="col-md-6")

fear_and_greed_previous = html.Div([
    html.H4(["previous_close", dbc.Badge(fear_greed.fear_and_greed_previous_close, className="ms-1")]),
    html.H4(["previous_1_week", dbc.Badge(fear_greed.fear_and_greed_previous_1_week, className="ms-1")]),
    html.H4(["previous_1_month", dbc.Badge(fear_greed.fear_and_greed_previous_1_month, className="ms-1")]),
    html.H4(["previous_1_year", dbc.Badge(fear_greed.fear_and_greed_previous_1_year, className="ms-1")]),

], className="col-md-6")

app.layout = dbc.Container([
    stocks,
    fear_greed_gauge,
    fear_and_greed_previous
], fluid=True)

if __name__ == '__main__':
    app.run_server(debug=True)
