import plotly.graph_objects as go
import dash
import dash_html_components as html
import dash_core_components as dcc
import requests

app = dash.Dash(__name__)

COUNTRY = "France"

data = {
    "dates": [],
    "confirmed": [],
    "deaths": [],
    "recovered": []
}


def data_figure():
    r = requests.get(url="https://pomber.github.io/covid19/timeseries.json")
    result = r.json()
    for res in result[COUNTRY]:
        data['dates'].append(res['date'])
        data['confirmed'].append(res['confirmed'])
        data['deaths'].append(res['deaths'])
        data['recovered'].append(res['recovered'])

    fig = go.Figure()
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

    fig.update_layout(
        xaxis=go.layout.XAxis(
            title_text=COUNTRY,
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
    html.H1(children=f'{COUNTRY} timeline'),
    dcc.Graph(id='timeline-graph', figure=data_figure())
])

if __name__ == '__main__':
    app.run_server(debug=True)
