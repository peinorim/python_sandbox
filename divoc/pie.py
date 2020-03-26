from datetime import datetime

import dash

app = dash.Dash(__name__)
import plotly.graph_objects as go


class Pie:

    def __init__(self, data=None, country=None):
        self.type = type
        self.country = country
        self.data = data

    def get_figure(self):
        fig = go.Figure()
        labels = ['Recovered', 'Deaths', 'Others']
        values = []

        last_data_country = self.data[self.country][-1]
        recov = round((last_data_country['recovered'] / last_data_country['confirmed']) * 100, 1)
        deat = round((last_data_country['deaths'] / last_data_country['confirmed']) * 100, 1)
        values.append(recov)
        values.append(deat)
        values.append(100 - recov - deat)

        fig.add_trace(
            go.Pie(labels=labels, values=values, name="Recovered / deaths repartition")
        )
        fig.update_traces(hole=.4, hoverinfo="label+percent+name")
        fig['layout']['height'] = 700
        return fig
