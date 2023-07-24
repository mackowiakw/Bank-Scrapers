from bs4 import BeautifulSoup
import requests
import re
import sys

headers = {
    'accept': 'application/json',
    # 'connection': 'keep-alive',
    # 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'cookie': 'salesmore_affid=GB; _gcl_au=1.1.910725504.1673008832; _ga=GA1.2.281154292.1673008833; _gid=GA1.2.1233159863.1673008833; cookieInfo=1; XSRF-TOKEN=dQ2BMgV2xJOkhPqhpaz8XOl7x6LXUTQUVWbk8jf2; _gat_UA-115307957-1=1; user_session=eyJpdiI6ImZ3eWEzMy9JTzl5SmEvU3UvZjNrRGc9PSIsInZhbHVlIjoiM2xNQUhVcXVWdFdhWC9jTHhDTmN0U3dodzU0Q0lGZlNkOUQyUy9kRVZWVzE3bGJDL2x2VjQyZ3hWSldSdWhqNHdMNEI0R05mYmpnQnRlL1VUMnFNak1qTmlPODBVa2RVSFVnWkpTRFVJdnBadzAxL2hNenFNVUp3eUF2dFJHOGIiLCJtYWMiOiI0NGNmM2JhMGQ0OTRmNzE1ZjA3MjNmZmFhM2FhNjAxMzY1OWNiN2YwNmJhNTJjODI5OWViNGE5ZGU5MjlmYzZiIiwidGFnIjoiIn0%3D; salesmore_tdpeh=kampania strona wnioski.velobank.pl; _gat_UA-33140607-1=1',
    'origin': 'https://www.velobank.pl',
    'referer': 'https://www.velobank.pl/kursy-walut',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'x-csrf-TOKEN': 'dQ2BMgV2xJOkhPqhpaz8XOl7x6LXUTQUVWbk8jf2',
    'x-requested-With': 'XMLHttpRequest',

    # 'connection': 'keep-alive',
}

date = '2023-01-13 10:00:59'


post_data = {
    'dateTime': date,
    'type': 'foreign',
    'locale': 'pl',
    '_token': 'dQ2BMgV2xJOkhPqhpaz8XOl7x6LXUTQUVWbk8jf2',
}

# url = f'https://www.bnpparibas.pl/kursy-walut?action=component_request.action&component.action=changeRates&component.id=3485195'
url = 'https://www.velobank.pl/api/modules/exchange-rates/changeDate'

response = requests.post(url, data=post_data, headers=headers)
print(response.status_code)

if not response.content:
    sys.exit('Empty response')

# data = response.json()

with open(f"{date.replace(':','-')}.html", 'w', encoding='utf-8') as f:
    # f.write(data['table'])
    f.write(response.content.decode('utf-8'))

sys.exit()

# soup = BeautifulSoup(response.content, 'html.parser')

# <h3 class="exchange_rates__header">Aktualna tabela kursowa nr <b>251a/22</b> z dnia: <b>29-12-2022</b></h3>
# dates_tmp = re.findall('\d\d\d\d-\d\d-\d\d', soup.find("div",
#    {"class": "configuration"}).attrs['data-configuration'])

# if len(dates_tmp) != 1:
# sys.exit('Błąd wyszukiwania daty')

# date = dates_tmp[0]

options = []
for option in soup.find("select", {"class": "table_select"}).find_all("option"):
    options.append(option['value'].strip())


bank_select = soup.find("select", {"class": "bank_select"})
if bank_select:
    banks = [b.attrs['value'] for b in bank_select.find_all("option")]
    print(banks)

    if 'bnp' in banks:
        banks.remove('bnp')
    if 'bgz' in banks:
        banks.remove('bgz')

    print(banks)

    if banks:
        print(f'{date} Found another bank: {banks}')
    else:
        print(f'{date} BGZ not downloaded')


print('status:', response.status_code)
print('----------')
print('date:', date)
print('----------')
# print(response.content)
# print('banks:', banks)
# if banks:
# print('bank:', bank_select.find("option", selected=True).attrs['value'])
print('----------')
print('options:', options)
