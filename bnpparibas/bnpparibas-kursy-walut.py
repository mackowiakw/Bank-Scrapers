import re
import requests
import threading
from html_parser import HTMLTableParser
from tqdm import tqdm
from datetime import date, timedelta


fields = ('Data', 'Godzina', 'Kod tabeli*', 'Nr tabeli', 'Kupno', 'Sprzedaż', 'Spread', 'Kurs średni banku')

missing_dates = ('2001-02-15', '2001-02-16', '2001-02-19', '2001-02-20', '2001-02-22', '2001-02-23', '2001-02-26', '2001-04-16', '2001-05-01', '2001-05-03', '2001-06-14', '2001-08-15', '2001-11-01', '2001-12-25', '2001-12-26', '2002-01-01', '2002-04-01', '2002-05-01', '2002-05-03', '2002-05-30', '2002-08-15', '2002-11-01', '2002-11-11', '2002-12-25', '2002-12-26', '2003-01-01', '2003-04-21', '2003-05-01', '2003-06-19', '2003-08-15', '2003-11-11', '2003-12-25', '2003-12-26', '2004-01-01', '2004-04-12', '2004-05-03', '2004-06-10', '2004-11-01', '2004-11-11', '2005-03-28', '2005-04-08', '2005-05-03', '2005-05-26', '2005-08-15', '2005-11-01', '2005-11-11', '2005-12-26', '2006-04-17', '2006-05-01', '2006-05-03', '2006-06-15', '2006-08-15', '2006-11-01', '2006-12-25', '2006-12-26', '2007-01-01', '2007-04-09', '2007-05-01', '2007-05-03', '2007-06-07', '2007-08-15', '2007-11-01', '2007-12-25', '2007-12-26', '2008-01-01', '2008-03-24', '2008-05-01', '2008-05-22', '2008-08-15', '2008-11-11', '2008-12-25', '2008-12-26', '2009-01-01', '2009-04-13', '2009-05-01', '2009-06-11', '2009-08-03', '2009-11-11', '2009-12-25', '2010-01-01', '2010-04-05', '2010-05-03', '2010-06-03', '2010-11-01', '2010-11-11', '2011-01-06', '2011-04-25', '2011-05-03', '2011-06-23',
                 '2011-08-15', '2011-11-01', '2011-11-11', '2011-12-26', '2012-01-06', '2012-04-09', '2012-05-01', '2012-05-03', '2012-06-07', '2012-08-15', '2012-11-01', '2012-12-25', '2012-12-26', '2013-01-01', '2013-04-01', '2013-05-01', '2013-05-03', '2013-05-30', '2013-08-15', '2013-11-01', '2013-11-11', '2013-12-25', '2013-12-26', '2014-01-01', '2014-01-06', '2014-04-21', '2014-05-01', '2014-06-19', '2014-08-15', '2014-11-11', '2014-12-25', '2014-12-26', '2015-01-01', '2015-01-06', '2015-04-06', '2015-05-01', '2015-05-04', '2015-05-05', '2015-06-04', '2015-11-11', '2015-12-25', '2016-01-01', '2016-01-06', '2016-03-28', '2016-05-03', '2016-05-26', '2016-08-15', '2016-11-01', '2016-11-11', '2016-12-26', '2017-01-06', '2017-04-17', '2017-05-01', '2017-05-03', '2017-06-15', '2017-08-15', '2017-11-01', '2017-12-25', '2017-12-26', '2018-01-01', '2018-04-02', '2018-05-01', '2018-05-03', '2018-05-31', '2018-08-15', '2018-11-01', '2018-12-25', '2018-12-26', '2019-01-01', '2019-04-22', '2019-05-01', '2019-05-03', '2019-06-20', '2019-08-15', '2019-11-01', '2019-11-11', '2019-12-25', '2019-12-26', '2020-01-01', '2020-01-06', '2020-04-13', '2020-05-01', '2020-06-11', '2020-11-11', '2020-12-25', '2021-01-01', '2021-01-06', '2021-04-05', '2021-05-03', '2021-06-03')

URL = 'https://www.bnpparibas.pl/kursy-walut?action=component_request.action&component.action=changeRates&component.id=3093332'

headers = {}


def getCodes(date):
    data = {
        'componentId' : '3093332',
        'ratesDate': date,
        'bankCode': 'bnp'
    }

    response = requests.post(URL, headers=headers, data=data)

    if response.status_code != 200:
        error_dates.append(date)
        return []

    codes = re.findall('value="\d+"', response.content.decode('utf-8'))
    codes = map(lambda x: x[7:-1], codes)
    codes = sorted(set(codes))
    return codes


def getRates(date, code):
    data = {
        'componentId' : '3093332',
        'ratesTable': code,
        'bankCode': 'bnp',
    }

    response = requests.post(URL, headers=headers, data=data).content.decode('utf-8')

    parser = HTMLTableParser()
    parser.feed(response)

    try:
        returned_date = re.search( '&quot;\d{4}-\d{2}-\d{2}&quot', response).group(0)[6:16]
        regex_res = re.search( f'<option selected="selected" value="{code}">\d+ \d\d:\d\d', response).group(0)
    except AttributeError:
        error_dates.append(date)
        return ''

    returned_time = regex_res[-5:]
    returned_tableNo = regex_res[regex_res.rfind('>')+1:-6]

    if returned_date != date:
        error_dates.append(date)
        return ''

    for row in parser.tables[0]:
        if row[1] == '1 CHF':
            return '\t'.join([date, returned_time, code, returned_tableNo] + row[2:6]) + '\n'

    return ''


class DownloadingThread(threading.Thread):
    def __init__(self, dates):
        super(DownloadingThread, self).__init__()
        self.dates = dates
        self.result = ''

    def run(self):
        for date in tqdm(self.dates):
            for code in getCodes(date):
                self.result += getRates(date, code)


def split(arr, n):
    k, m = divmod(len(arr), n)
    return (arr[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


if __name__ == '__main__':

    dates = []
    error_dates = []

    # with open('error-dates.txt') as file:
    # dates = file.readlines()
    # dates = [line.rstrip() for line in dates]

    start_date = date(2001, 2, 14)
    end_date = date(2021, 9, 21)

    while start_date <= end_date:
        if start_date.weekday() < 5:
            date_str = start_date.strftime("%Y-%m-%d")
            if date_str not in missing_dates:
                dates.append(date_str)
        start_date += timedelta(days=1)

    threads = [DownloadingThread(d) for d in split(dates, 16)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    result = '\t'.join(fields) + '\n' + ''.join([t.result for t in threads])

    with open(f'bnpparibas-kursy-walut.txt', 'w') as result_file:
        result_file.write(result)

    error_dates = sorted(error_dates)

    with open(f'error-dates-kursy-walut.txt', 'w') as result_file:
        result_file.write('\n'.join(error_dates))

    print('\n'.join(error_dates))
