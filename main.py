import sqlite3

connection = sqlite3.connect('test.db')

cursor = connection.cursor()

cursor.execute('CREATE TABLE IF NOT EXISTS test2 ([a:d] TEXT, [g.g] TEXT, [f-y] TEXT, [index] TEXT)')

cursor.execute('INSERT INTO test2 VALUES ("a", "b", "c", "d")')

cursor.execute('SELECT * FROM test2')

print(cursor.fetchall())