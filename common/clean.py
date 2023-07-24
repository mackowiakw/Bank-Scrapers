from freeday import isFreeday
from datetime import datetime

FILENAME = 'pekao-stare-kopia.txt'

fails = []
with open(FILENAME, 'r', encoding='utf-8') as file:
    for line in file.readlines():

        if line.strip() == '':
            continue

        date = line.strip().split('\t')[0]

        if datetime.strptime(date, "%Y-%m-%d").weekday() in [5, 6]:
            continue

        if isFreeday(date):
            continue
        else:
            fails.append(line)


with open(FILENAME, 'w', encoding='utf-8') as file:
    file.writelines(''.join(fails))
