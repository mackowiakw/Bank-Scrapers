import sys
from datetime import datetime, timedelta


FILENAME = 'bruteforce.txt'

STARTLINE_NUM = 13

downloaded = {}
brakujace_daty = []

with open(FILENAME, 'r', encoding='utf-8') as f:
    current_line_number = 0
    for line in f.readlines():
        current_line_number += 1
        if current_line_number <= STARTLINE_NUM:
            continue

        this = line.strip().split('\t')
        date = this[0]
        table = int(this[2])

        if date not in downloaded:
            downloaded[date] = [table]
        else:
            downloaded[date] += [table]

for date, tables in downloaded.items():
    # if len(tables) != max(tables):
    # print(f'{date}:', *tables, ':', *
    # missing = [t for t in range(1, max(tables)) if t not in tables]
    # print(f'{date}', *missing)

    # for miss in missing:
    max_p0 = max(tables)
    max_p1 = max_p0 + 1
    max_p2 = max_p0 + 2

    # if max_p0 > 1:
    # brakujace_daty.append(f"'{date} {max_p1}',")
    # brakujace_daty.append(f"'{date} {max_p2}',")

    if max_p0 == 1:
        brakujace_daty.append(f"'{date} {max_p1}',")


with open('brakujace_daty.py', 'w') as f:
    f.write('DATESX = [' + '\n'.join(brakujace_daty) + ']')


print("OK")
