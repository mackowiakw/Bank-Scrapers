import re
import requests
import threading
from html_parser import HTMLTableParser
from tqdm import tqdm
from datetime import date, timedelta


fields = ('Data', 'Godzina', 'Pieniądze-Kupno', 'Pieniądze-Sprzedaż', 'Dewizy-Kupno', 'Dewizy-Sprzedaż', 'Spread')

missing_dates = ('02-01-2008', '24-03-2008', '01-05-2008', '22-05-2008', '15-08-2008', '11-11-2008', '25-12-2008', '26-12-2008', '01-01-2009', '13-04-2009', '01-05-2009', '11-06-2009', '11-11-2009', '25-12-2009', '01-01-2010', '05-04-2010', '03-05-2010', '03-06-2010', '01-11-2010', '11-11-2010', '06-01-2011', '25-04-2011', '03-05-2011', '23-06-2011', '15-08-2011',
                '01-11-2011', '11-11-2011', '26-12-2011', '06-01-2012', '09-04-2012', '01-05-2012', '03-05-2012', '07-06-2012', '15-08-2012', '01-11-2012', '25-12-2012', '26-12-2012', '01-01-2013', '01-04-2013', '01-05-2013', '03-05-2013', '30-05-2013', '15-08-2013', '01-11-2013', '11-11-2013', '25-12-2013', '26-12-2013', '01-01-2014', '06-01-2014', '21-04-2014', '01-05-2014')

base_URL = 'https://www.santander.pl/przydatne-informacje/kursy-archiwalne-kb?action=component_request.action&component.action=getRates&component.id=1980576'

headers = {
    'authority': 'www.santander.pl',
    'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'dnt': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-user': '?1',
    'sec-fetch-dest': 'document',
    'accept-language': 'en-GB,en;q=0.9',
}


def getHours(date):
    url = f'{base_URL}&date-1980576={date}'
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        error_dates.append(date)
        return []

    hours = re.findall('\d\d:\d\d', response.content.decode('utf-8'))
    return sorted(set(hours))


def getRates(date, time):
    url = f'{base_URL}&time-1980576={time}&date-1980576={date}'
    response = requests.get(url, headers=headers).content.decode('utf-8')

    parser = HTMLTableParser()
    parser.feed(response)

    try:
        returned_date = re.search('data-cur-date="\d\d-\d\d-\d\d\d\d', response).group(0)[-10:]
        returned_time = re.search('selected="selected" value="\d\d:\d\d', response).group(0)[-5:]
    except AttributeError:
        error_dates.append(date)
        return ''

    if returned_date != date or returned_time != time:
        error_dates.append(date)

    for row in parser.tables[0]:
        if row[1] == '1 CHF':
            return '\t'.join([date, time] + row[2:7]) + '\n'

    return ''


class DownloadingThread(threading.Thread):
    def __init__(self, dates):
        super(DownloadingThread, self).__init__()
        self.dates = dates
        self.result = ''

    def run(self):
        for date in tqdm(self.dates):
            for time in getHours(date):
                self.result += getRates(date, time)


def split(arr, n):
    k, m = divmod(len(arr), n)
    return (arr[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


if __name__ == '__main__':

    dates = []
    error_dates = []

    with open('error_Dates.txt') as file:
        dates = file.readlines()
        dates = [line.rstrip() for line in dates]

    # start_date = date(2008, 1, 2)
    # end_date = date(2014, 6, 9)

    # while start_date <= end_date:
    #     if start_date.weekday() < 5:
    #         date_str = start_date.strftime("%d-%m-%Y")
    #         if date_str not in missing_dates:
    #             dates.append(date_str)
    #     start_date += timedelta(days=1)

    threads = [DownloadingThread(d) for d in split(dates, 8)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    result = '\t'.join(fields) + '\n' + ''.join([t.result for t in threads])

    with open(f'santander-kursy-archiwalne.txt', 'w') as result_file:
        result_file.write(result)


    error_dates = sorted(error_dates, key=lambda row : row[6:10]+row[3:5]+row[0:2]+row[11:16])

    with open(f'error_dates.txt', 'w') as result_file:
        result_file.write('\n'.join(error_dates))
    
    print('\n'.join(error_dates))
