# fields = ('buying', 'selling', 'spread')
# result = f'date\thour\t' + '\t'.join(fields) + '\n'
result = ''

for i in range(1, 9):
    with open(f'BPH-{i}.txt') as file:
        dates = file.readlines()

    dates = ''.join(dates)
    with open("BPH.txt", "a") as result_file:
        result_file.write(dates)
