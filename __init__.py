from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

db_url = 'postgresql+psycopg2://bidder:bidder@localhost:5432/football'
Engine = create_engine(db_url, echo=False)
SessionMaker = sessionmaker(bind=Engine, autoflush=False)
Session = scoped_session(SessionMaker)

Base = declarative_base()
