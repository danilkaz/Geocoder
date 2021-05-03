tag = '</way>'
index = 0
with open('Izhevsk', encoding='utf-8') as f:
    for line in f:
        if tag in line:
            index += 1
print(index)
