import json
import requests
from tqdm import tqdm
from datetime import date, datetime, timedelta


fields = ('foreignExchangeBuy', 'foreignExchangeSale', 'moneyBuy', 'moneySale')
result = f'date\thour\t' + '\t'.join(fields) + '\n'

headers = {
    'Connection': 'keep-alive',
    'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
    'Accept': 'application/json, text/plain, */*',
    'DNT': '1',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJzY29wZSI6ImludmVzdG1lbnRGdW5kcyIsImNmZyI6IiJ9.sbVFtlSE_455K4ijLgzFc9HQ62DbtqxOAiEyPCGyFAI',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://www.bankmillennium.pl/o-banku/serwis-ekonomiczny/kursy-walut',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,pl;q=0.7',
    'Cookie': 'JSESSIONID=14BF820F953004FD17DAB5411CBC3315; uuid-user-audit=ca1031c7-dfdf-4898-b110-d67a4623293a; _gcl_au=1.1.946764876.1630152281; _gid=GA1.2.1855644831.1630152282; Marketing_consent=1; PSESSIONID=42DA43D3C0FEF30F81CCEA3731FF4C1C; LB_bank_cookie=\u0021zZ0mPBKHPPIPsuu9LesOLImnjhqSYwz6iyx/ur0O/rkRW+dTgD7za+3gTljkNTJ1Ey6X2eMr8MzU2gc=; _ga_DJ8B9NM8HM=GS1.1.1630230399.4.0.1630230399.60; _ga=GA1.2.1746713548.1630152282; _dc_gtm_UA-51105080-1=1; _dc_gtm_UA-51105080-3=1; _dc_gtm_UA-51105080-4=1; _dc_gtm_UA-51105080-5=1; XSRF-Token=68616071-dfb1-4ebb-95d0-3de4ff6aebc9; _gat_UA-51105080-1=1',
}

# with open('daty.txt') as file:
#     dates = file.readlines()
#     dates = [line.rstrip() for line in dates]
dates = []

start_date = date(2006, 1, 1)
end_date = date(2021, 8, 29)
delta = timedelta(days=1)

while start_date <= end_date:
    dates.append(start_date.strftime("%d-%m-%Y"))
    start_date += delta


for date_requested in tqdm(dates):

    date_requested_YYYYMMDD = datetime.strptime(date_requested, '%d-%m-%Y').strftime('%Y-%m-%d')

    url = f'https://www.bankmillennium.pl/portal-apps/getFxRates?date={date_requested}&language=pl'

    response = requests.get(url, headers=headers)
    x = json.loads(response.content)

    if x == []:
        result += date_requested_YYYYMMDD + '\n'
        continue

    for record in x:
        timestamp = record['timeStamp'] // 1000
        dt_object = datetime.fromtimestamp(timestamp)
        date_from_timestamp = dt_object.strftime('%Y-%m-%d')
        hour_from_timestamp = dt_object.strftime('%H:%M')

        if date_from_timestamp != date_requested_YYYYMMDD:
            print('ERROR')
            exit()

        for single in record['items']:
            if single['symbol'] == '797/CHF':
                result += date_from_timestamp + '\t'
                result += hour_from_timestamp + '\t'
                for field in fields:
                    result += f'{single[field]}\t'
                result += '\n'


with open("Result.txt", "w") as result_file:
    result_file.write(result)

print(result)
