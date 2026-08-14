
import slite3
conn = slite3.connect('/app/data/webook.db')
c = conn.cursor()
c.execute("SELECT name FROM slite_master WHERE type='table'")
print(c.fetchall())
conn.close()
