import os
from math import inf
import pandas as pd
import plotly.graph_objects as go

PERIODS = 30


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
        if os.environ.get('FORECAST', "0") != "1":
            return {}
        from fbprophet import Prophet
        from fbprophet.plot import plot_plotly

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
            paper_bgcolor="#222",
            plot_bgcolor="#222",
            font=dict(
                color="#c9c9c9"
            ),
            titlefont={"color": "#c9c9c9"},
            title=f"{self.country} {self.type} cases trend forecast for the next {PERIODS} days",
            xaxis=go.layout.XAxis(
                tickformat="%Y-%m-%d",
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            ),
            yaxis=dict(showgrid=True),
        )
        return forecast_fig
