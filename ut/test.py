import sqlite3
from sqlite3 import Error
import pandas as pd

def value_if_null(x,val):
    if pd.isnull(x):
        return val
    else:
        return x


conn = sqlite3.connect('C:\TheProject\db.sqlite3')

ssql="""
SELECT name,tbl_name FROM sqlite_master
WHERE type='table' and name like 'ut_%' and name not in ('ut_cache_table','ut_instances','ut_values')
ORDER BY name;
"""
df=pd.read_sql(ssql,conn)

print (df)



import mysql.connector
from pandas.io import sql

mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="pfbox",
    password="admin_pqv34433_GAS",
    database = 'pfbox$ut'
)

from pandas.io import sql
import pymysql
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}"
                       .format(user="pfbox",
                               pw="admin_pqv34433_GAS",
                               db="pfbox$ut"))

cur=engine
cur.execute('SET FOREIGN_KEY_CHECKS=0;')

for i,r in df.iterrows():
    print ('deleting from {}'.format(r.tbl_name))
    cur.execute('delete from {} where id>-100'.format(r.tbl_name))

for i,r in df.iterrows():
    print (r.tbl_name)
    cur.execute ('alter table {} modify id int(11)'.format(r.tbl_name))
    table=pd.read_sql('select * from {}'.format(r.tbl_name),conn)
    table.loc[table.id==0,'id']=-1
    if r.tbl_name in ['ut_attributes','ut_inputtypes','ut_filters']:
        for c in table.columns:
            if c in ['InputType_id','Ref_Class_id','Ref_Attribute_id','InternalAttribute_id',
                     'Attribute1_id','Attribute2_id','Attribute3_id','Class_id']:
                table.loc[table[c]==0,c]=-1
    print (table)

    table.to_sql(con=engine, name=r.tbl_name, if_exists='append',index=False)
    cur.execute ('alter table {} modify id int(11) auto_increment, auto_increment = {}'.format(r.tbl_name,max(value_if_null(table.id.max(),0),0)+1))
    #cur.execute ('alter table {} modify id int(11) auto_increment'.format(r.tbl_name))

cur = mydb.cursor().execute('SET FOREIGN_KEY_CHECKS=1;')


