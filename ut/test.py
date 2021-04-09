import sqlite3
from sqlite3 import Error
import pandas as pd
from sqlalchemy import create_engine

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
#print (df)

import mysql.connector
from pandas.io import sql

import psycopg2
from sqlalchemy.orm import sessionmaker
def sqllite_to_postgres():
    engine = create_engine("postgresql://{user}:{pw}@localhost:9999/{db}"
                           .format(user="super",
                                   pw="admin_pqv34433_GAS",
                                   db="postgres"))
    df=pd.read_sql(sql="SELECT table_name as tbl_name FROM information_schema.tables WHERE " \
                       "table_name like 'ut_%%' and table_name not in ('ut_cache_table') /*and table_name not in ('ut_instances','ut_values') */ order by table_name",con=engine)
    #Session = sessionmaker(bind=engine)
    #session = Session()
    cur=engine
    cur.execute("SET session_replication_role = 'replica';")

    for i,r in df.iterrows():
        print ('disable triggers on {}'.format(r.tbl_name))
        cur.execute('ALTER TABLE public."{}" DISABLE TRIGGER ALL;'.format(r.tbl_name))

    for i,r in df.iterrows():
        print ('deleting triggers on {}'.format(r.tbl_name))
        cur.execute('delete from public."{}" where id>-100;'.format(r.tbl_name))


    for i,r in df.iterrows():
        print (r.tbl_name)
        try:
            pass
#            cur.execute ('alter table {} modify id int(11)'.format(r.tbl_name))
        except:
            pass
        table=pd.read_sql('select * from {}'.format(r.tbl_name),conn)
        table.loc[table.id==0,'id']=-1
        if r.tbl_name in ['ut_attributes','ut_inputtypes','ut_filters','ut_classes']:
            for c in table.columns:
                if c in ['Filtered','ReadOnly','ShowInTable','UniqueAtt','NotNullAtt',
                         'UseExternalTables','UseAutoCounter']:
                    table[c]=table[c].apply(lambda x: True if x==1 else False )
                if c in ['InputType_id','Ref_Class_id','Ref_Attribute_id','InternalAttribute_id',
                         'Attribute1_id','Attribute2_id','Attribute3_id','Class_id']:
                    table.loc[table[c]==0,c]=-1
        print (table.head(5))
        table.to_sql(con=engine, name=r.tbl_name, if_exists='append',chunksize=1000,index=False,method='multi')
#        cur.execute ('alter table {} modify id int(11) auto_increment, auto_increment = {}'.format(r.tbl_name,max(value_if_null(table.id.max(),0),0)+1))
        #cur.execute ('alter table {} modify id int(11) auto_increment'.format(r.tbl_name))
    cur.execute("SET session_replication_role = 'origin';")
    #session.commit()

    for i,r in df.iterrows():
        print ('enable triggers on {}'.format(r.tbl_name))
        cur.execute('ALTER TABLE public."{}" ENABLE TRIGGER ALL;'.format(r.tbl_name))

    for i, r in df.iterrows():
        id=pd.read_sql('select max(id) id from "{}"'.format(r.tbl_name),engine).id.max()
        cur.execute('ALTER SEQUENCE "{}_id_seq" RESTART WITH {}'.format(r.tbl_name,value_if_null(id,0)+1))

sqllite_to_postgres()

def sqlite_to_mysql():
    engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}"
                           .format(user="pfbox",
                                   pw="admin_pqv34433_GAS",
                                   db="pfbox$ut"))

    cur=engine
    cur.execute('SET FOREIGN_KEY_CHECKS=0;')

    for i,r in df.iterrows():
        print ('deleting from {}'.format(r.tbl_name))
        try:
            cur.execute('delete from {} where id>-100'.format(r.tbl_name))
        except:
            print ('could not delete {}'.format(r.tbl_name))
            pass

    for i,r in df.iterrows():
        print (r.tbl_name)
        try:
            cur.execute ('alter table {} modify id int(11)'.format(r.tbl_name))
        except:
            pass
        table=pd.read_sql('select * from {}'.format(r.tbl_name),conn)
        table.loc[table.id==0,'id']=-1
        if r.tbl_name in ['ut_attributes','ut_inputtypes','ut_filters']:
            for c in table.columns:
                if c in ['InputType_id','Ref_Class_id','Ref_Attribute_id','InternalAttribute_id',
                         'Attribute1_id','Attribute2_id','Attribute3_id','Class_id']:
                    table.loc[table[c]==0,c]=-1
        print (table.head(5))
        table.head(100).to_sql(con=engine, name=r.tbl_name, if_exists='append',index=False)
        cur.execute ('alter table {} modify id int(11) auto_increment, auto_increment = {}'.format(r.tbl_name,max(value_if_null(table.id.max(),0),0)+1))
        #cur.execute ('alter table {} modify id int(11) auto_increment'.format(r.tbl_name))
    cur.execute('SET FOREIGN_KEY_CHECKS=1;')


