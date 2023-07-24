import sys

FILENAME = 'C://Users/WiktorMackowiak/Desktop/WYNIKI/PKOBP/PKOBP-Kursy_Spready_CHF_dla_kredytow_mieszk.txt'
TABCOUNT = 7
CORRUPTED_LINES = []
MISSING_DATES = []

FIRSTLINE_NUM = 6
FIRSTLINE = '2015-01-27	09:00	4.1278	0.00%	4.1692	0.00%	1.00%	0.0414'

# ------------------------------------------------------------------------------------------
#
#
#
#
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
