import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()
# Fix potential NULLs or 'nan' strings in category columns
cur.execute("UPDATE latlon_suitability SET shs_category = 'Fair' WHERE shs_category IS NULL OR shs_category = 'nan'")
cur.execute("UPDATE wheat_shs_germination SET category = 'Fair' WHERE category IS NULL OR category = 'nan'")
cur.execute("UPDATE wheat_shs_booting SET category = 'Fair' WHERE category IS NULL OR category = 'nan'")
cur.execute("UPDATE wheat_shs_ripening SET category = 'Fair' WHERE category IS NULL OR category = 'nan'")
conn.commit()
print('Data cleaned successfully')
