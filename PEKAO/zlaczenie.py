# fields = ('Data', 'Godzina', 'Kupno', 'Sprzedaż', 'Kurs średni NBP (FIXING)', 'W przeliczeniu 5000 USD*')
# result = '\t'.join(fields) + '\n'

result = ''

with open('Tabela kursowa Banku Pekao S.A.txt', 'r') as file:
    f1 = file.readlines()

with open("uzupełnienie.txt", "r") as file2:
    f2 = file2.readlines()


rr = f1 + f2

# print(len(f1))
# print(len(f2))
# print(len(rr))

rr = sorted(rr)

fields = ('Data', 'Godzina', 'Kupno', 'Sprzedaż', 'Spread')
xd = '\t'.join(fields) + '\n'

# print(rr)
with open("Tabela kursowa Banku Pekao S.A.txt", "w") as result_file:
    result_file.write(xd + ''.join(rr[:-2]))


