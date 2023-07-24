import os
import requests
import time
import threading
from tqdm import tqdm
from common.freeday import isFreeday
from datetime import date, datetime, timedelta

START_DATE = date(2006, 2, 1)
# START_DATE = date(2019, 10, 1)
END_DATE = date(2014, 5, 20)
# END_DATE = date(2019, 11, 8)
DATES = [
    # '2019-11-01',
    # '2019-11-02',
    # '2019-11-03',
    # '2019-11-04',
    # '2019-11-05',
    # '2021-06-12',
    # '2021-06-13',
    # '2021-06-14',
    # '2014-05-13',
    # '2014-05-14',
    # '2014-05-15',
]

THREADS_NUMBER = 13

# FILENAME = f'bnpparibas-zolte-kursy-walut'
FILENAME = f'bnpparibas-zolte-kursy-walut_HL'
# FILENAME_MG_HL = f'bnpparibas-zolte-kursy-walut_MG_HL'
# FILENAME_CRD = f'bnpparibas-zolte-kursy-walut_CRD'

HEADER = f'''BNP Paribas: ŻÓŁTE KURSY WALUT
Tabela kursów walut dotyczy Klientów w ramach działalności przejętej przez BNP Paribas Bank Polska S.A. w wyniku podziału podmiotu o numerze KRS 14540

ARCHIWALNE KURSY WALUT DLA UMÓW HIPOTECZNYCH - NUMERY ZAWIERAJĄCE HL

* - Pole dodatkowe (niewidoczne w przeglądarce)

'''

# HEADER_MG_HL = HEADER.replace(
# 'TABELA KURSÓW WALUT', 'KURSY WALUT DLA UMÓW HIPOTECZNYCH - NUMERY ZACZYNAJĄCE SIĘ OD MG I HL')
# HEADER_CRD = HEADER.replace(
# 'TABELA KURSÓW WALUT', 'KURSY WALUT DLA UMÓW HIPOTECZNYCH - NUMERY ZACZYNAJĄCE SIĘ OD CRD')

FIELDS = ('Data', 'Godzina', 'ID', 'Kupno',
          'Sprzedaż', 'Spread', 'Kurs średni*')

# ------------------------------------------------------------------------------

FIELDNAMES = ('ratedate', 'ratetime', 'id', 'buyrate',
              'sellrate', 'spread', 'averagerate')

headers = {
    'Accept': 'application/json',
    'Connection': 'keep-alive',
    # 'Referer': 'https://zoltekursywalut.bnpparibas.pl/kursy-walut-2',
    'Referer': 'https://zoltekursywalut.bnpparibas.pl/archiwalne-kursy-walut-dla-umow-hipotecznych---numery-zawierajace-hl',
}


def getRates(date):
    # url = f'https://zoltekursywalut.bnpparibas.pl/Quot/get?type=kursy walut&date={date}'
    url = f'https://zoltekursywalut.bnpparibas.pl/Quot/get?type=kursy polbank&date={date}'

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {'error': f"Failed to fetch the resource: HTTP {response.status_code}"}

    result = ''

    data = response.json()

    table_date = data['date']

    if table_date != date:
        return {'error': f"Got another date than expected"}

    if data['rates'] == []:
        if isFreeday(date):
            return {'error': f"No course entries on this day (FREEDAY)"}
        return {'error': f"No course entries on this day"}

    # Single entry in data.rates:
    # {
    #     "name": "kursy walut",
    #     "unit": "1",
    #     "code": "CHF",
    #     "id": "795197",
    #     "currency_id": "3",
    #     "buyrate": "3.7786",
    #     "sellrate": "3.9724",
    #     "averagerate": "3.8755",
    #     "spread": "0.1938",
    #     "bmindex": "0.0000",
    #     "ratedate": "2019-11-07",
    #     "ratetime": "11:19:30"
    # }

    CHFs = [entry for entry in data['rates'] if entry['code'] == 'CHF']
    CHFs = sorted(CHFs, key=lambda entry: f"{entry['ratetime']} {entry['id']}")

    # first_entry = '\t'.join([CHFs[0][field] for field in FIELDNAMES]) + '\n'

    for entry in CHFs:
        result += '\t'.join([entry[field] for field in FIELDNAMES]) + '\n'

    # return {'data': result, 'first_entry': first_entry}
    return {'data': result}


class DownloadingThread(threading.Thread):
    def __init__(self, dates):
        super(DownloadingThread, self).__init__()
        self.dates = dates
        self.errors = []
        self.result = ''
        # self.result_MG_HL = ''

    def run(self):
        # print("Warning! This is approximated progress bar and some other threads can be still operating after reaching 100%.")
        for date in tqdm(self.dates):
            try:
                rates = getRates(date)
                if 'error' in rates:
                    self.errors.append(f"{date}\t{rates['error']}")
                else:
                    self.result += rates['data']
                    # self.result_MG_HL += rates['first_entry']
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
    # print(x)

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

    # result_mg_hl = HEADER_MG_HL + '\t'.join(FIELDS) + '\n' + \
    #     ''.join([t.result_MG_HL for t in threads])

    # result_crd = HEADER_CRD + '\t'.join(FIELDS) + '\n' + \
    #     ''.join([t.result for t in threads])

    errors = '\n'.join(['\n'.join(t.errors)
                       for t in threads if t.errors]) + '\n'

    i = 0
    while os.path.exists(f'{FILENAME}-{i}.txt'):
        i += 1

    # kursy walut
    with open(f'{FILENAME}-{i}.txt', 'w', encoding='utf-8') as result_file:
        result_file.write(result)

    # MG HL
    # with open(f'{FILENAME_MG_HL}-{i}.txt', 'w', encoding='utf-8') as result_file:
    #     result_file.write(result_mg_hl)

    # # CRD
    # with open(f'{FILENAME_CRD}-{i}.txt', 'w', encoding='utf-8') as result_file:
    #     result_file.write(result_crd)

    # Fails
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
