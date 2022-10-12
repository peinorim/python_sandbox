import csv
import io
import os
import zipfile
from datetime import datetime
import dash
import requests
from dash import html
from dash import dcc
from math import inf
import pandas as pd
import plotly.graph_objects as go

app = dash.Dash(__name__)
PERIODS = 1


class Forecast:

    def format_forecast(self, dates=None, percents=None):
        forecast = {
            'ds': dates,
            'y': percents
        }

        return pd.DataFrame.from_dict(forecast)

    def forecast_figure(self, dates=None, percents=None, title=None):
        from fbprophet import Prophet
        from fbprophet.plot import plot_plotly
        m = Prophet()
        m.fit(self.format_forecast(dates=dates, percents=percents))
        future = m.make_future_dataframe(periods=PERIODS)
        forecast = m.predict(future)

        forecast_fig = plot_plotly(m, forecast, uncertainty=True, plot_cap=True, trend=False, changepoints=True)

        forecast_fig['layout']['showlegend'] = True
        forecast_fig['layout']['width'] = inf
        forecast_fig['layout'].title.text = title

        forecast_fig.update_layout(
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
                             label="YTD",
                             step="year",
                             stepmode="todate"),
                        dict(count=1,
                             label="1y",
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
        return forecast_fig

    def generate_figure(self, dates=None, percents=None, title=None):
        return dcc.Graph(figure=self.forecast_figure(dates=dates, percents=percents, title=title))

    def get_figures(self, dates=None, stats=None):
        figures = []
        for index, item in stats.items():
            print(f"############################################################################################")
            print(f"###################################        {index}        #######################################")
            print(f"############################################################################################")
            figures.append(self.generate_figure(
                dates=dates,
                percents=stats.get(index).get('out_percents'),
                title=f"{index} : {item.get('nb_out')} out, {item.get('current_percent')}%, last out on {item.get('last_out')}"
            ))
        return figures


class Draw:
    def __init__(self, date=None, one=None, two=None, three=None, four=None, five=None, luck=None):
        self.date = date
        self.picked = sorted([one, two, three, four, five])
        self.luck = sorted(luck) if isinstance(luck, list) else luck
        self.result = f'{"-".join(map(str, self.picked))}+{self.luck}'


class History:
    draws = []
    blue_stats = {}
    red_stats = {}
    all_dates = []
    eu = False

    def __init__(self, eu=False, max_date=None):

        url = "https://media.fdj.fr/static/csv/loto/loto_201911.zip"
        if eu:
            url = "https://media.fdj.fr/static/csv/euromillions/euromillions_202002.zip"
        response = requests.get(url, stream=True)
        z = zipfile.ZipFile(io.BytesIO(response.content))
        foo2 = z.read(z.infolist()[0])
        data = foo2.decode('utf-8' if not eu else 'latin-1').splitlines()
        self.eu = eu

        if not max_date:
            max_date = datetime.now()

        for index, line in enumerate(data):
            try:
                row = line.split(';')
                draw_date = datetime.strptime(row[2], '%d/%m/%Y')
                if draw_date <= max_date:
                    if self.eu:
                        draw = Draw(
                            date=draw_date,
                            one=int(row[5]),
                            two=int(row[6]),
                            three=int(row[7]),
                            four=int(row[8]),
                            five=int(row[9]),
                            luck=[int(row[10]), int(row[11])]
                        )
                    else:
                        draw = Draw(
                            date=draw_date,
                            one=int(row[4]),
                            two=int(row[5]),
                            three=int(row[6]),
                            four=int(row[7]),
                            five=int(row[8]),
                            luck=int(row[9])
                        )

                    self.draws.append(draw)
                    self.all_dates.append(draw_date)
                    self.__set_stats(draw=draw, index=index)
            except ValueError:
                pass

    def __set_stats(self, draw=None, index=None):
        max_blue = 50 if not self.eu else 51
        if draw and draw.date and draw.picked and draw.luck:
            for number in range(1, max_blue):
                if not self.blue_stats.get(number):
                    self.blue_stats.update({
                        number: {
                            'nb_out': 0,
                            'current_percent': 0,
                            'last_out': None,
                            'out_percents': [],
                            'out_dates': []
                        }
                    })
                if number in draw.picked:
                    self.blue_stats[number]['nb_out'] += 1
                    self.blue_stats[number]['out_dates'].append(draw.date.strftime("%d/%m/%Y"))

                self.blue_stats[number]['out_percents'].append(
                    round((self.blue_stats[number]['nb_out'] / index) * 100, 2)
                )
                self.blue_stats[number]['current_percent'] = self.blue_stats[number]['out_percents'][-1]
                self.blue_stats[number]['last_out'] = self.blue_stats[number]['out_dates'][-1] if self.blue_stats[number]['out_dates'] else None

            max_red = 11 if not self.eu else 13
            for number in range(1, max_red):
                if not self.red_stats.get(number):
                    self.red_stats.update({
                        number: {
                            'nb_out': 0,
                            'current_percent': 0,
                            'last_out': None,
                            'out_percents': [],
                            'out_dates': []
                        }
                    })
                if isinstance(draw.luck, int) and number == draw.luck or \
                        isinstance(draw.luck, list) and number in draw.luck:
                    self.red_stats[number]['nb_out'] += 1
                    self.red_stats[number]['out_dates'].append(draw.date.strftime("%d/%m/%Y"))

                self.red_stats[number]['out_percents'].append(
                    round((self.red_stats[number]['nb_out'] / index) * 100, 2)
                )
                self.red_stats[number]['current_percent'] = self.red_stats[number]['out_percents'][-1]
                self.red_stats[number]['last_out'] = self.red_stats[number]['out_dates'][-1] if self.red_stats[number]['out_dates'] else None

            self.blue_stats = dict(sorted(self.blue_stats.items()))
            self.red_stats = dict(sorted(self.red_stats.items()))


if __name__ == '__main__':
    MAX_DATE = "2022-10-12"
    EU = True
    max_date = datetime.strptime(MAX_DATE, '%Y-%m-%d')
    history = History(eu=EU, max_date=max_date)

    if os.name != 'nt':
        blue_figures = Forecast().get_figures(dates=history.all_dates, stats=history.blue_stats)
        red_figures = Forecast().get_figures(dates=history.all_dates, stats=history.red_stats)

        app.layout = html.Div(children=[
            html.H2(f'Last draw on : {history.all_dates[-1]:%Y-%m-%d}'),
            html.H2('Blue'),
            html.Div(children=blue_figures),
            html.H2('Red'),
            html.Div(children=red_figures)
        ])
        app.run_server(debug=False)
