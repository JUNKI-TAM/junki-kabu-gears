import sqlite3

DATABASE = 'database.db'

def create_gears_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS gears (name,weight,price)")
    con.close()