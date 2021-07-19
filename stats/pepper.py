import csv
from datetime import datetime


class Pepper:
    heat = 0

    def __init__(self, num=None, nb_picked=None, occurence=None, last_sorted_date=None):
        self.num = int(num)
        self.nb_picked = int(nb_picked)
        self.occurence = float(occurence.replace(',', '.'))
        self.last_sorted_date = datetime.strptime(last_sorted_date, '%d/%m/%Y')


class PepperPot:
    peppers = []

    def __init__(self):
        self.__get_data()

    def __get_data(self):
        with open('stats.csv', newline='') as csvfile:
            datareader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in datareader:
                self.peppers.append(
                    Pepper(num=row[0], nb_picked=row[1], occurence=row[2], last_sorted_date=row[3])
                )
            csvfile.close()
        self.__generate_heat()

    def __generate_heat(self):
        if self.peppers:
            now = datetime.now()
            for pepper in self.peppers:
                last_picked = (now - pepper.last_sorted_date).days
                pepper.heat = round(pepper.occurence * last_picked, 2)

            self.__sort_by_heat()

    def open(self):
        now = datetime.now()
        print(f"Let's open our pepper pot on {now:%Y-%m-%d}.")
        for pepper in self.peppers:
            print(
                f"{pepper.num} heat is {pepper.heat} ({(now - pepper.last_sorted_date).days} days not seen, {pepper.occurence}% occured)."
            )
        print("End of pepper pot opening")

    def __sort_by_heat(self):
        self.peppers.sort(key=lambda x: x.heat, reverse=False)


if __name__ == '__main__':
    pot = PepperPot()
    pot.open()
