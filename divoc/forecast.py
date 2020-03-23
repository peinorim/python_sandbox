from math import inf

from fbprophet import Prophet
from fbprophet.plot import plot_plotly
import pandas as pd
import plotly.graph_objects as go

PERIODS = 90


class Forecast:

    def __init__(self, data=None, country=None, type=None):
        self.type = type
        self.country = country
        self.data = data

    def format_forecast(self):
        forecast = {'ds': [], 'y': []}
        for res in self.data:
            if res == self.country:
                for day in self.data[res]:
                    forecast['ds'].append(day['date'])
                    forecast['y'].append(day[self.type])
        return pd.DataFrame.from_dict(forecast)

    def get_figure(self):
        m = Prophet()
        m.fit(self.format_forecast())
        future = m.make_future_dataframe(periods=PERIODS)
        forecast = m.predict(future)

        forecast_fig = plot_plotly(m, forecast, uncertainty=True, plot_cap=True, trend=True, changepoints=True,
                                   changepoints_threshold=0.01)

        forecast_fig['layout']['showlegend'] = True
        forecast_fig['layout']['width'] = inf
        forecast_fig['layout']['height'] = 700

        forecast_fig.update_layout(
            title=f"{self.country} {self.type} cases trend forecast for the next 90 days",
            xaxis=go.layout.XAxis(
                tickformat="%Y-%m-%d",
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
