fields = ('Data', 'Godzina', 'Kupno', 'Sprzedaż', 'Kurs średni NBP (FIXING)', 'W przeliczeniu 5000 USD*')
result = '\t'.join(fields) + '\n'

for i in range(1, 9):
    with open(f'getin-dewizy-{i}.txt') as file:
        dates = file.readlines()

    dates = ''.join(dates)
    with open("getin-dewizy.txt", "a") as result_file:
        result_file.write(dates)
