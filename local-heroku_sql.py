import pandas as pd
import psycopg2
from sqlalchemy import create_engine


# Heroku Postgresのコンフィグ
connection_config = {
    'host': 'ec2-54-210-128-153.compute-1.amazonaws.com',
    'database': 'd5evq9s0k3ah3p',
    'user': 'tdmhdafruvebzx',
    'port': '5432',
    'password': '2b49dd7bf409cc17dfd288cf43faf04eef06e800e17fe2cab498191ac8b6373e'
}
global engine
engine = create_engine(
    'postgres://tdmhdafruvebzx:2b49dd7bf409cc17dfd288cf43faf04eef06e800e17fe2cab498191ac8b6373e@ec2-54-210-128-153.compute-1.amazonaws.com:5432/d5evq9s0k3ah3p'.
        format(**connection_config))
#sr = pd.Series('category':[[2],[3],[4]])

# PostgreSQLに接続する
con = psycopg2.connect(**connection_config)


# 事前にローカルSQLからCSV出力後、Heroku Postgresに読み込ませる
df = pd.read_csv('market.csv')
df.to_sql('market', con=engine, if_exists='append',# or replace
          index=False)

df = pd.read_csv('atklist4.csv')
df.to_sql('atklist4',con=engine, if_exists='append',# or replace
          index=False)


