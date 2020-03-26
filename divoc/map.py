import plotly.graph_objects as go


class Map:

    def __init__(self, data=None, type=None, tots=None):
        self.type = type
        self.data = data
        self.tots = tots

    def get_figure(self):
        fig = go.Figure()

        for country in self.data:
            if self.data[country] and self.data[country][-1][self.type] and self.data[country][-1].get('long') and \
                    self.data[country][-1].get('lat'):
                fig.add_trace(go.Scattergeo(
                    lon=[self.data[country][-1]['long']],
                    lat=[self.data[country][-1]['lat']],
                    text=f'{country} : {self.data[country][-1][self.type]} cases',
                    marker=dict(
                        size=round(self.data[country][-1][self.type] / (self.tots[self.type] / 400), 0),
                        line_color='rgb(40,40,40)',
                        line_width=0.5,
                        sizemode='area'
                    ),
                    name=country
                ))
        fig.update_layout(
            title=f'World {self.type} cases map',
            height=700,
            showlegend=False,
            geo=dict(
                scope='world',
                landcolor='rgb(217, 217, 217)',
            )
        )

        return fig
