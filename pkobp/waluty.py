import os
import re
import requests
import time
import threading
from html_table_parser import HTMLTableParser
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import date, timedelta, datetime


START_DATE = date(2022, 11, 25)
# START_DATE = date(2000, 8, 1)
END_DATE = date(2023, 1, 3)
# END_DATE = date(2022, 11, 27)

THREADS_NUMBER = 1

FILENAME = 'PKOBP-Tabela_kursow'

INFO = '''PKO BP: TABELA KURSÓW
* - Kursy dla transakcji z wyłączeniem obsługi kredytów
** - Kursy walut wykorzystywane do obsługi kredytów

'''

FIELDS = ('Data', 'Godzina', 'Nr tabeli', 'Średni kurs NBP*',
          'Kupno Dewizy*', 'Kupno Pieniądze*', 'Kupno Zmiana*',
          'Sprzedaż Dewizy*', 'Sprzedaż Pieniądze*', 'Sprzedaż Zmiana*',
          'Kupno Dewizy**', 'Kupno Zmiana**',
          'Sprzedaż Dewizy**', 'Sprzedaż Zmiana**'
          )

# ------------------------------------------------------------------------------
ERROR_LABEL = 'error'

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,pl;q=0.7',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Host': 'www.pkobp.pl',
    'Referer': 'https://www.pkobp.pl/waluty/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}


def getRates(date):
    date_str = datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")

    url = f'https://www.pkobp.pl/waluty/?part=rates&date={date_str}'
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {ERROR_LABEL: f"Failed to fetch the resource (HTTP status was code not 200)"}

    soup = BeautifulSoup(response.content, 'html.parser')

    hours = soup.find("input", {"type": "hidden",
                                "id": "js-courses-hours"})

    if hours is None:
        return {ERROR_LABEL: f"Invalid page received"}

    hours = re.findall('\d\d:\d\d', hours.attrs['value'])
    hours = sorted(set(hours))

    # Brak notowań tego dnia (np. święto)
    if hours == []:
        return {ERROR_LABEL: f"No course entries on this day"}

    # Check if received date is the same as requested
    received_date = soup.find(
        "input", {"type": "hidden", "class": "js-real-date"}).attrs['value']
    if received_date != date_str.replace('-', '.'):
        return {ERROR_LABEL: f"Requested antoher date than received: {received_date}"}

    result = ''

    for hour in hours:
        url = f'https://www.pkobp.pl/waluty/?part=rates&date={date_str}&time={hour}'
        response = requests.get(url, headers=headers)

        soup = BeautifulSoup(response.content, 'html.parser')
        nr_tabeli = soup.find(
            "div", {"class": "course__table-version"}).text.strip()
        nr_tabeli = nr_tabeli.split()[-1]

        all_courses = soup.find_all("div", {"class": "course"})

        for course in all_courses:
            country = course.find("h3", {"class": "course__title"})

            if not country:
                continue

            elif country.text.strip() == "SZWAJCARIA":

                parser = HTMLTableParser()
                parser.feed(str(course))

                kredytowe_kupno_dewizy = ''
                kredytowe_kupno_zmiana = ''
                kredytowe_sprzedaz_dewizy = ''
                kredytowe_sprzedaz_zmiana = ''

                if parser.tables[0][0] == ['', 'Dewizy', 'Pieniądze', 'Zmiana']:
                    # [['', 'Dewizy', 'Pieniądze', 'Zmiana'], ['Kupno', '2.5489', '2.5438', '0.19%'], ['Sprzedaż', '2.6056', '2.6108', '0.19%']]

                    nie_kredytowe_kurs_NBP = course.find(
                        "div", {"class": "course__info"}).text.strip().split()[-1]

                    nie_kredytowe_dewizy = parser.tables[0]

                    nie_kredytowe_kupno_dewizy = nie_kredytowe_dewizy[1][1]
                    nie_kredytowe_kupno_pieniadze = nie_kredytowe_dewizy[1][2]
                    nie_kredytowe_kupno_zmiana = nie_kredytowe_dewizy[1][3]
                    nie_kredytowe_sprzedaz_dewizy = nie_kredytowe_dewizy[2][1]
                    nie_kredytowe_sprzedaz_pieniadze = nie_kredytowe_dewizy[2][2]
                    nie_kredytowe_sprzedaz_zmiana = nie_kredytowe_dewizy[2][3]

                elif parser.tables[0][0] == ['', 'Dewizy', 'Zmiana']:
                    # [['', 'Dewizy', 'Zmiana'], ['Kupno', '4.3940', '0.02%'], ['Sprzedaż', '4.4381', '0.02%']]
                    kredytowe_dewizy = parser.tables[0]

                    kredytowe_kupno_dewizy = kredytowe_dewizy[1][1]
                    kredytowe_kupno_zmiana = kredytowe_dewizy[1][2]
                    kredytowe_sprzedaz_dewizy = kredytowe_dewizy[2][1]
                    kredytowe_sprzedaz_zmiana = kredytowe_dewizy[2][2]

                else:
                    return {ERROR_LABEL: f"Table contains invalid headers and data"}

        row = (date, hour, nr_tabeli, nie_kredytowe_kurs_NBP,
               nie_kredytowe_kupno_dewizy, nie_kredytowe_kupno_pieniadze, nie_kredytowe_kupno_zmiana,
               nie_kredytowe_sprzedaz_dewizy, nie_kredytowe_sprzedaz_pieniadze, nie_kredytowe_sprzedaz_zmiana,
               kredytowe_kupno_dewizy, kredytowe_kupno_zmiana,
               kredytowe_sprzedaz_dewizy, kredytowe_sprzedaz_zmiana
               )

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

    dates = []
    start_time = time.time()

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
