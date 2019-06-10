import csv
import sys

from main import quadro

if __name__ == "__main__":

    print(sys.stdin.readline().strip() + ',similarity percentage')

    for row_source in csv.reader(iter(sys.stdin.readline, '')):
        row = row_source[2:]

        if row[0] == '' or row[1] == '' or row[2] == '' or row[3] == '':
            continue

        row = [float(string) for string in row]

        # Calculate users
        # row_source.append(str(quadro(row, d=[17.0, 70.0, 800.0, 35.0], n=[1, 5, 100, 5])))

        row_source.append(str(quadro(row, [290.0, 150.0, 18.0, 800], [10, 10, 1, 100])))

        print(','.join(row_source))