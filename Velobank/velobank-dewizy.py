import json
import os
import requests
import time
import threading
from tqdm import tqdm
from datetime import date, datetime, timedelta
from common.freeday import isFreeday
from bs4 import BeautifulSoup

# START_DATE = date(2004, 1, 1)
# END_DATE = date(2006, 2, 1)
# START_DATE = date(2023, 1, 10)
# START_DATE = date(2001, 2, 14)
# END_DATE = date(2005, 1, 31)
# START_DATE = date(2001, 2, 14)
START_DATE = date(2023, 1, 4)
END_DATE = date(2023, 1, 20)
DATES = [

    # '2004-12-25',
    # '2004-11-10',  # No course entries on this day
    # '2004-11-11',  # No course entries on this day
    # '2004-11-12',  # No course entries on this day

    # '2004-11-15',  # No course entries on this day
    # '2004-11-16',  # No course entries on this day
    # '2004-11-17',  # No course entries on this day
    # '2004-11-18',  # No course entries on this day
    # '2004-11-19',  # 10:36:59	CHF entry not found

    # '2004-11-22',  # No course entries on this day
    # '2004-11-23',  # No course entries on this day
    # '2022-05-01',

    # '2022-05-03',
    # '2022-11-11',
    # '2023-01-06',
    # '2023-01-07',
    # '2023-01-08',
    # '2023-01-09',
    # '2015-01-10',
    # '2015-01-10',
    # '2015-01-10',
    # '2016-01-09',
    # '2022-06-30',

    # '2013-04-19',
    # '2020-10-01',
    # '2023-01-15',
    # '2023-01-16',
    # '2023-01-17',
    # '2015-01-10',

]

THREADS_NUMBER = 5

_TOKEN = 'wqyryaME4ple1yat5pIwBIWNm4VuUAQGSDLQ77S6'
_COOKIE = 'salesmore_affId=GB; _gcl_au=1.1.910725504.1673008832; _ga=GA1.2.281154292.1673008833; cookieInfo=1; _gid=GA1.2.258326227.1674327461; XSRF-TOKEN=wqyryaME4ple1yat5pIwBIWNm4VuUAQGSDLQ77S6; salesmore_tdpeh=kampania strona wnioski.velobank.pl; _gat_UA-33140607-1=1; _gat_UA-115307957-1=1; user_session=eyJpdiI6ImYybmZ4M2NXRTNKc21rQ3N3ZjlRcGc9PSIsInZhbHVlIjoiTVFYdk5GdDB4UDRYN05rYytIbEpaN3QxTEZUOUgwcWxsUSszMVVKMEVaem5abUI0NWxtMzc3ZGgrMzhVWEpja2ZlZW9LSHZVbUZzd2JDUTByT3cxN25PNGU1aHA3QmtDWm1YcG16SFNmNmw3Z0x3Y3BoMnRuZDF0eEFKRWErOEgiLCJtYWMiOiIxNGZlYmUzYjg0MTc3MzhhNmY4ZTAwZTY4YzZhOWMyYTc4NWUxYTFjMjdkMGY0MzkyZWJhZGNhYTYxYmEzN2QzIiwidGFnIjoiIn0='

FILENAME = f'velobank-dewizy'

HEADER = f'''Velobank: Kursy walut - DEWIZY (CHF)

* - Po kursie średnim NBP


'''

FIELDS = ('Data', 'Godzina', 'Kupno', 'Sprzedaż',
          'Kurs średni NBP (FIXING)', 'W przeliczeniu 5000 USD*')

# ------------------------------------------------------------------------------

headers = {
    'accept': 'application/json',
    # 'connection': 'keep-alive',
    # 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'cookie': _COOKIE,
    'origin': 'https://www.velobank.pl',
    'referer': 'https://www.velobank.pl/kursy-walut',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'x-csrf-TOKEN': _TOKEN,
    # 'x-requested-With': 'XMLHttpRequest',

    # 'connection': 'keep-alive',
}


