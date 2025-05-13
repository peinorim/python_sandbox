from datetime import datetime, timedelta

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import yfinance as yf
import plotly.graph_objs as go


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


def calculate_sp500_performance(start, end):
    # Télécharger les données du S&P 500
    sp500_data = download_data('^GSPC', start, end)
    # Calculer les rendements journaliers
    sp500_returns = sp500_data.pct_change().dropna()
    # Calculer la valeur cumulée du S&P 500 en démarrant à 100
    return 100 * (1 + sp500_returns).cumprod()


# Définir les tickers pour les actions et l'or
stocks = {
    'CSPX.L': 0.7,
    'GLDD.L': 0.3,
}

# Définir la période d'analyse
start_date = '2024-01-01'
end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

portfolio_value = calculate_portfolio_performance(stocks=stocks, start_date=start_date, end_date=end_date)
sp500_value = calculate_sp500_performance(start_date, end_date)

app = dash.Dash(external_stylesheets=[dbc.themes.DARKLY])
app.layout = dbc.Container([
    dbc.Row([
        html.Div(className="col-md-2"),
        html.Div([dcc.Graph(
            id='performance-graph',
            figure={
                'data': [
                    go.Scatter(
                        x=portfolio_value.index,
                        y=portfolio_value,
                        mode='lines',
                        name='Portfolio'
                    ),
                    go.Scatter(
                        x=sp500_value.index,
                        y=sp500_value,
                        mode='lines',
                        name='S&P 500'
                    )
                ],
                'layout': go.Layout(
                    title='Valinor Fund Performance vs S&P 500',
                    xaxis={'title': 'Date'},
                    yaxis={'title': 'Cumulative Returns'},
                    legend={'x': 0, 'y': 1},
                    hovermode='closest'
                )
            }
        )], className="col-md-8"),
        html.Div(className="col-md-2"),
    ])
], fluid=True)

if __name__ == '__main__':
    app.run_server(debug=True)
