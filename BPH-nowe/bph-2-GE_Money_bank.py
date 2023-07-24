import os
import requests
import time
import threading
from tqdm import tqdm
from datetime import date, timedelta

# START_DATE = date(2004, 7, 1)
# END_DATE = date(2023, 1, 3)
START_DATE = date(2022, 12, 15)
END_DATE = date(2023, 1, 20)
DATES = []

THREADS_NUMBER = 4

FILENAME = 'BPH-GE_Money_Bank'

HEADER = '''BPH - Kursy walut: Dla Klientów dawnego GE Money Banku (CHF)

'''

FIELDS = ('Data', 'Kupno', 'Sprzedaż', 'Spread')

# ------------------------------------------------------------------------------


headers = {
    'authority': 'www.bph.pl',
    'accept': 'application/json',
    'referer': 'https://www.bph.pl/pl/kursy-walut/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'connection': 'keep-alive',
}


def getRates(date):
    url = f'https://www.bph.pl/pi/api/currency/twge/currencies?date={date}'

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {'error': f"Failed to fetch the resource: HTTP {response.status_code}"}

    if not response.content:
        return {'error': f"No course entries on this day"}

    data = response.json()
    result = ''

    for entry in data:
        if entry['currency'] == 'CHF':
            buying = entry['buying']
            selling = entry['selling']
            spread = entry['spread']
            break
    else:
        return {'error': 'CHF not found in the entry'}

    row = (date, buying, selling, spread)
    result += '\t'.join([str(x) for x in row]) + '\n'

    return {'data': result, 'info': ''}


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
    # x = getRates('2008-05-07')

    # print(x)
    # print(xd)

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
    print("Success rates: ", result.count('\n') - 2)
    print("Failure dates: ", errors.count('\n'))
    print(f"Execution time: {exec_time//60} min {round(exec_time % 60, 2)} s")
