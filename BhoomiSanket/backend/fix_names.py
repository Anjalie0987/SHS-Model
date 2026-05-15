import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()
cur.execute("UPDATE latlon_suitability SET village_name = REPLACE(village_name, '<', 'A') WHERE village_name LIKE '%<%'")
conn.commit()
print('Fixed names')
