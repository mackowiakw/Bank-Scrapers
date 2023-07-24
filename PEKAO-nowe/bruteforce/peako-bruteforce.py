import os
import requests
import time
import threading
from tqdm import tqdm
# from common.freeday import isFreeday
from datetime import date, timedelta, datetime


# START_DATE = date(2023, 1, 18)
START_DATE = date(2005, 1, 1)
END_DATE = date(2005, 12, 31)
# END_DATE = date(2022, 12, 4)
# END_DATE = date(2023, 1, 20)

DATES = [    # '2006-08-15',

    '2009-08-11 3',
]

THREADS_NUMBER = 4

MAX_HTTP_ATTEMPS = 3
# MAX_DAY_ENTRIES = 10
# MAX_ENTRIES_OFFSET = 2

FILENAME = 'PEKAO-Kursy_walut-bruteforce'

HEADER = '''PEKAO: Tabela kursowa Banku Pekao S.A. (CHF)

Dane powyciągne z poniższego linku iterując po parametrach 'date' oraz 'table':

https://www.pekao.com.pl/.currencies/file?type=TEXT&source=PEKAO&date=2020-01-20&table=1

Ten link jest tym samym, co kryje się pod przyciskiem 'POBIERZ TXT' na stronie internetowej
Zdarzają się jednak dni, kiedy na stronie nie ma widocznych żadnych kursów, ale link do pobrania pliku działa
Na przykład 2020-01-20 - na stronie kursów nie widać, chociaż pod linkiem są dostępne

* - Nr tabeli nie zawsze jest ciągły. Są dni z tabelami [2, 3] albo [1, 2, 4]

'''

FIELDS = ('Data', 'Godzina', 'Nr tabeli*', 'Kupno', 'Sprzedaż', 'Spread')

# ------------------------------------------------------------------------------

headers = {
    'Authority': 'www.pekao.com.pl',
    'Accept': 'text/html',
    'Accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,pl;q=0.7',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
}


def getRates(date, table=1):

    result, info = '', ''
    # last_succeded_table_number = 0

    # for pekaoTable in range(1, MAX_DAY_ENTRIES):

    # url = f'https://www.pekao.com.pl/.currencies/file?type=TEXT&source=PEKAO&date={date}&table={pekaoTable}'
    url = f'https://www.pekao.com.pl/.currencies/file?type=TEXT&source=PEKAO&date={date}&table={table}'

    for _ in range(MAX_HTTP_ATTEMPS):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            break
    else:
        # if isFreeday(date):
        # return {'error': f"FREEDAY"}
        # if pekaoTable >= last_succeded_table_number + MAX_ENTRIES_OFFSET:
        # break
        # if pekaoTable == MAX_ENTRIES_OFFSET + 1 and not isFreeday(date):
        # return {'error': f"No course entries on this day"}
        # info += f"{date}\t{'--:--'}\t{pekaoTable}\t{MAX_HTTP_ATTEMPS} OF {MAX_HTTP_ATTEMPS} FAILED TO FETCH TABLE. LAST HTTP STATUS: {response.status_code}\n"
        return {'error': f"{table}\t{MAX_HTTP_ATTEMPS} OF {MAX_HTTP_ATTEMPS} FAILED TO FETCH TABLE. LAST HTTP STATUS: {response.status_code}"}
        # continue

    data = response.content.decode('utf-8')

    for line in data.split('\n'):

        line = line.strip()
        if line.startswith('TABELA KURSOWA'):
            # ['TABELA', 'KURSOWA', 'NR:', '1', '30.11.2020', '07:00']
            line = line.split()
            table_number = line[3]
            table_date = f'{line[4][6:10]}-{line[4][3:5]}-{line[4][0:2]}'
            table_hour = line[5]

            if table_date != date or table_number != str(table):
                return {'error': f"{'--:--'}\t{table}\tGot another date or antoher table number than requested. Got:\t{table_date}\t{table_number}"}
            else:
                continue

        if line.endswith('CHF'):
            # ['797', '1:1', 'Szwajcaria', '1/', '4.0463', '4.2484', '0.2021', 'CHF']
            line = line.split()
            if len(line) != 8:
                # info += f"{table_date}
                return {'error': f"{table_hour}\t{table_number}\tWrong number of fields:\t{len(line)}"}
            else:
                kupno = line[4]
                sprzedaz = line[5]
                spread = line[6]
                row = (table_date, table_hour, table_number,
                       kupno, sprzedaz, spread)
                result += '\t'.join(row) + '\n'
                # last_succeded_table_number = int(table_number)
            break
    else:
        result += f"{table_date}\t{table_hour}\t{table_number}\tCHF entry not found\n"

    return {'data': result, 'info': info}


class DownloadingThread(threading.Thread):
    def __init__(self, dates):
        super(DownloadingThread, self).__init__()
        self.dates = dates
        self.errors = []
        self.result = ''

    def run(self):
        # print("Warning! This is approximated progress bar and some other threads can be still operating after reaching 100%.")
        for date in tqdm(self.dates):
            try:
                date = date.replace(f'\t', ' ')
                if ' ' in date:
                    day, num = date.split()
                    rates = getRates(day, num)
                else:
                    rates = getRates(date)
                if 'error' in rates:
                    self.errors.append(f"{date}\t{rates['error']}")
                else:
                    self.result += rates['data']
                    if rates['info']:
                        self.errors.append(rates['info'])
            except Exception as e:
                self.errors.append(f"{date}\tAnother error occured: {e}")


def split(arr, n):
    k, m = divmod(len(arr), n)
    return (arr[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


if __name__ == '__main__':

    # x = getRates('2022-06-30')
    # xd = getRates('2020-11-30')
    # x = getRates('2006-11-30') // błąd gdy nie ma peakoTable=1 ale jest pekaoTable=2
    # getRates('2023-01-20')
    # getRates('2015-01-09')
    # for date in DATES:
    # x = getRates(date)
    # print(x['data'])
    # print(x['error'])
    # print(xd)
    # print(f)

    # print(getRates('2005-01-03'))
    # import sys
    # sys.exit()
    # -------------------------------------------------

    dates = []
    start_time = time.time()

    if DATES:
        dates = DATES
    else:
        date = START_DATE
        while date <= END_DATE:
            if date.weekday() < 5:
                dates.append(date.strftime("%Y-%m-%d"))
            date += timedelta(days=1)

    threads = [DownloadingThread(d) for d in split(dates, THREADS_NUMBER)]

    print("Starting...")

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    result = HEADER + '\t'.join(FIELDS) + '\n' + \
        ''.join([t.result for t in threads])

    errors = '\n'.join(['\n'.join(t.errors)
                        for t in threads if t.errors]) + '\n'

    i = 0
    while os.path.exists(f'{FILENAME}-{i}.txt'):
        i += 1

    with open(f'{FILENAME}-{i}.txt', 'w', encoding='utf-8') as result_file:
        result_file.write(result)

    with open(f'{FILENAME}-FAILS-{i}.txt', 'w', encoding='utf-8') as fails_file:
        fails_file.write(errors)

    exec_time = time.time() - start_time
    time.sleep(1)

    print("Finished!")
    print("Total dates: ", len(dates))
    print("Success dates: ", len(dates) - errors.count('\n'))
    print("Total rates: ", result.count('\n') - 2)
    print("Failure dates: ", errors.count('\n'))
    print(f"Execution time: {exec_time//60} min {round(exec_time % 60, 2)} s")
