from datetime import datetime

import plotly.graph_objects as go
import dash

app = dash.Dash(__name__)


class Timeline:

    def __init__(self, data=None, countries=None, type=None):

        self.type = type
        self.countries = countries if countries else list()
        self.data = data

    def get_figure(self):
        fig = go.Figure()

        for res in self.data:
            if self.countries is None or res in self.countries or len(self.countries) == 0:
                data = {
                    "dates": [],
                    "confirmed": [],
                    "deaths": [],
                    "recovered": []
                }

                for index, day in enumerate(self.data[res]):
                    data['dates'].append(datetime.strptime(day['date'], '%m/%d/%y'))
                    data['confirmed'].append(day.get('confirmed'))
                    data['deaths'].append(day.get('deaths'))
                    if day.get('recovered') is None:
                        data['recovered'].append(self.data[res][index - 1].get('recovered'))
                    else:
                        data['recovered'].append(day.get('recovered'))

                if len(self.countries) != 1:
                    graph_title = self.type
                    fig.add_trace(go.Scatter(
                        x=data['dates'],
                        y=data[self.type],
                        name=res,
                        opacity=0.8))
                else:
                    graph_title = f'{self.countries[0]}'
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
            paper_bgcolor="#222",
            plot_bgcolor="#222",
            title=f"{graph_title} cases",
            titlefont={"color": "#c9c9c9"},
            font=dict(
                color="#c9c9c9"
            ),
            xaxis=go.layout.XAxis(
                range=[datetime.strptime("2020-02-23", '%Y-%m-%d'), datetime.now()],
                autorange=False,
                tickformat="%Y-%m-%d",
                gridcolor="#6F6F6F",
                linecolor='#6F6F6F',
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#6F6F6F",
                tickfont={"color": "#c9c9c9"},
                linecolor='#6F6F6F'
            ),
        )
        return fig
