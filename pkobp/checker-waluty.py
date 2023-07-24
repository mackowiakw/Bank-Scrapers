import sys

FILENAME = 'pkobp/PKOBP-Tabela_kursow-0.txt'
TABCOUNT = 13
FIRSTLINE_NUM = 6
# CORRUPTED_LINES = [2436, 5848]
CORRUPTED_LINES = [2484, 5952]
MISSING_DATES = ['2000-11-27', '2000-11-28', '2004-01-06', '2005-04-08']


FIRSTLINE = '2000-08-02	08:00	I/149/00	2.6052	2.5443	2.5417	-0.39%	2.6220	2.6297	-0.39%				'

# ------------------------------------------------------------------------------------------

previous = FIRSTLINE.split('\t')
downloaded_dates = [previous[0].strip()]

with open(FILENAME, 'r', encoding='utf-8') as f:
    i = 0
    for line in f.readlines():
        i += 1
        if i <= FIRSTLINE_NUM:
            continue

        this = line.strip().split('\t')
        downloaded_dates.append(this[0])

        if line.count('\t') != TABCOUNT:
            sys.exit(f"Dupa (taby): {i} {line}")

        if previous[0] + previous[1] >= this[0] + this[1]:
            sys.exit(f"Dupa (kolejność): {i} {line}")

        # type check
        for id in range(3, len(this) - 1):
            if this[id]:
                try:
                    if this[id][-1] == '%':
                        float(this[id][:-1])
                    else:
                        float(this[id])

                except Exception as e:
                    if i not in CORRUPTED_LINES:
                        print(e)
                        print(this)
                        sys.exit(
                            f'Dupa (zły typ): "{this[id]}" linia {i}: {line}')

        previous = this

start_date = FIRSTLINE.split('\t')[0]

with open('dates.txt', 'r', encoding='utf-8') as f:
    for date in f.readlines():
        date = date.strip()

        if date < start_date:
            continue

        if date not in downloaded_dates:
            if date not in MISSING_DATES:
                sys.exit(f"Dupa (brakująca data): {date}")


print("OK")
