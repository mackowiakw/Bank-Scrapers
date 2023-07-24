import sys
from freeday import isFreeday
from datetime import datetime, timedelta


FILENAME = 'pekao-kopia.txt'

STARTLINE_NUM = 13
COLUMNS_NUMBER = 5

INCLUDE_WEEKNDS = False


def SORT_KEY_LAMBDA(columns):
    # return columns[0]  # Data
    # return columns[0] + ' ' + columns[1]  # Data + godzina
    # return int(columns[2])  # id tabeli
    # return columns[2]  # id tabeli

    # data + nr_tabeli
    # return columns[0] + ' ' + columns[2]  # .split(' ')[0].rjust(3, '0')

    # data + godzina + nr_tabeli # .split(' ')[0].rjust(3, '0')
    return columns[0] + ' ' + columns[1] + ' ' + columns[2]


STARTLINE = '2005-01-03	07:00	1	2.5694	2.6876	0.1182'
LAST_LINE = '2023-01-20	07:00	1	4.6505	4.8838	0.2333'

CORRUPTED_LINES = []
MISSING_DATES = []

# ROW_STRUCTURE = (
#     {'type': 'float', 'ignore': ['', 1.0]},
# )

# ------------------------------------------------------------------------------------------
#
#
#
#
# ------------------------------------------------------------------------------------------

previous = STARTLINE.split('\t')
dates_downloaded = [previous[0].strip()]

with open(FILENAME, 'r', encoding='utf-8') as f:

    current_line_number = 0

    for line in f.readlines():

        current_line_number += 1

        if current_line_number <= STARTLINE_NUM:
            continue

        this = line.strip().split('\t')
        dates_downloaded.append(this[0])

        # if line.count('\t') + 1 not in (COLUMNS_NUMBER, COLUMNS_NUMBER+1):
        if line.count('\t') + 1 != COLUMNS_NUMBER:
            sys.exit(f"Dupa (taby): {current_line_number} {line}")

        if SORT_KEY_LAMBDA(this) <= SORT_KEY_LAMBDA(previous):
            if current_line_number not in CORRUPTED_LINES:
                # if this[1] == previous[1]:
                sys.exit(f"Dupa (kolejność): {current_line_number} {line}")

        # type check
        # for id in range(3, len(this) - 1):
        #     if this[id]:
        #         try:
        #             if this[id][-1] == '%':
        #                 float(this[id][:-1])
        #             else:
        #                 float(this[id])

        #         except Exception as e:
        #             if current_line_number not in CORRUPTED_LINES:
        #                 print(e)
        #                 print(this)
        #                 sys.exit(
        #                     f'Dupa (zły typ): "{this[id]}" linia {current_line_number}: {line}')

        # current_table_numer = int(this[2])
        # previous_table_number = int(previous[2])

        # if current_table_numer != previous_table_number + 1:
            # if this[0][5:] == previous[0][5:] and (current_line_number not in CORRUPTED_LINES):
                # sys.exit(
                # f"Dupa (brak tabeli): {current_table_numer - 1}\n{current_line_number}: {line}")

        previous = this


dates = []
date = datetime.strptime(STARTLINE.split('\t')[0], '%Y-%m-%d')
last_date = datetime.strptime(LAST_LINE.split('\t')[0], '%Y-%m-%d')

if last_date <= date:
    sys.exit(f"LAST_DATE must be greater than START_DATE")

while date <= last_date:
    if date.weekday() < 5:
        dates.append(date.strftime('%Y-%m-%d'))
    elif INCLUDE_WEEKNDS:
        dates.append(date.strftime('%Y-%m-%d'))
    date += timedelta(days=1)

# if abs(len(dates) - len(dates_downloaded)) > 20:
    # sys.exit(
    # f"Chyba niepoprawna liczba dat pobranych: {len(dates_downloaded)} ze wszystkich ({len(dates)})")

for tested_date in dates:
    if tested_date not in dates_downloaded \
            and tested_date not in MISSING_DATES \
            and not isFreeday(tested_date):
        print(f"Dupa (brakująca data): {tested_date}")
        # sys.exit(f"Dupa (brakująca data): {tested_date}")

print("OK")
