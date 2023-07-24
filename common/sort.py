FILENAME = 'x.txt'
START_LINE_NUM = 4
# SORT_ROW_FIRST_LETTERS = 10     # 2011-07-11
# SORT_ROW_FIRST_LETTERS = 16     # 2011-07-11 07:00
SORT_ROW_FIRST_LETTERS = 18     # 2011-07-11 07:00 1

# --------------------------------------------------


NEWFILENAME = FILENAME[:FILENAME.rfind(
    '.')] + '-sorted' + FILENAME[FILENAME.rfind('.'):]

header = ''
data_rows = []


with open(FILENAME, 'r') as file:

    i = 0
    for line in file.readlines():
        i += 1

        if i < START_LINE_NUM:
            header += line
        else:
            data_rows.append(line)

data_rows = set(data_rows)
sorted_rows = sorted(data_rows, key=lambda row: row[:SORT_ROW_FIRST_LETTERS])

with open(NEWFILENAME, 'w') as result_file:
    result_file.write(header + ''.join(sorted_rows))
