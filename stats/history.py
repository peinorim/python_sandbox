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
            print("")
            for pick in draw.picked:
                if not self.blue_stats.get(pick):
                    self.blue_stats.update({
                        pick: {
                            'nb_out': 1,
                            'out_percents': [round((1 / index) * 100, 2)],
                            'out_dates': [draw.date.strftime("%d/%m/%Y")]
                        }
                    })
                else:
                    self.blue_stats[pick]['nb_out'] += 1
                    self.blue_stats[pick]['out_percents'].append(round((self.blue_stats[pick]['nb_out'] / index) * 100, 2))
                    self.blue_stats[pick]['out_dates'].append(draw.date.strftime("%m/%d/%Y"))

            if not self.red_stats.get(draw.luck):
                self.red_stats.update({
                    draw.luck: {
                        'nb_out': 1,
                        'out_percents': [round((1 / index) * 100, 2)],
                        'out_dates': [draw.date.strftime("%d/%m/%Y")]
                    }
                })
            else:
                self.red_stats[draw.luck]['nb_out'] += 1
                self.red_stats[draw.luck]['out_percents'].append(round((self.red_stats[draw.luck]['nb_out'] / index) * 100, 2))
                self.red_stats[draw.luck]['out_dates'].append(draw.date.strftime("%m/%d/%Y"))

            self.blue_stats = dict(sorted(self.blue_stats.items()))
            self.red_stats = dict(sorted(self.red_stats.items()))


if __name__ == '__main__':
    History()
