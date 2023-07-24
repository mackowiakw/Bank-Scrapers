import json
import requests
from requests.models import Response
from html_parser import HTMLTableParser
from tqdm import tqdm
from datetime import date, timedelta


fields = ('Data', 'Kupno', 'Sprzedaż', 'Spread')
result = '\t'.join(fields) + '\n'

# with open('daty.txt') as file:
#     dates = file.readlines()
#     dates = [line.rstrip() for line in dates]
dates = []

# start_date = date(2006, 1, 1)
# end_date = date(2013, 10, 31)
start_date = date(2013, 11, 1)
end_date = date(2021, 8, 30)
delta = timedelta(days=1)

while start_date <= end_date:
    dates.append(start_date.strftime("%Y-%m-%d"))
    start_date += delta


def get_data(date_str):
    url = f'https://www.getinbank.pl/api/modules/exchange-rates/changeDate'

    POST_data = {
        'dateTime': f'{date_str} 23:59:59',  # '2021-08-11 23:59:59',
        'type': 'credits',  # 'money',
        'locale': 'pl',
        '_token': 'qUeiztl38uf2hahAoHekKcBirJ2zA56C8w9SPHn2',
    }

    headers = {
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
        'DNT': '1',
        'X-CSRF-TOKEN': 'qUeiztl38uf2hahAoHekKcBirJ2zA56C8w9SPHn2',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.getinbank.pl',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.getinbank.pl/kursy-walut',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,pl;q=0.7',
        'Cookie': 'salesmore_affId=GB; _gcl_au=1.1.1604492928.1630269990; _ga=GA1.2.1991368399.1630269990; _gid=GA1.2.1724256401.1630269990; _fbp=fb.1.1630269990131.1926157567; cookieInfo=1; XSRF-TOKEN=qUeiztl38uf2hahAoHekKcBirJ2zA56C8w9SPHn2; user_session=eyJpdiI6ImhXZVdzaWMra051cXpwZSsyR0pFTHc9PSIsInZhbHVlIjoibUNRY2VkWjFEZlwvVFZOYkxicjNsU2M2VXFZQ2FqS0N1aU5HV3NiZWJWVmpwcWpXdWJmbDdLQ1JhUFlnd3VyeXpBZkVmT2lkZHlpVHpwV3JCSHg5V3V3PT0iLCJtYWMiOiIzY2RhN2MxMGYxNzA4NTcxNzc1YTYwNTVjYmVkMDlkZWRiNzc0MGI2MzY5YWI5MDBjYzM0NTJhNWY2OGNhNDc0In0=; salesmore_tdpeh=kampania strona wnioski.getinbank.pl',
    }

    response = requests.post(url, headers=headers, data=POST_data).content.decode('utf-8')

    p = HTMLTableParser()
    p.feed(json.loads(response)['table'])

    for row in p.tables[0]:
        if row[0] == 'CHF':
            return f'{date_str}\t{row[1]}\t{row[2]}\t{row[3]}\n'


for date_requested in tqdm(dates):
    result += get_data(date_requested)

with open("getin-kredyty-2.txt", "w") as result_file:
    result_file.write(result)
