import sqlalchemy

engine = sqlalchemy.create_engine('postgresql://postgres:postgres@localhost:5432/sspdim')
metadata = sqlalchemy.MetaData()

connection = engine.connect()

userinfo = sqlalchemy.Table('userinfo', metadata, autoload_with = engine)
servers = sqlalchemy.Table('servers', metadata, autoload_with = engine)