from datetime import datetime
from math import inf

import pandas as pd
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import plotly.graph_objects as go

DATE_FORMAT = "%Y-%m-%d"


class FinanceApi:

    def get_stock_data(self, symbol: str = None, start_date: str = None):
        try:
            forecast = {'ds': [], 'y': []}
            data = yf.download(symbol, start=start_date, end=datetime.now().strftime("%Y-%m-%d"))
            forecast['ds'] = data.index.tz_localize(None).tolist()
            forecast['y'] = data.Close.tolist()
            return pd.DataFrame.from_dict(forecast)
        except Exception as err:
            print(err)
            raise err

    def forecast_figure(self, symbol=None, start_date=None, periods=None):
        m = Prophet()
        m.fit(self.get_stock_data(symbol=symbol, start_date=start_date))
        future = m.make_future_dataframe(periods=periods)
        forecast = m.predict(future)

        forecast_fig = plot_plotly(m, forecast, uncertainty=True, plot_cap=True, trend=False, changepoints=True)

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


if __name__ == "__main__":
    api = FinanceApi()
    symbol = "SP5C.PA"
    start_date = "2020-01-01"

    data = FinanceApi().get_stock_data(symbol=symbol, start_date=start_date)
