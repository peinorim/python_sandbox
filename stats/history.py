import csv
from datetime import datetime


class Draw:
    def __init__(self, date=None, one=None, two=None, three=None, four=None, five=None, luck=None):
        self.date = date
        self.picked = sorted([one, two, three, four, five])
        self.luck = luck
        self.result = f'{"-".join(map(str, self.picked))}+{self.luck}'


class History:
    draws = []
    blue_stats = {}
    red_stats = {}

    def __init__(self):
        with open('history.csv', newline='') as csvfile:
            datareader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for index, row in enumerate(datareader):
                try:
                    draw = Draw(date=datetime.strptime(row[2], '%d/%m/%Y'), one=int(row[4]), two=int(row[5]), three=int(row[6]), four=int(row[7]), five=int(row[8]), luck=int(row[9]))
                    self.draws.append(draw)
                    self.__set_stats(draw=draw, index=index)
                except ValueError:
                    pass
            csvfile.close()
        print("")

    def __set_stats(self, draw=None, index=None):
        if draw and draw.date and draw.picked and draw.luck:
            for number in range(1, 50):
                if not self.blue_stats.get(number):
                    self.blue_stats.update({
                        number: {
                            'nb_out': 0,
                            'out_percents': [],
                            'out_dates': []
                        }
                    })
                if number in draw.picked:
                    self.blue_stats[number]['nb_out'] += 1
                    self.blue_stats[number]['out_dates'].append(draw.date.strftime("%d/%m/%Y"))

                self.blue_stats[number]['out_percents'].append(round((self.blue_stats[number]['nb_out'] / index) * 100, 2))

            for number in range(1, 11):
                if not self.red_stats.get(number):
                    self.red_stats.update({
                        number: {
                            'nb_out': 0,
                            'out_percents': [],
                            'out_dates': []
                        }
                    })
                if number == draw.luck:
                    self.red_stats[number]['nb_out'] += 1
                    self.red_stats[number]['out_dates'].append(draw.date.strftime("%d/%m/%Y"))
                self.red_stats[number]['out_percents'].append(round((self.red_stats[number]['nb_out'] / index) * 100, 2))

            self.blue_stats = dict(sorted(self.blue_stats.items()))
            self.red_stats = dict(sorted(self.red_stats.items()))


if __name__ == '__main__':
    History()
