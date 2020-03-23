from datetime import datetime

import plotly.graph_objects as go
import dash

app = dash.Dash(__name__)


class Timeline:

    def __init__(self, data=None, countries=None, type=None):

        self.type = type
        self.countries = countries
        self.data = data

    def get_figure(self):
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
                    data['dates'].append(datetime.strptime(day['date'], '%Y-%m-%d'))
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
            # paper_bgcolor="#2B3E50",
            # plot_bgcolor="rgba(1.0, 1.0, 1.0, 0.1)",
            title=f"{graph_title} cases",
            # titlefont={"color": "#FFF"},
            xaxis=go.layout.XAxis(
                # tickfont={"color": "#FFF"},
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
            yaxis=dict(
                showgrid=True,
                # tickfont={"color": "#FFF"},
            ),
        )
        return fig
