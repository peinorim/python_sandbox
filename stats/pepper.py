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
    blue_peppers = []
    red_peppers = []
    now = datetime.now()

    def __init__(self):
        self.__get_blue_data()
        self.__get_red_data()
        self.__generate_heat()

    def __get_blue_data(self):
        with open('blue.csv', newline='') as csvfile:
            datareader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in datareader:
                self.blue_peppers.append(
                    Pepper(num=row[0], nb_picked=row[1], occurence=row[2], last_sorted_date=row[3])
                )
            csvfile.close()

    def __get_red_data(self):
        with open('red.csv', newline='') as csvfile:
            datareader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in datareader:
                self.red_peppers.append(
                    Pepper(num=row[0], nb_picked=row[1], occurence=row[2], last_sorted_date=row[3])
                )
            csvfile.close()

    def __generate_heat(self):

        if self.blue_peppers:
            for pepper in self.blue_peppers:
                last_picked = (self.now - pepper.last_sorted_date).days
                pepper.heat = round(pepper.occurence * last_picked, 2)
        if self.red_peppers:
            for pepper in self.red_peppers:
                last_picked = (self.now - pepper.last_sorted_date).days
                pepper.heat = round(pepper.occurence * last_picked, 2)
        self.__sort_by_heat()

    def open(self):
        print(f"Let's open our pepper pot on {self.now:%Y-%m-%d}.")

        if self.blue_peppers:
            print("-------------------- BLUE FIRST --------------------")
            for pepper in self.blue_peppers:
                print(
                    f"Number {pepper.num} heat is {pepper.heat} ({(self.now - pepper.last_sorted_date).days} days not seen, {pepper.occurence}% occured)."
                )
            print("----------------------------------------------------")
            print("----------------------------------------------------")

        if self.red_peppers:
            print("-------------------- RED THEN --------------------")
            for pepper in self.red_peppers:
                print(
                    f"Number {pepper.num} heat is {pepper.heat} ({(self.now - pepper.last_sorted_date).days} days not seen, {pepper.occurence}% occured)."
                )
            print("----------------------------------------------------")
            print("----------------------------------------------------")

        print("End of pepper pot opening")

    def __sort_by_heat(self):
        self.blue_peppers.sort(key=lambda x: x.heat, reverse=False)
        self.red_peppers.sort(key=lambda x: x.heat, reverse=False)


if __name__ == '__main__':
    pot = PepperPot()
    pot.open()
