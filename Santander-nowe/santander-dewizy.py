import os
import requests
import re
import time
import threading
from tqdm import tqdm
from datetime import date, datetime, timedelta
from common.freeday import isFreeday
from bs4 import BeautifulSoup

START_DATE = date(2022, 12, 15)
# START_DATE = date(2021, 9, 17)
# START_DATE = date(2023, 1, 2)
# END_DATE = date(2023, 1, 4)
END_DATE = date(2023, 1, 20)
DATES = [
    # '2022-06-21',
    # '2022-11-07'
]


THREADS_NUMBER = 3

FILENAME = 'Santander-dewizy'

HEADER = '''Santander: Kursy walut
Aktualne tabele kursowe wymiany walut w Santander Bank Polska
DEWIZY

'''

FIELDS = ('Data', 'Godzina', 'Nr tabeli', 'Kupno', 'Sprzedaż',
          'Spread', 'Kurs średni Santander Bank Polska')

# ------------------------------------------------------------------------------

headers = {
    'authority': 'www.santander.pl',
    'accept': '*/*',
    'referer': 'https://www.santander.pl/przydatne-informacje/kursy-walut',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'connection': 'keep-alive',
}


def getRates(date):
    date_str = datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")
    url = f'https://www.santander.pl/przydatne-informacje/kursy-walut?action=component_request.action&component.action=getRates&component.id=2542920&date-2542920={date_str}'

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {'error': f"Failed to fetch the resource: HTTP {response.status_code}"}

    soup = BeautifulSoup(response.content, 'html.parser')

    # <h3 class="exchange_rates__header">Aktualna tabela kursowa nr <b>251a/22</b> z dnia: <b>29-12-2022</b></h3>
    table_dates_tmp = re.findall(
        '\d\d-\d\d-\d\d\d\d', soup.find("h3", {"class": "exchange_rates__header"}).text)

    if len(table_dates_tmp) != 1:
        return {'error': f"Failed to parse table date"}

    table_date = table_dates_tmp[0].strip()

    if table_date != date_str:
        if isFreeday(date):
            return {'error': f"No course entries on this day"}
        # print('requested date:', date, date_str)
        # print('got date:', table_date)
        # print('Table header:', soup.find("h3", {"class": "exchange_rates__header"}).text)
        # with open(date+'_XXXX', 'w') as f:
        #     f.write(response.content.decode('utf-8'))
        return {'error': f"Got another date than expected. Probably no course entries on this day but it is strongly recommended to try again"}

    # table codes
    options = []
    for option in soup.find("select", {"class": "js-exchange_rates__publication-table-number"}).find_all("option"):
        options.append((option['value'], option.text.strip()))
        if option.attrs.get('selected') == 'selected':
            already_downloaded_table_code = option['value']
            already_downloaded_response_content = response.content

    result, info = '', ''

    for (code, hour) in options:

        if code == already_downloaded_table_code:
            content = already_downloaded_response_content
        else:
            url = f'https://www.santander.pl/przydatne-informacje/kursy-walut?action=component_request.action&component.action=getRates&component.id=2542920&t-2542920={code}'
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return {'error': f"Failed to fetch the resource: HTTP {response.status_code}"}
            content = response.content

        soup = BeautifulSoup(content, 'html.parser')

        # <h3 class="exchange_rates__header">Aktualna tabela kursowa nr <b>251a/22</b> z dnia: <b>29-12-2022</b></h3>
        table_dates_tmp = re.findall(
            '\d\d-\d\d-\d\d\d\d', soup.find("h3", {"class": "exchange_rates__header"}).text)

        if len(table_dates_tmp) != 1:
            return {'error': f"Failed to parse table date {code}"}

        table_date = table_dates_tmp[0].strip()

        for option in soup.find("select", {"class": "js-exchange_rates__publication-table-number"}).find_all("option"):
            if option.attrs.get('selected') == 'selected':
                table_code = option['value'].strip()
                table_hour = option.text.strip()
                break

        # <tbody class="exchange_rates__table-body">
        #   <tr class="exchange_rates__td--currency">
        #       <td class="exchange_rates__symbol"><span>1 CHF</span></td>
        #       <td class="exchange_rates__buy"><span>4.7141</span></td>
        #       <td class="exchange_rates__sell"><span>4.8093</span></td>
        #       <td class="exchange_rates__spread"><span>0.0952</span></td>
        #       <td class="exchange_rates__mean"><span>4.7617</span></td>
        #   </tr>
        # </thead>

        for entry in soup.find("tbody", {"class": "exchange_rates__table-body"}).find_all("tr", {"class": "exchange_rates__td--currency"}):
            if '1 CHF' == entry.find("td", {"class": "exchange_rates__symbol"}).text.strip():
                buy = entry.find(
                    "td", {"class": "exchange_rates__buy"}).text.strip()
                sell = entry.find(
                    "td", {"class": "exchange_rates__sell"}).text.strip()
                spread = entry.find(
                    "td", {"class": "exchange_rates__spread"}).text.strip()
                mean = entry.find(
                    "td", {"class": "exchange_rates__mean"}).text.strip()
                break
        else:
            info += f'{date}\tCHF not found in table {table_code.strip()} from {hour}'
            continue

        row = (date, table_hour, table_code, buy, sell, spread, mean)
        result += '\t'.join([str(x) for x in row]) + '\n'

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
    # x = getRates('2008-11-10')

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
