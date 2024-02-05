import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

from stock.finance import FinanceApi

# https://dash.plotly.com/dash-core-components/graph
# https://bootswatch.com/darkly/
# https://dash-bootstrap-components.opensource.faculty.ai/docs/components/


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
    api = FinanceApi()
    figure = FinanceApi().forecast_figure(symbol=symbol, start_date=START_DATE, periods=PERIODS)

    stocks.append(
        html.Div(children=[
            dcc.Graph(id=f'forecast-{symbol.lower()}', figure=figure)
        ], className='col-md-6')
    )

app.layout = dbc.Container(stocks, fluid=True)

if __name__ == '__main__':
    app.run_server(debug=True)
