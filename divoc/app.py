import locale
import os
from datetime import datetime

import dash
import dash_html_components as html
import dash_core_components as dcc

import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output

from divoc import Data
from divoc.forecast import Forecast
from divoc.map import Map
from divoc.pie import Pie
from divoc.timeline import Timeline

external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, assets_external_path='assets')
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

TYPE = 'confirmed'
data = Data().data

countries = []
types = [
    {'label': "Confirmed", 'value': "confirmed"},
    {'label': "Deaths", 'value': "deaths"},
    {'label': "Recovered", 'value': "recovered"},
]

tots = {
    'last_date': None,
    'confirmed': 0,
    'deaths': 0,
    'recovered': 0
}

for country in data:
    if len(data[country]) > 0:
        countries.append({'label': country, 'value': country})
        tots['confirmed'] += data[country][-1].get('confirmed', 0)
        tots['deaths'] += data[country][-1].get('deaths', 0)
        tots['recovered'] += data[country][-1].get('recovered', 0)
        tots['last_date'] = datetime.strptime(data[country][-1].get('date'), '%m/%d/%y')

timeline_all = Timeline(data=data, countries=[], type="confirmed")
timeline_one = Timeline(data=data, countries=["France"], type="confirmed")
forecast = Forecast(data=data, country="France", type="confirmed")
map = Map(data=data, type="confirmed", tots=tots)
pie = Pie(data=data, country="France")

hidden = ''
if os.environ.get('FORECAST', "0") != "1":
    hidden = 'hidden'

app.layout = html.Div(children=[
    html.H1(f"COVID-19 Worldwide data", style={"textAlign": "center", "padding": "10px 0"}),
    html.H6(f"Last update on : {tots['last_date']:%Y-%m-%d}", style={"textAlign": "center", "padding": "10px 0"}),
    html.Header([
        dbc.Row(
            [
                html.Div(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4('{0:n}'.format(tots['confirmed']), className="card-title"),
                                html.H6("Confirmed cases", className="card-subtitle")
                            ]
                        )
                    ), className="col-md-4"
                ),
                html.Div(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    f"{'{0:n}'.format(tots['deaths'])} ({round((tots['deaths'] / tots['confirmed']) * 100, 1)}%)",
                                    className="card-title"),
                                html.H6("Deaths", className="card-subtitle")
                            ]
                        )
                    ), className="col-md-4"
                ),
                html.Div(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    f"{'{0:n}'.format(tots['recovered'])} ({round((tots['recovered'] / tots['confirmed']) * 100, 1)}%)",
                                    className="card-title"),
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
                    clearable=False,
                    value="confirmed",
                    placeholder="Select a type of data",
                ), className="col-md-3"
            )
        ], className="col-md-12 row")
    ], className="row"),
    dbc.Row([
        html.Div([dcc.Graph(id='timeline-all-graph', figure={})], className="col-md-6"),
        html.Div([dcc.Graph(id='map-graph', figure={})], className="col-md-6"),
        html.Div(
            html.Div(
                dcc.Dropdown(
                    id='country-dropdown',
                    options=countries,
                    clearable=False,
                    value='France',
                    multi=False,
                    placeholder="Select one country",
                ), className="col-md-3"
            ), className="col-md-12 row"
        ),
        html.Div([dcc.Graph(id='timeline-one-graph', figure={})], className="col-md-6"),
        html.Div([dcc.Graph(id='pie-one-graph', figure={})], className="col-md-6"),
        html.Div([dcc.Graph(id='forecast-graph', figure={})], className=f"col-md-12 {hidden}"),
    ]
    ),
    html.Footer([
        html.A("Data provided by CSSEGISandData", href="https://github.com/CSSEGISandData/COVID-19", target="_blank"),
    ], style={"textAlign": "center", "padding": "20px 0"})

], className="container-fluid")


@app.callback([
    Output(component_id='timeline-all-graph', component_property='figure'),
    Output(component_id='map-graph', component_property='figure')
],
    [
        Input(component_id='countries-dropdown', component_property='value'),
        Input(component_id='types-dropdown', component_property='value'),
    ]
)
def update_countries(countries, type):
    timeline_all = Timeline(data=data, countries=countries, type=type)
    map = Map(data=data, type=type, tots=tots)

    return timeline_all.get_figure(), map.get_figure()


@app.callback([
    Output(component_id='timeline-one-graph', component_property='figure'),
    Output(component_id='forecast-graph', component_property='figure'),
    Output(component_id='pie-one-graph', component_property='figure'),
],
    [
        Input(component_id='country-dropdown', component_property='value'),
        Input(component_id='types-dropdown', component_property='value'),
    ]
)
def update_country(country, type):
    timeline_one = Timeline(data=data, countries=[country], type=type)
    forecast = Forecast(data=data, country=country, type=type)
    pie = Pie(data=data, country=country)

    return timeline_one.get_figure(), forecast.get_figure(), pie.get_figure()


if __name__ == '__main__':
    app.run_server(debug=True)
