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
from prophet import Prophet
from prophet.plot import plot_plotly
from requests import RequestException
import logging

cmdstanpy_logger = logging.getLogger("cmdstanpy")
cmdstanpy_logger.disabled = True

PERIODS = 5
MAX_DATE = "2022-11-21"
EU = False
GRAPHS = False


class Forecast:

    def format_forecast(self, dates=None, percents=None):
        forecast = {
            'ds': dates,
            'y': percents
        }

        return pd.DataFrame.from_dict(forecast)

    def get_forecast(self, dates=None, percents=None):
        m = Prophet()
        m.fit(self.format_forecast(dates=dates, percents=percents))
        future = m.make_future_dataframe(periods=PERIODS)
        future_values = list(m.predict(future).yhat.values)
        low_val = future_values[-PERIODS-1]
        high_val = future_values[-2]
        return [
            low_val,
            high_val,
            round(((high_val - low_val) / abs(low_val)) * 100, 2)
        ]

    def forecast_figure(self, dates=None, percents=None, title=None):
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
                title=f"{index} : {item.get('nb_out')} out, {item.get('current_percent')}%, last out on {item.get('last_out'):%Y-%m-%d}"
            ))
        return figures


class Draw:
    def __init__(self, date=None, one=None, two=None, three=None, four=None, five=None, luck=None):
        self.date = date
        self.picked = sorted([one, two, three, four, five])
        self.luck = sorted(luck) if isinstance(luck, list) else luck
        self.result = f'{"-".join(map(str, self.picked))}+{self.luck}'


class ZipToData:

    def zip_to_data(self, url=None, eu=False):
        if url:
            file_data = None
            file_name = 'fr.zip'
            encoding = 'utf-8'
            if eu:
                file_name = 'eu.zip'
                encoding = 'latin-1'

            try:
                response = requests.get(url, stream=True)
                print("###################################        ONLINE MODE       #######################################")
                z = zipfile.ZipFile(io.BytesIO(response.content))
                file_data = z.read(z.infolist()[0])
                self.__save_to_file(content=response.content, file_name=file_name)
                z.close()
            except RequestException:
                print("###################################        OFFLINE MODE       #######################################")
                archive = zipfile.ZipFile(file_name, 'r')
                file_data = archive.read(list(archive.NameToInfo.keys())[0])
                archive.close()
            except Exception as err:
                print(str(err))
            if file_data:
                return file_data.decode(encoding=encoding).splitlines()
        return {}

    def __save_to_file(self, content=None, file_name=None):
        if content and file_name:
            f = open(f"{os.getcwd()}/{file_name}", 'wb')
            f.write(content)
            f.close()


class History:
    draws = []
    blue_stats = {}
    red_stats = {}
    all_dates = []
    eu = False

    def __init__(self, eu=False, max_date=None):

        url = "https://media.fdj.fr/static-draws/csv/loto/loto_201911.zip"
        if eu:
            url = "https://media.fdj.fr/static-draws/csv/euromillions/euromillions_202002.zip"
        data = ZipToData().zip_to_data(url=url, eu=eu)
        self.eu = eu
        self.max_blue = 50 if not self.eu else 51
        self.max_red = 11 if not self.eu else 13

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
                    self.draws = sorted(self.draws, key=lambda x: x.date, reverse=False)
                    self.all_dates.append(draw_date)
                    self.all_dates.sort()
                    self.__set_stats(draw=draw)
            except ValueError:
                pass

    def __set_stats(self, draw=None):

        if draw and draw.date and draw.picked and draw.luck:
            for number in range(1, self.max_blue):
                if not self.blue_stats.get(number):
                    self.blue_stats.update({
                        number: {
                            'nb_out': 0,
                            'current_percent': 0,
                            'last_out': None,
                            'out_percents': [],
                            'out_dates': [],
                            'forecast': None,
                            'prediction': None,
                        }
                    })
                if number in draw.picked:
                    self.blue_stats[number]['nb_out'] += 1
                    self.blue_stats[number]['out_dates'].append(draw.date)

                self.blue_stats[number]['out_percents'].append(
                    round((self.blue_stats[number]['nb_out'] / len(self.draws)) * 100, 2)
                )
                self.blue_stats[number]['out_dates'].sort()
                self.blue_stats[number]['current_percent'] = self.blue_stats[number]['out_percents'][-1]
                self.blue_stats[number]['last_out'] = self.blue_stats[number]['out_dates'][-1] if \
                    self.blue_stats[number]['out_dates'] else None

            for number in range(1, self.max_red):
                if not self.red_stats.get(number):
                    self.red_stats.update({
                        number: {
                            'nb_out': 0,
                            'current_percent': 0,
                            'last_out': None,
                            'out_percents': [],
                            'out_dates': [],
                            'forecast': None,
                            'prediction': None,
                        }
                    })
                if isinstance(draw.luck, int) and number == draw.luck or \
                        isinstance(draw.luck, list) and number in draw.luck:
                    self.red_stats[number]['nb_out'] += 1
                    self.red_stats[number]['out_dates'].append(draw.date)

                self.red_stats[number]['out_percents'].append(
                    round((self.red_stats[number]['nb_out'] / len(self.draws)) * 100, 2)
                )
                self.red_stats[number]['out_dates'].sort()

                self.red_stats[number]['current_percent'] = self.red_stats[number]['out_percents'][-1]
                self.red_stats[number]['last_out'] = self.red_stats[number]['out_dates'][-1] if self.red_stats[number][
                    'out_dates'] else None

            self.blue_stats = dict(sorted(self.blue_stats.items()))
            self.red_stats = dict(sorted(self.red_stats.items()))

    def get_predictions(self):
        print(
            f"###################################        LAST {'EU' if self.eu else 'FR'} : {self.all_dates[-1]:%Y-%m-%d} : {self.draws[-1].result}       #######################################")
        print("###################################        BLUE        #######################################")
        for number in range(1, self.max_blue):
            self.blue_stats[number]['forecast'] = Forecast().get_forecast(
                dates=self.all_dates,
                percents=self.blue_stats.get(number).get('out_percents')
            )
            self.blue_stats[number]['prediction'] = self.blue_stats[number]['forecast'][-1]
            print(
                f"{number} - Last : {self.blue_stats[number]['last_out']:%Y-%m-%d} - {self.blue_stats[number]['current_percent']}% || {self.blue_stats[number]['forecast']}")
        print("###################################        RED        #######################################")
        for number in range(1, self.max_red):
            self.red_stats[number]['forecast'] = Forecast().get_forecast(
                dates=self.all_dates,
                percents=self.red_stats.get(number).get('out_percents')
            )
            self.red_stats[number]['prediction'] = self.red_stats[number]['forecast'][-1]
            print(
                f"{number} - Last : {self.red_stats[number]['last_out']:%Y-%m-%d} - {self.red_stats[number]['current_percent']}% || {self.red_stats[number]['forecast']}")


if __name__ == '__main__':

    max_date = datetime.strptime(MAX_DATE, '%Y-%m-%d')
    history = History(eu=EU, max_date=max_date)

    if GRAPHS:
        app = dash.Dash(__name__)
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
    else:
        history.get_predictions()
