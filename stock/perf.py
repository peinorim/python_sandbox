from datetime import datetime, timedelta

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import yfinance as yf
import plotly.graph_objs as go
from dash_bootstrap_templates import load_figure_template

load_figure_template("darkly")


def download_data(tickers, start, end):
    data = yf.download(tickers, start=start, end=end)
    return data['Close']


def calculate_portfolio_performance(stocks: dict = None, start_date: str = None, end_date: str = None):
    # Télécharger les données
    data = download_data(list(stocks.keys()), start_date, end_date)
    # Calculer les rendements journaliers
    returns = data.pct_change().dropna()
    # Définir les poids du portefeuille
    weights = list(stocks.values())
    # Calculer les rendements du portefeuille
    portfolio_returns = returns.dot(weights)
    # Calculer la valeur cumulée du portefeuille en démarrant à 100
    return 100 * (1 + portfolio_returns).cumprod()


# Définir les tickers pour les actions et l'or
sp500 = {
    'CSPX.AS': 1,
}
msci_world = {
    'CW8.PA': 1,
}
nasdaq = {
    'CNDX.AS': 1,
}
emu = {
    'MFEC.PA': 1,
}
idl = {
    'GOLD.MI': 0.25,
    'JPYEUR=X': 0.25,
    'NRGW.PA': 0.25,
    'AASI.PA': 0.25,
}
valinor = {
    'CSPX.AS': 0.40,
    'ACA.PA': 0.25,
    'IEMA.AS': 0.1,
    'GOLD.MI': 0.25,
}

dad = {
    'GOLD.MI': 0.25,
    "CSW.PA": 0.15,
    "WINC.DE": 0.1,
    "GLDV.MI": 0.1,
    "XGSD.DE": 0.15,
    "EEI.MI": 0.15,
    "EMHD.PA": 0.1,
}

# Définir la période d'analyse
start_date = '2025-01-01'
end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

valinor_value = calculate_portfolio_performance(stocks=valinor, start_date=start_date, end_date=end_date)
sp500_value = calculate_portfolio_performance(stocks=sp500, start_date=start_date, end_date=end_date)
msci_world_value = calculate_portfolio_performance(stocks=msci_world, start_date=start_date, end_date=end_date)
nasdaq_value = calculate_portfolio_performance(stocks=nasdaq, start_date=start_date, end_date=end_date)
emu_value = calculate_portfolio_performance(stocks=emu, start_date=start_date, end_date=end_date)
idl_value = calculate_portfolio_performance(stocks=idl, start_date=start_date, end_date=end_date)
dad_value = calculate_portfolio_performance(stocks=dad, start_date=start_date, end_date=end_date)

app = dash.Dash(external_stylesheets=[dbc.themes.DARKLY])
app.layout = dbc.Container([
    dbc.Row([
        html.Div(className="col-md-2"),
        html.Div([dcc.Graph(
            id='performance-graph',
            figure={
                'data': [
                    go.Scatter(
                        x=valinor_value.index,
                        y=valinor_value,
                        mode='lines',
                        name='Valinor'
                    ),
                    go.Scatter(
                        x=sp500_value.index,
                        y=sp500_value,
                        mode='lines',
                        name='S&P 500'
                    ),
                    go.Scatter(
                        x=msci_world_value.index,
                        y=msci_world_value,
                        mode='lines',
                        name='World'
                    ),
                    go.Scatter(
                        x=nasdaq_value.index,
                        y=nasdaq_value,
                        mode='lines',
                        name='NASDAQ'
                    ),
                    go.Scatter(
                        x=emu_value.index,
                        y=emu_value,
                        mode='lines',
                        name='EMU'
                    ),
                    go.Scatter(
                        x=idl_value.index,
                        y=idl_value,
                        mode='lines',
                        name='IDL'
                    ),
                    go.Scatter(
                        x=dad_value.index,
                        y=dad_value,
                        mode='lines',
                        name='Dad'
                    )
                ],
                'layout': go.Layout(
                    title='Valinor Performance',
                    xaxis={'title': 'Date'},
                    yaxis={'title': 'Cumulative Returns'},
                    legend={'x': 0, 'y': 1},
                    template='darkly',
                    hovermode='closest'
                )
            }
        )], className="col-md-8"),
        html.Div(className="col-md-2"),
    ])
], fluid=True)

if __name__ == '__main__':
    app.run(debug=True)
