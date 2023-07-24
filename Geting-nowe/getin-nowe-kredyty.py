import json
import os
import re
import requests
import time
import threading
from tqdm import tqdm
from datetime import date, datetime, timedelta
# from common.freeday import isFreeday
from bs4 import BeautifulSoup

# START_DATE = date(2004, 8, 29)
# END_DATE = date(2006, 2, 1)
# START_DATE = date(2023, 1, 10)
# START_DATE = date(2001, 2, 14)
# END_DATE = date(2006, 1, 1)
# START_DATE = date(2021, 8, 21)
START_DATE = date(2023, 1, 1)
END_DATE = date(2023, 1, 20)
DATES = [
    # '2023-01-15',
    # '2023-01-16',
    # '2023-01-17',
    # '2015-01-22',
    # '2019-01-03',
    # '2019-08-22',
    # '2019-08-23',
    # '2019-10-30',

]


THREADS_NUMBER = 3

_TOKEN = 'oSY8r38ve9Wt0ZbR8cmt9g8KIQnuu9sZgLCH7yVd'
_COOKIE = '_ga=GA1.2.379930174.1673008829; cookieInfo=1; _gid=GA1.2.807981481.1674327388; XSRF-TOKEN=oSY8r38ve9Wt0ZbR8cmt9g8KIQnuu9sZgLCH7yVd; _gat_UA-33140607-1=1; _gat_UA-115307957-1=1; user_session=eyJpdiI6IjJWKzIyNmwvdmRzWGhnSzhLdDVLWkE9PSIsInZhbHVlIjoicGFuSVFHMXR6bzd1VTBGdkkyQ2NuajYvTDMxSUFiYm1YL1h6bVduYnFLQ1lBVXRoL3JLR3prbHdUWExEWEk3Y1JkQTlZTGtvL3JTZDBuNHFESElyaU4rSTZSaUxYRDN3Vm9HODVtT0xpNGppU2psYjQwV2VXbG1SdTdhZm5VTnIiLCJtYWMiOiIwYzgwNTVkOGI0ZDA3MzJjNWQxNTA0Yjg4ZjE0NzE0YzJmNzg4Y2Q3MDhiODI5ZmI0OTYwZDRiNTBkMTRmOTcwIiwidGFnIjoiIn0='

FILENAME = f'getin-kredyty'

HEADER = f'''Velobank: Kursy walut - KREDYTY (CHF)

* - Pobrano wszystkie dni - w tym soboty, niedziele i święta. 
    Datę 2019-08-23 traktować szczególnie bo nie działa (pokazuje różne wartości kursów po zmianie godziny na stronie)
** - Godziny notowań w dniach: 2015-01-22, 2019-01-03, 2019-08-22, 2019-08-23, 2019-10-30


'''

FIELDS = ('Data', 'Kupno', 'Sprzedaż', 'Spread')

# ------------------------------------------------------------------------------

headers = {
    'accept': 'application/json',
    'connection': 'keep-alive',
    # 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'cookie': _COOKIE,
    # 'origin': 'https://www.velobank.pl',
    'origin': 'https://www.getinbank.pl',
    # 'referer': 'https://www.velobank.pl/kursy-walut',
    'referer': 'https://www.getinbank.pl/kursy-walut',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'x-csrf-TOKEN': _TOKEN,
    # 'x-requested-With': 'XMLHttpRequest',

    # 'connection': 'keep-alive',
}


def getRates(date):

    # url = 'https://www.velobank.pl/api/modules/exchange-rates/changeDate'
    url = 'https://www.getinbank.pl/api/modules/exchange-rates/changeDate'

    post_data = {
        # 'dateTime': f"{date}",
        'dateTime': f"{date} 23:59:59",
        'type': 'credits',
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

    info = ''
    hours = re.findall("\d\d:\d\d", data['table'])

    # Extra check - succeed for ['2015-01-22', '2019-01-03', '2019-08-22', '2019-08-23', '2019-10-30',]
    if soup.find("select", {"name": "time"}) or hours:
        info += f'{date}\tMore than one hour found: [{",".join(sorted(set(hours)))}]'

    result = ''

    # <div class="table-container">
    #   <table>
    #     <tbody>
    #       <tr class="row-header">
    #         <th> Kraj </th>
    #         <th> Kupno </th>
    #         <th> Sprzedaż </th>
    #         <th> Spread </th>
    #       </tr>
    #       <tr class="row-1">
    #         <td> CHF </td>
    #         <td> 4.6325 <i class="icon icon-currency-up"></i> </td>
    #         <td> 4.7963 <i class="icon icon-currency-up"></i> </td>
    #         <td> 0.1638 <i class="icon icon-currency-up"></i> </td>
    #       </tr>
    #     </tbody>
    #   </table>
    # </div>

    for entry in soup.find("div", {"class": "table-container"}).find("table").find("tbody").find_all("tr"):
        tds = [td.text.strip()
               for td in entry.find_all("td") or entry.find_all("th")]

        if tds[0] == 'CHF':
            if len(tds) != 4:
                info += f"{date}\tINFO: Another number of columns\n"

            # row = (date.replace(" ", f"\t"), *tds[1:])
            row = (date, *tds[1:])
            result += '\t'.join([str(x) for x in row]) + '\n'
            break
    else:
        info += f'{date}\tCHF entry not found'

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
    # x = getRates('2004-08-03')
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
            # if date.weekday() < 5:
            #    # dates.append(date.strftime("%Y-%m-%d"))
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
