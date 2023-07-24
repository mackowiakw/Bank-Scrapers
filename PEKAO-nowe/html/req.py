import requests
from bs4 import BeautifulSoup
from datetime import datetime

headers = {
    'Authority': 'www.pekao.com.pl',
    'Accept': 'text/html',
    'Accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,pl;q=0.7',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
}

ERROR_LABEL = 'error'


def getRates(date):

    url = f'https://www.pekao.com.pl/kursy-walut/lista-walut.html?pekaoDate={date}'
    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.content, 'html.parser')

    if response.status_code != 200:
        return {ERROR_LABEL: f"Failed to fetch the resource (HTTP status was code not 200)"}

    # <h2 class="">Tabela kursowa Banku Pekao S.A.</h2>
    # <p class="no-margin">Ostatnia aktualizacja: <span>02.12.2022</span> <span >07:00</span></p>
    h2 = soup.find("h2", string="Tabela kursowa Banku Pekao S.A.")
    p = h2.find_next_sibling("p")

    # 'Ostatnia aktualizacja: 14.10.2010 08:10'
    last_updated = p.text.split(' ')[2]

    if last_updated != datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y"):
        return {ERROR_LABEL: f"No course entries on this day"}

    # <select class="select-hide custom-list" name="exchangeTables" data-calendar-pekao-time data-custom-select>
    #   <option value="1">07:00</option>
    #   <option value="2">14:30</option>
    # </select>
    hours = soup.find("select", {"name": "exchangeTables"})
    entries_this_day = len(hours.find_all("option")) if hours else 1

    result = ''

    for num in range(1, 1 + entries_this_day):

        url = f'https://www.pekao.com.pl/.currencies/file?type=TEXT&source=PEKAO&date={date}&table={num}'

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return {ERROR_LABEL: f"Failed to fetch the resource (HTTP status was code not 200)"}

        for line in response.content.decode('utf-8').split('\r\n'):
            if line.startswith('TABELA KURSOWA'):
                tmp = line.split()
                table_number = tmp[3]
                table_date = f'{tmp[4][6:10]}-{tmp[4][3:5]}-{tmp[4][0:2]}'
                table_hour = tmp[5]
                continue

            if line.startswith('797   1:1   Szwajcaria'):
                values = line.split()
                kupno = values[4]
                sprzedaz = values[5]
                spread = values[6]
                symbol = values[7]
                break

        row = (table_date, table_hour, table_number,
               kupno, sprzedaz, spread, symbol)
        result += '\t'.join(row) + '\n'

    return {'data': result}


# x1 = getRates('2022-11-30')  # tylko 1 notowanie
# x2 = getRates('2022-12-01')  # 3 notowania
# x3 = getRates('2022-12-04')  # niedziela
x4 = getRates('2022-02-28')  # 7 notowań

print(x4['data'])
