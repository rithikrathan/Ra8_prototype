lines = [
    'x:69',
    'y:420'
]

for line in lines:
    poss = line.find(':')
    key = line[:poss]
    value = line[poss+1:]
    print(f'{key}, => ({value})')
