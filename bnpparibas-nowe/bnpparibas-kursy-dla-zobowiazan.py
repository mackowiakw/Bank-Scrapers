import json
import os
import requests
import time
import threading
from tqdm import tqdm
from datetime import date, datetime, timedelta
from common.freeday import isFreeday
from bs4 import BeautifulSoup

# START_DATE = date(2023, 1, 1)
# START_DATE = date(2021, 9, 17)
# START_DATE = date(2001, 2, 14)
# END_DATE = date(2002, 3, 4)
# END_DATE = date(2013, 5, 4)
START_DATE = date(2023, 1, 1)
END_DATE = date(2023, 1, 20)
DATES = [
    # '2022-05-01',

    # '2022-05-03',
    # '2022-11-11',
    # '2023-01-06',
    # '2023-01-07',
    # '2023-01-08',
    # '2023-01-09',
    # '2015-01-10',
    # '2016-01-09',
    # '2022-06-30',

    # '2013-04-19',
    # '2020-10-01',
    # '2023-01-01',
    # '2023-01-12',
    # '2023-01-13',
    # '2021-04-30',
    # '2021-05-01',
    # '2021-05-02',
    # '2021-05-03',
    # '2021-06-11',
    # '2021-06-12',
    # '2021-06-13',
    # '2021-06-14',
]

THREADS_NUMBER = 5
BANK_CODE = 'bnp'  # 'bnp' or 'bgz'

FILENAME = f'bnpparibas-kursy-dla-zobowiazan'

HEADER = f'''BNP Paribas: Kursy walut
TABELA KURSÓW WALUT DLA ZOBOWIĄZAŃ KREDYTOWYCH W BNP PARIBAS BANK POLSKA S.A.
na potrzeby obsługi aneksów antyspreadowych do produktów denominowanych do walut obcych oferowanych klientom detalicznym (konsumentom)


'''

FIELDS = ('Data', 'Nr tabeli Godzina', 'Kod tabeli',
          'Kupno', 'Sprzedaż', 'Spread', 'Kurs średni')

# ------------------------------------------------------------------------------

headers = {
    'authority': 'www.bnpparibas.pl',
    'accept': '*/*',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://www.bnpparibas.pl',
    'referer': 'https://www.bnpparibas.pl/kursy-walut/kursy-walut-dla-zobowiazan',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'connection': 'keep-alive',
}


def getRates(date):
    url = f'https://www.bnpparibas.pl/kursy-walut/kursy-walut-dla-zobowiazan?action=component_request.action&component.action=changeRates&component.id=3485215'

    post_data = {
        'componentId': 3485215,
        'ratesDate': date,
        'bankCode': '',  # BANK_CODE
    }

    response = requests.post(url, data=post_data, headers=headers)

    if response.status_code != 200:
        return {'error': f"Failed to fetch the resource: HTTP {response.status_code}"}

    soup = BeautifulSoup(response.content, 'html.parser')

    # <div class="configuration" data-configuration="{"defaultDate": "2023-01-12","showCalculator": "false"}">
    table_date = json.loads(soup.find(
        "div", {"class": "configuration"}).attrs['data-configuration'])['defaultDate']
    bank_select = soup.find("select", {"class": "bank_select"})
    table_bank = bank_select.find(
        "option", selected=True).attrs['value'] if bank_select else 'bnp'

    if table_date != date:
        if isFreeday(date):
            return {'error': f"No course entries on this day"}
        return {'error': f"Got another DATE than expected. Probably no course entries on this day but it is strongly recommended to try once again"}

    if table_bank != BANK_CODE:
        return {'error': f"Got another BANK than expected. No course entries on this day for this bank"}

    # search for entries on this day
    options = []
    for option in soup.find("select", {"class": "table_select"}).find_all("option"):
        options.append((option['value'], option.text.strip()))
        if option.attrs.get('selected') == 'selected':
            already_downloaded_table_code = option['value']
            already_downloaded_response_content = response.content

    options = sorted(options, key=lambda x: x[0])

    info = ''

    # Check if there exists antoher bank(s)
    if BANK_CODE == 'bnp' and bank_select is not None:
        banks = [b.attrs['value'] for b in bank_select.find_all("option")]

        if 'bnp' in banks:
            banks.remove('bnp')
        if 'bgz' in banks:
            info += f'{date}\tBGZ not downloaded'
            banks.remove('bgz')

        if banks:
            info += f'{date}\tFound another bank: {banks}'

    # ----------------------------------------------------------------------------------------------------

    result = ''
    for (code, num_hour) in options:
        # for (requested_code, requested_num_hour) in options:

        # num, hour = num_hour.split(' ')[1]   # '13 08:45'

        if code == already_downloaded_table_code:
            content = already_downloaded_response_content
        else:
            # if True:
            post_data = {
                'componentId': 3485215,
                'ratesTable': code,
                'bankCode': '',  # BANK_CODE
            }
            response = requests.post(url, data=post_data, headers=headers)
            if response.status_code != 200:
                return {'error': f"Failed to fetch the resource: HTTP {response.status_code}"}
            content = response.content

        soup = BeautifulSoup(content, 'html.parser')
        table_select = soup.find("select", {"class": "table_select"})
        bank_select = soup.find("select", {"class": "bank_select"})

        table_date = json.loads(soup.find(
            "div", {"class": "configuration"}).attrs['data-configuration'])['defaultDate']
        table_num_hour = table_select.find("option", selected=True).text
        # table_bank = bank_select.find(
        #     "option", selected=True).attrs['value'] if bank_select else 'bnp'
        table_code = table_select.find("option", selected=True).attrs['value']

        # <table class="rates_table default-table" aria-describedby="rates-3485215">
        #   <tbody>
        #     <tr class="bgz_bnp_exchange_rates__tableBodyRow" data-index="2">
        #       <td class="bgz_bnp_exchange_rates__country icon-CH">Szwajcaria</td>
        #       <td class="bgz_bnp_exchange_rates__currency important">1 CHF</td>
        #       <td>4,5639</td>
        #       <td>4,7979</td>
        #       <td>0,2340</td>
        #       <td>4,6809</td>
        #     </tr>
        #   </tbody>
        # </table>

        for entry in soup \
            .find("table", {"class": "rates_table", "aria-describedby": "rates-3485215"}) \
                .find("tbody") \
                .find_all("tr", {"class": "bgz_bnp_exchange_rates__tableBodyRow"}):

            if '1 CHF' == entry.find("td", {"class": "bgz_bnp_exchange_rates__currency"}).text.strip():
                tds = entry.find_all("td")

                if len(tds) != 6:
                    return {'error': f"Failed to parse table rows"}

                buy = tds[2].text.strip()
                sell = tds[3].text.strip()
                spread = tds[4].text.strip()
                mean = tds[5].text.strip()

                row = (table_date, table_num_hour,
                       table_code, buy, sell, spread, mean)
                result += '\t'.join([str(x) for x in row]) + '\n'
                break

        else:
            row = (table_date, table_num_hour, table_code)
            info += '\t'.join([str(x) for x in row]) + \
                f'\tCHF entry not found\n'

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
    # getRates('2023-01-13')
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
