import os
import random
import requests
import time
import threading
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import date, timedelta, datetime


START_DATE = date(2005, 1, 1)
END_DATE = date(2022, 12, 4)

# tych dat brakuje względem PEKAO-0 i PEKAO-1
DATES = [
    '2023-01-19',
]

THREADS_NUMBER = 5
MAX_ATTEMPS = 5

FILENAME = 'PEKAO-Kursy_walut-3'

INFO = '''PEKAO: Tabela kursowa Banku Pekao S.A. (CHF)

'''

FIELDS = ('Data', 'Godzina', 'Nr tabeli', 'Kupno', 'Sprzedaż', 'Spread')

# ------------------------------------------------------------------------------

ERROR_LABEL = 'error'

headers = {
    'Authority': 'www.pekao.com.pl',
    'Accept': 'text/html',
    'Accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,pl;q=0.7',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
}


def getRates(date):

    url = f'https://www.pekao.com.pl/kursy-walut/lista-walut.html?pekaoDate={date}'
    response = requests.get(url, headers=headers)

    attemps = 1
    while response.status_code == 410:
        # if attemps > MAX_ATTEMPS - 5:
        # time.sleep(4 + random.random())
        if attemps >= MAX_ATTEMPS:
            return {ERROR_LABEL: f"Failed to determinate number of entries this day ({MAX_ATTEMPS} of {MAX_ATTEMPS} attemps failed with HTTP 410 GONE)"}
        attemps += 1
        response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {ERROR_LABEL: f"Failed to fetch the resource: HTTP {response.status_code}"}

    soup = BeautifulSoup(response.content, 'html.parser')

    # <h2 class="">Tabela kursowa Banku Pekao S.A.</h2>
    # <p class="no-margin">Ostatnia aktualizacja: <span>02.12.2022</span> <span >07:00</span></p>
    h2 = soup.find("h2", string="Tabela kursowa Banku Pekao S.A.")
    p = h2.find_next_sibling("p")

    if p is None:
        return {ERROR_LABEL: f"No course entries on this day (A)"}

    # 'Ostatnia aktualizacja: 14.10.2010 08:10'
    last_updated = p.text.split(' ')[2]

    if last_updated != datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y"):
        return {ERROR_LABEL: f"No course entries on this day (B)"}

    # <select class="select-hide custom-list" name="exchangeTables" data-calendar-pekao-time data-custom-select>
    #   <option value="1">07:00</option>
    #   <option value="2">14:30</option>
    # </select>
    hours = soup.find("select", {"name": "exchangeTables"})
    entries_this_day = len(hours.find_all("option")) if hours else 1

    result = ''

    for num in range(1, 1 + entries_this_day):

        url = f'https://www.pekao.com.pl/.currencies/file?type=TEXT&source=PEKAO&date={date}&table={num}'
        response = requests.get(url, headers=headers)

        # NP TU https://www.pekao.com.pl/kursy-walut/lista-walut.html?pekaoDate=2006-11-30&pekaoTable=2

        # Brak wpisów o danej godzinie
        # https://www.pekao.com.pl/kursy-walut/lista-walut.html?pekaoDate=2008-10-27&pekaoTable=3
        if response.status_code == 410:
            url = f'https://www.pekao.com.pl/kursy-walut/lista-walut.html?pekaoDate={date}&pekaoTable={num}'
            response_check = requests.get(url, headers=headers)
            soup = BeautifulSoup(response_check.content, 'html.parser')

            # Gdy są wpisy dla danej godziny:
            #   <h2 class="">Tabela dla kart debetowych</h2>
            # Gdy nie ma wpisów dla danej godziny:
            #   <h2 class="cl-flag table-big-font text-center"> Brak kursu z danego dnia, proszę wybrać inną datę.  </h2>

            h2 = soup.find(
                "h2", {"class": "cl-flag table-big-font text-center"})
            if h2:
                if h2.text.strip() == 'Brak kursu z danego dnia, proszę wybrać inną datę.':
                    return {ERROR_LABEL: f"No course entry at this hour (C)"}

        # attemps = 1
        # while response.status_code == 410:
        #     # if attemps > MAX_ATTEMPS - 5:
        #     # time.sleep(4 + random.random())
        #     if attemps >= MAX_ATTEMPS:
        #         return {ERROR_LABEL: f"Failed to fetch table number {num} ({MAX_ATTEMPS} of {MAX_ATTEMPS} attemps failed with HTTP 410 GONE)"}
        #     attemps += 1
        #     response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return {ERROR_LABEL: f"Failed to fetch the resource: HTTP {response.status_code}"}

        for line in response.content.decode('utf-8').split('\r\n'):
            if line.startswith('TABELA KURSOWA'):
                tmp = line.split()
                table_number = tmp[3]
                table_date = f'{tmp[4][6:10]}-{tmp[4][3:5]}-{tmp[4][0:2]}'
                table_hour = tmp[5]
                continue

            if line.startswith('797   1:1   Szwajcaria'):
                tmp = line.split()
                kupno = tmp[4]
                sprzedaz = tmp[5]
                spread = tmp[6]
                break

        row = (table_date, table_hour, table_number, kupno, sprzedaz, spread)
        result += '\t'.join(row) + '\n'

    return {'data': result}


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
                if ERROR_LABEL in rates:
                    self.errors.append(f"{date}\t{rates[ERROR_LABEL]}")
                else:
                    self.result += rates['data']
            except Exception as e:
                self.errors.append(f"{date}\tAnother error occured: {e}")


def split(arr, n):
    k, m = divmod(len(arr), n)
    return (arr[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


if __name__ == '__main__':

    # url = 'https://www.pekao.com.pl/kursy-walut/lista-walut.html?pekaoDate=2006-11-28'
    # response = requests.get(url)
    # with open(f'2006-11-28.html', 'wb') as out_file:
    #     out_file.write(response.content)
    # del response

    # x = getRates('2022-06-30')
    # xd = getRates('2006-11-28')
    # x = getRates('2006-11-30') // błąd gdy nie ma peakoTable=1 ale jest pekaoTable=2
    # x = getRates('2018-08-17')

    # print(x)
    # print(xd)

    # import sys
    # sys.exit()

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

    # with open('FAILS-1.txt') as file:
    # dates = file.readlines()
    # dates = [line.strip().split()[0] for line in dates]

    threads = [DownloadingThread(d) for d in split(dates, THREADS_NUMBER)]

    print("Starting...")

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    result = INFO + '\t'.join(FIELDS) + '\n' + \
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
