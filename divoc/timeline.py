import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import requests

app = dash.Dash(__name__)


class Timeline:

    def __init__(self, data=None, countries=None, type=None):

        self.type = type
        self.countries = countries
        self.data = data

    def data_figure(self):
        fig = go.Figure()

        for res in self.data:
            if res in self.countries or len(self.countries) == 0:
                data = {
                    "dates": [],
                    "confirmed": [],
                    "deaths": [],
                    "recovered": []
                }

                for day in self.data[res]:
                    data['dates'].append(day['date'])
                    data['confirmed'].append(day['confirmed'])
                    data['deaths'].append(day['deaths'])
                    data['recovered'].append(day['recovered'])

                if len(self.countries) > 1 or len(self.countries) == 0:
                    graph_title = self.type
                    fig.add_trace(go.Scatter(
                        x=data['dates'],
                        y=data[self.type],
                        name=res,
                        opacity=0.8))
                else:
                    graph_title = self.countries[0]
                    fig.add_trace(go.Scatter(
                        x=data['dates'],
                        y=data['confirmed'],
                        name="confirmed",
                        opacity=0.8))

                    fig.add_trace(go.Scatter(
                        x=data['dates'],
                        y=data['deaths'],
                        name="deaths",
                        opacity=0.8))

                    fig.add_trace(go.Scatter(
                        x=data['dates'],
                        y=data['recovered'],
                        name="recovered",
                        opacity=0.8))

        # Use date string to set xaxis range
        fig['layout']['showlegend'] = True
        fig['layout']['height'] = 700

        fig.update_layout(
            title=f"{graph_title} cases",
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
                             label="AAJ",
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
        return fig
