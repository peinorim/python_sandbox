from datetime import datetime

import yfinance as yf
import matplotlib.pyplot as plt


def download_data(tickers, start, end):
    data = yf.download(tickers, start=start, end=end)
    return data['Adj Close']


def calculate_portfolio_performance(stock1, stock2, gold, start, end):
    # Télécharger les données
    data = download_data([stock1, stock2, gold], start, end)

    # Calculer les rendements journaliers
    returns = data.pct_change().dropna()

    # Définir les poids du portefeuille
    weights = [1/3, 1/3, 1/3]  # 2/3 d'actions et 1/3 d'or

    # Calculer les rendements du portefeuille
    portfolio_returns = returns.dot(weights)

    # Calculer la valeur cumulée du portefeuille
    portfolio_value = 100 * ((1 + portfolio_returns).cumprod())

    return portfolio_value


def calculate_sp500_performance(start, end):
    # Télécharger les données du S&P 500
    sp500_data = download_data('^GSPC', start, end)

    # Calculer les rendements journaliers
    sp500_returns = sp500_data.pct_change().dropna()

    # Calculer la valeur cumulée du S&P 500
    sp500_value = 100 * ((1 + sp500_returns).cumprod())

    return sp500_value


def plot_performance(portfolio_value, sp500_value):
    plt.figure(figsize=(10, 6))
    plt.plot(portfolio_value, label='Portfolio')
    plt.plot(sp500_value, label='S&P 500', linestyle='--')
    plt.title('Portfolio Performance vs S&P 500')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    # Définir les tickers pour les actions et l'or
    stock1 = 'CSPX.L'  # Exemple d'action 1
    stock2 = 'NDIA.L'  # Exemple d'action 2
    gold = 'GLDD.L'  # Ticker pour l'or (futures or)

    # Définir la période d'analyse
    start_date = '2024-01-01'
    end_date = datetime.today().strftime('%Y-%m-%d')

    # Calculer la performance du portefeuille
    portfolio_value = calculate_portfolio_performance(stock1, stock2, gold, start_date, end_date)

    # Calculer la performance du S&P 500
    sp500_value = calculate_sp500_performance(start_date, end_date)

    # Afficher la performance du portefeuille et du S&P 500
    plot_performance(portfolio_value, sp500_value)
