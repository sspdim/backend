import sqlalchemy

engine = sqlalchemy.create_engine('postgresql://postgres:postgres@localhost:5432/sspdim')
metadata = sqlalchemy.MetaData()

connection = engine.connect()

userinfo = sqlalchemy.Table('userinfo', metadata, autoload_with = engine)
servers = sqlalchemy.Table('servers', metadata, autoload_with = engine)
tokens = sqlalchemy.Table('tokens', metadata, autoload_with = engine)
pending_friend_requests = sqlalchemy.Table('pending_friend_requests', metadata, autoload_with = engine)
pending_messages = sqlalchemy.Table('pending_messages', metadata, autoload_with = engine)
Keys = sqlalchemy.Table('keys', metadata, autoload_with = engine)