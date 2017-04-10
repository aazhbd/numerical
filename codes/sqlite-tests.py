import time
import sqlite3
import click

from random import randint

@click.command()
@click.option('--database', default='mydb.db', help='Opens the sqlite connection on filename')
@click.option('--table', default='test', help='Creates the table in sqlite')
@click.option('--insert', default='10', help='Operation options are, get, create, delete')
def main(database, table, insert):
    """CLI tool to analyze SQLite3"""
    database = database.lower()
    table = table.lower()
    insert = insert.lower()
    click.echo('Database name is : %s' % database)
    click.echo('Table name is : %s' % table)
    click.echo('number of rows name is : %s' % insert)
    start = time.time()
    db = DbTest(database)
    db.createTable(table)
    db.insertData(insert)
    db.showValues()
    db.showStatus()
    end = time.time()
    click.echo("Time taken : " + str(end - start))


class DbTest:
    def __init__(self, db_name):
        self.con = sqlite3.connect(db_name)
        self.cur = self.con.cursor()
        print("Connected.")
    
    def createTable(self, table_name):
        self.table_name = table_name
        try:
            self.cur.execute("create table " + str(self.table_name) + " (a, b)")
        except:
            print("Table exists.")
            return
        print("Table created.")
    
    def showStatus(self):
        print(self.cur.fetchone())
    
    def insertData(self, rows):
        for r in range(0, int(rows)):
            self.cur.execute("insert into " + str(self.table_name) + " (a, b) values(" + str(randint(0,9)) + ", " + str(randint(0,9)) + ")")
        
        print("Values added. " + str(rows))
    
    def showValues(self):
        self.cur.execute("select * from " + str(self.table_name))
        print(self.cur.fetchall())


if __name__ == '__main__':
    main()
