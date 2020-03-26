from datetime import datetime

import pandas as pd


class Data:
    data = {}

    def __init__(self):
        self.init_data()

    def init_data(self):
        df_conf = pd.read_csv(
            'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')

        for index, line in enumerate(df_conf.values):
            country = line[1]
            lat = line[2]
            long = line[3]
            if pd.notnull(line[0]):
                country = line[0]
            self.data.update({country: []})

            for i in range(4, len(df_conf.columns.values)):
                col = df_conf.columns.values[i]
                val = int(line[i])
                self.data[country].append({'date': col, 'confirmed': val, 'lat': lat, 'long': long})

        df_deat = pd.read_csv(
            'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')

        for index, line in enumerate(df_deat.values):
            country = line[1]
            if pd.notnull(line[0]):
                country = line[0]
            if country not in self.data:
                self.data.update({country: []})

            for i in range(4, len(df_deat.columns.values)):
                val = int(line[i]) if pd.notnull(line[i]) else None
                self.data[country][i - 4].update({'deaths': val})

        df_recov = pd.read_csv(
            'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv')

        for index, line in enumerate(df_recov.values):
            country = line[1]
            if pd.notnull(line[0]):
                country = line[0]
            if country not in self.data:
                self.data.update({country: []})

            for i in range(4, len(df_recov.columns.values) + 1):
                if i == len(line):
                    val = int(line[i - 1]) if pd.notnull(line[i - 1]) else None
                else:
                    val = int(line[i]) if pd.notnull(line[i]) else None
                if len(self.data[country]) > 0:
                    self.data[country][i - 4].update({'recovered': val})

        self.data = dict(sorted(self.data.items()))
