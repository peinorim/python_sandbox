import csv
from datetime import datetime


class Marble:
    def __init__(self, num=None, nb_sort=None, occurence=None, last_sorted_date=None):
        self.num = int(num)
        self.nb_sort = int(nb_sort)
        self.occurence = float(occurence.replace(',', '.'))
        self.sorted_date = datetime.strptime(last_sorted_date, '%d/%m/%Y')


class Pepper:
    data = list()

    def __init__(self, sort_by_occurence=True):
        self.__get_data(sort_by_occurence=sort_by_occurence)

    def __get_data(self, sort_by_occurence=True):
        with open('stats.csv', newline='') as csvfile:
            datareader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in datareader:
                self.data.append(
                    Marble(num=row[0], nb_sort=row[1], occurence=row[2], last_sorted_date=row[3])
                )
            csvfile.close()

            if sort_by_occurence:
                self.__sort_by_occurence()

    def __sort_by_occurence(self):
        self.data.sort(key=lambda x: x.occurence, reverse=True)


if __name__ == '__main__':
    pepper = Pepper()
    print("")
