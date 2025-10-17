from math import inf

from prophet import Prophet
from prophet.plot import plot_plotly
import plotly.graph_objects as go


class Forecast:

    def __init__(self):
        self.m = Prophet()

    def get_future_data(self, data: dict =None, periods: int = None):
        self.m.fit(data)
        future = self.m.make_future_dataframe(periods=periods)
        return self.m.predict(future)

    def render_figure(self, symbol: str = None, info: dict=None, data=None, periods=None):

        forecast = self.get_future_data(data=data, periods=periods)
        forecast_fig = plot_plotly(self.m, forecast, uncertainty=True, plot_cap=True, trend=False, changepoints=True)

        forecast_fig['layout']['showlegend'] = True
        forecast_fig['layout']['width'] = inf
        forecast_fig['layout']['title'] = f"{info.get('shortName').strip()} ({symbol}) 200MA : {info.get('twoHundredDayAverage')}".upper() if info else symbol.upper()

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
