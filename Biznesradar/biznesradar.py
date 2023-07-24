import requests
from html_parser import HTMLTableParser
from tqdm import tqdm


fields = ('Data', 'Otwarcie', 'Max', 'Min', 'Zamknięcie')
result = '\t'.join(fields) + '\n'

headers = {
    'Connection': 'keep-alive',
    'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Referer': 'https://www.biznesradar.pl/notowania-historyczne/CHFPLN',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,pl;q=0.7',
    'Cookie': 'cookiedisc=1; APE_Cookie=%7B%22frequency%22%3A17%7D; _bruid=a7d2662246e22dd2e315a8bf62ba84c4; _gid=GA1.2.369586271.1631646562; _dc_gtm_UA-18972811-6=1; var_fbh=16; _ga=GA1.2.1254455649.1631232876; _ga_F42CM1YWLE=GS1.1.1631704262.6.1.1631704453.0',
}

for i in tqdm(reversed(range(1, 72))):
    url = f'https://www.biznesradar.pl/notowania-historyczne/CHFPLN,{i}'
    response = requests.get(url, headers=headers).content.decode('utf-8')

    p = HTMLTableParser()
    p.feed(response)

    for row in reversed(p.tables[0][1:]):
        date = f'{row[0][6:12]}-{row[0][3:5]}-{row[0][0:2]}'
        result += f'{date}\t{row[1]}\t{row[2]}\t{row[3]}\t{row[4]}\n'


print(result)


with open(f'biznesradar.txt', 'w') as result_file:
    result_file.write(result)
