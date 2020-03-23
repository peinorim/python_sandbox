import json

import plotly.graph_objects as go


class Map:

    def __init__(self, data=None, type=None):
        self.type = type
        self.data = data
        with open("countries.geo.json") as response:
            self.geojson = json.load(response)

    def get_figure(self):
        locations = []
        count_by_locations = []

        for res in self.data:
            locations.append(res)
            count_by_locations.append(self.data[res][-1].get(self.type))

        zmin = min(count_by_locations) if len(count_by_locations) > 0 else None
        zmax = max(count_by_locations) if len(count_by_locations) > 0 else None

        fig = go.Figure(go.Choroplethmapbox(geojson=self.geojson, locations=locations, z=count_by_locations,
                                            colorscale="reds", zmin=zmin, zmax=zmax,
                                            marker_opacity=1, marker_line_width=0.2))
        fig.update_layout(
            title=f'World {self.type} cases map',
            mapbox_style="carto-positron",
            mapbox_center={"lat": 46.625708, "lon": 2.460577},
            height=700,
            mapbox_zoom=1
        )

        return fig
