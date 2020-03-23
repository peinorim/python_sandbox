import locale
from datetime import datetime

import dash
import dash_html_components as html
import dash_core_components as dcc

import dash_bootstrap_components as dbc
import requests

from divoc.forecast import Forecast
from divoc.map import Map
from divoc.timeline import Timeline

external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, assets_external_path='assets')
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

TYPE = 'confirmed'
r = requests.get(url="https://pomber.github.io/covid19/timeseries.json")
data = r.json()
data = dict(sorted(data.items()))
countries = []
types = [
    {'label': "Confirmed", 'value': "confirmed"},
    {'label': "Deaths", 'value': "deaths"},
    {'label': "Recovered", 'value': "recovered"},
]
confirmed_tot = 0
deaths_tot = 0
recovered_tot = 0
last_date = None

for country in data:
    countries.append({'label': country, 'value': country})
    confirmed_tot += data[country][-1].get('confirmed')
    deaths_tot += data[country][-1].get('deaths')
    recovered_tot += data[country][-1].get('recovered')
    last_date = datetime.strptime(data[country][-1].get('date'), '%Y-%m-%d')

timeline_all = Timeline(data=data, countries=[], type="confirmed")
timeline_one = Timeline(data=data, countries=["France"])
forecast = Forecast(data=data, country="France", type="confirmed")
map = Map(data=data, type="confirmed")

app.layout = html.Div(children=[
    html.H1(f"COVID-19 Worldwide data", style={"textAlign": "center", "padding": "20px 0"}),

    html.Header([
        dbc.Row(
            [
                html.Div(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4('{0:n}'.format(confirmed_tot), className="card-title"),
                                html.H6("Confirmed cases", className="card-subtitle")
                            ]
                        )
                    ), className="col-md-4"
                ),
                html.Div(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4('{0:n}'.format(deaths_tot), className="card-title"),
                                html.H6("Deaths", className="card-subtitle")
                            ]
                        )
                    ), className="col-md-4"
                ),
                html.Div(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4('{0:n}'.format(recovered_tot), className="card-title"),
                                html.H6("Recovered", className="card-subtitle")
                            ]
                        )
                    ), className="col-md-4"
                )
            ], className="col-md-12", style={"paddingBottom": "20px"}
        ),
        html.Div([
            html.Div(
                dcc.Dropdown(
                    id='countries-dropdown',
                    options=countries,
                    multi=True,
                    placeholder="Select one or several countries",
                ), className="col-md-3"
            ),
            html.Div(
                dcc.Dropdown(
                    id='types-dropdown',
                    options=types,
                    multi=False,
                    value="Confirmed",
                    placeholder="Select a type of data",
                ), className="col-md-3"
            )
        ], className="col-md-12 row")
    ], className="row"),
    dbc.Row([
        html.Div([dcc.Graph(id='timeline-all-graph', figure=timeline_all.get_figure())], className="col-md-6"),
        html.Div([dcc.Graph(id='map-graph', figure=map.get_figure())], className="col-md-6"),
        html.Div(
            html.Div(
                dcc.Dropdown(
                    id='country-dropdown',
                    options=countries,
                    multi=False,
                    placeholder="Select one country",
                ), className="col-md-3"
            ), className="col-md-12 row"
        ),
        html.Div([dcc.Graph(id='timeline-one-graph', figure=timeline_one.get_figure())], className="col-md-6"),
        html.Div([dcc.Graph(id='forecast-graph', figure=forecast.get_figure())], className="col-md-6"),
    ]
    ),
    html.Footer([
        html.P(f"Last update on : {last_date:%Y-%m-%d}"),
        html.A("Data provided by pomber", href="https://github.com/pomber", target="_blank"),
    ], style={"textAlign": "center", "padding": "20px 0"})

], className="container-fluid")

if __name__ == '__main__':
    app.run_server(debug=True)