def getRates(date):

    url = 'https://www.velobank.pl/api/modules/exchange-rates/changeDate'

    post_data = {
        'dateTime': f"{date} 23:59:59",
        'type': 'foreign',
        'locale': 'pl',
        '_token': _TOKEN,
    }

    response = requests.post(url, data=post_data, headers=headers)

    if response.status_code != 200:
        return {'error': f"Failed to fetch the resource: HTTP {response.status_code}"}

    data = response.json()
    already_downloaded_data = data

    if 'table' not in data:
        return {'error': f"Key 'table' not found in response"}

    soup = BeautifulSoup(data['table'], 'html.parser')
    time_select = soup.find("select", {"name": "time"})

    if not time_select:
        # if isFreeday(date):
        # return {'error': f"No course entries on this day (FREEDAY)"}

        already_downloaded_hour = '23:59:59'
        hours = ['23:59:59']
        one_entry_this_day = True
        # return {'error': f"No course entries on this day"}
    else:
        one_entry_this_day = False

        already_downloaded_hour = time_select.find(
            "option", selected=True).attrs['value']
        # search for entries on this day
        hours = []
        for option in time_select.find("optgroup", {"label": "Czas"}).find_all("option"):
            hours.append(option.attrs['value'])
        hours = sorted(hours)

        # where = time_select.find("optgroup", {"label": "Czas"}).find_all("option")
        # hours = sorted([option.attrs['value'] for option in where])
    # ----------------------------------------------------------------------------------------------------

    result, info = '', ''
    for hour in hours:
        if hour == already_downloaded_hour:
            data = already_downloaded_data
        else:
            post_data = {
                'dateTime': f'{date} {hour}',
                'type': 'foreign',
                'locale': 'pl',
                '_token': _TOKEN,
            }
            response = requests.post(url, data=post_data, headers=headers)
            if response.status_code != 200:
                return {'error': f"Failed to fetch the resource: HTTP {response.status_code}"}
            data = response.json()
            if 'table' not in data:
                return {'error': f"Key 'table' not found in response"}

        soup = BeautifulSoup(data['table'], 'html.parser')

        if one_entry_this_day:
            selected_hour = '23:59:59'
        else:
            selected_hour = soup.find("select", {"name": "time"}).find(
                "option", selected=True).attrs['value']

        if hour != selected_hour:
            return {'error': f"Critical error. Selected date is not the same as requested"}

        # <div class="table-container">
        #   <table>
        #     <tbody>
        #       <tr class="row-header">
        #         <td> Kraj </td>
        #         <td> Symbol waluty (JM) </td>
        #         <td> Kupno </td>
        #         <td> Sprzedaż </td>
        #         <td> Kurs średni NBP (FIXING) </td>
        #         <td> W przeliczeniu 5000 USD* </td>
        #       </tr>
        #       <tr class="row-4">
        #         <td> Szwajcaria </td>
        #         <td> 797/CHF (1) </td>
        #         <td> 4.6325 <i class="icon icon-currency-down"></i> </td>
        #         <td> 4.7963 <i class="icon icon-currency-down"></i> </td>
        #         <td> 4.6959 <i class="icon icon-currency-up"></i> </td>
        #         <td> 4625 </td>
        #       </tr>
        #     </tbody>
        #   </table>
        # </div>

        for entry in soup.find("div", {"class": "table-container"}).find("table").find("tbody").find_all("tr"):
            tds = [td.text.strip() for td in entry.find_all("td")]

            if tds[0] == 'Szwajcaria':
                if len(tds) != 6:
                    info += f"{date}\tINFO: Another number of columns\n"
                # buy = tds[2]
                # sell = tds[3]
                # nbp_mean = tds[4]
                # usd_5000 = tds[5]
                if not isFreeday(date):
                    row = (date, hour, *tds[2:])
                else:
                    row = (date, hour, *tds[2:], 'FREEDAY')

                # row = (date, hour, buy, sell, nbp_mean, usd_5000)
                result += '\t'.join([str(x) for x in row]) + '\n'
                break
        else:
            info += f'{date}\t{hour}\tCHF entry not found'

    return {'data': result, 'info': info, }


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
    # getRates('2015-01-10')
    # getRates('2015-01-09')
    # for date in DATES:
    # x = getRates(date)
    # print(x['data'])
    # print(xd)
    # print(f)

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
