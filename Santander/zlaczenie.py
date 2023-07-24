fields = ('Data', 'Godzina', 'Nr tabeli', 'Kupno', 'Sprzedaż', 'Spread', 'Kurs średni Santander Bank Polska')
header = '\t'.join(fields) + '\n'

with open('error_dates-dewizy.txt') as file:
    error_dates = file.readlines()
    error_dates = [line.rstrip() for line in error_dates]

with open('santander-kursy-walut-dewizy-basic.txt') as file:
    basic_rows = file.readlines()
    basic_rows = [line.rstrip() for line in basic_rows]

for row in basic_rows:
    if row[:10] in error_dates:
        basic_rows.remove(row)

with open('santander-kursy-walut-dewizy-errors.txt') as file:
    additonal_rows = file.readlines()
    additonal_rows = [line.rstrip() for line in additonal_rows]

result_rows = basic_rows + additonal_rows
result_rows = sorted(result_rows, key=lambda row : row[6:10]+row[3:5]+row[0:2]+row[11:16])

with open('santander-kursy-walut.txt', 'w') as result_file:
    result_file.write(header + '\n'.join(result_rows))
