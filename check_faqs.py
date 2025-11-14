import pymysql

conn = pymysql.connect(host='localhost', user='root', database='chatbot_db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM faqs')
result = cursor.fetchone()
print('Total FAQs:', result[0])

cursor.execute('SELECT question, answer FROM faqs LIMIT 5')
print('Sample FAQs:')
for row in cursor.fetchall():
    print('Q:', row[0][:50] + '...', 'A:', row[1][:50] + '...')

conn.close()
