import json
import requests
import sys
from tqdm import tqdm
from datetime import date, timedelta


headers = {
  'authority': 'www.bph.pl',
  'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
  'accept': 'application/json, text/javascript, */*; q=0.01',
  'dnt': '1',
  'x-requested-with': 'XMLHttpRequest',
  'sec-ch-ua-mobile': '?0',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-mode': 'cors',
  'sec-fetch-dest': 'empty',
  'referer': 'https://www.bph.pl/pl/kursy-walut/',
  'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,pl;q=0.7',
  'cookie': '_ga=GA1.2.378626934.1630328712; _gid=GA1.2.1333736409.1630328712',
}

id = int(sys.argv[-1])
if id == 1:
    fields = ('buying', 'selling', 'spread')
    result = f'date\thour\t' + '\t'.join(fields) + '\n'
else:
    result = ''

dates = []

# designed for 8-threads executing
start_date = date(2006, 1, 1) + timedelta(days=715) * (id - 1)
end_date = start_date + timedelta(days=715)

if id == 8:
    end_date = date(2021,8, 27)

delta = timedelta(days=1)

dates = []
while start_date <= end_date:
    dates.append(start_date.strftime("%Y-%m-%d"))
    start_date += delta


for date in tqdm(dates):

    url = f'https://www.bph.pl/pi/api/currency/tw0/hours?date={date}'
    response = requests.get(url, headers=headers)

    if not response.content:
        result += f'{date}\n'
        continue

    times = json.loads(response.content)

    for time in times:
        url = f'https://www.bph.pl/pi/api/currency/tw0/currencies?date={date} {time}'
        response = requests.get(url, headers=headers)

        for record in json.loads(response.content):
            if record['currency'] == 'CHF':
                result += f"{date}\t{time}\t{record['buying']}\t{record['selling']}\t{record['spread']}\n"


with open(f"BPH-{id}.txt", "w") as result_file:
    result_file.write(result)
