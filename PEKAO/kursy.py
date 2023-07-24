import json
import requests
from requests.models import Response
from tqdm import tqdm
from datetime import date, timedelta


fields = ('Data', 'Godzina', 'Kupno', 'Sprzedaż', 'Spread')
result = '\t'.join(fields) + '\n'

dates = []
start_date = date(2006, 1, 1)
# end_date = date(2013, 11, 30)
# start_date = date(2013, 12, 1)
end_date = date(2021, 9, 10)
delta = timedelta(days=1)

while start_date <= end_date:
    dates.append(start_date.strftime("%Y-%m-%d"))
    start_date += delta


def get_data(date_requested, table=1):
    url = f'https://www.pekao.com.pl/.currencies/file?type=TEXT&source=PEKAO&date={date_requested}&table={table}'

    headers = {
        'Connection': 'keep-alive',
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 500:
        if table == 1:
            return f'{date_requested}\n'
        else:
            return f''
    
    for line in response.content.decode('utf-8').split('\r\n'):
        if line.startswith('TABELA KURSOWA'):
            hour = line[-5:]
            date = f'{line[-10:-6]}-{line[-13:-11]}-{line[-16:-14]}'
            continue
        if line[:3] == '797':
            values = list(filter(None, line.split(' ')))
            break
    
    return f'{date}\t{hour}\t{values[-4]}\t{values[-3]}\t{values[-2]}\n'

for date_requested in tqdm(dates):
    # result += get_data(date_requested, 1)
    # result += get_data(date_requested, 2)
    result += get_data(date_requested, 4)

# print(result)

with open("uzup.txt", "w") as result_file:
# with open("Tabela kursowa Banku Pekao S.A.txt", "w") as result_file:
    result_file.write(result)
