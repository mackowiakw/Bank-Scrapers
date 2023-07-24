import json
import requests
import threading
from tqdm import tqdm
from datetime import date, timedelta


colNames = ('Data', 'Godzina', 'Kupno', 'Sprzedaż', 'Spread', 'Kurs średni')
fields = ('ratedate', 'ratetime', 'buyrate', 'sellrate', 'spread', 'averagerate')

def getRates(date):
    url = f'https://zoltekursywalut.bnpparibas.pl/Quot/get?type=kursy polbank&date={date}'
    response = requests.post(url)

    data = json.loads(response.content.decode('utf-8'))

    partialResult = ''
    for record in data['rates']:
        if record['code'] == 'CHF':
            partialResult += '\t'.join([record[key] for key in fields]) + '\n'
        elif partialResult:
            return partialResult

    return f'{date}\n'
    

class DownloadingThread(threading.Thread):
    def __init__(self, dates):
        super(DownloadingThread, self).__init__()
        self.dates = dates
        self.result = ''

    def run(self):
        for date in tqdm(self.dates):
            self.result += getRates(date)


def split(arr, n):
    k, m = divmod(len(arr), n)
    return (arr[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


if __name__ == '__main__':

    dates = []
    start_date = date(2006, 2, 1)
    end_date = date(2014, 5, 20)

    while start_date <= end_date:
        if start_date.weekday() < 5:
            dates.append(start_date.strftime('%Y-%m-%d'))
        start_date += timedelta(days=1)

    threads = [DownloadingThread(d) for d in split(dates, 16)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    result = '\t'.join(colNames) + '\n' + ''.join([t.result for t in threads])

    with open(f'bnp-zolte-zawierajace-HL.txt', 'w') as result_file:
        result_file.write(result)
