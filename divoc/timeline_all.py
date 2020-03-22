import plotly.graph_objects as go
import dash
import dash_html_components as html
import dash_core_components as dcc
import requests

app = dash.Dash(__name__)

TYPE = 'confirmed'
COUNTRIES = ['France', 'China', 'Italy', 'United Kingdom', 'US', 'Germany', 'all']


def data_figure():
    r = requests.get(url="https://pomber.github.io/covid19/timeseries.json")
    result = r.json()
    result = dict(sorted(result.items()))
    fig = go.Figure()

    for res in result:
        if res in COUNTRIES or 'all' in COUNTRIES:
            data = {
                "dates": [],
                "confirmed": [],
                "deaths": [],
                "recovered": []
            }

            for day in result[res]:
                data['dates'].append(day['date'])
                data['confirmed'].append(day['confirmed'])
                data['deaths'].append(day['deaths'])
                data['recovered'].append(day['recovered'])

            fig.add_trace(go.Scatter(
                x=data['dates'],
                y=data[TYPE],
                name=res,
                opacity=0.8))

    # Use date string to set xaxis range
    fig['layout']['showlegend'] = True
    fig['layout']['height'] = 700

    fig.update_layout(
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


app.layout = html.Div(children=[
    html.H1(children=f'All countries {TYPE} cases'),
    dcc.Graph(id='timeline-graph', figure=data_figure())
])

if __name__ == '__main__':
    app.run_server(debug=True)
