"""
Setting up a pg database that contains this schema
    1. Create a new database in postgres called football
    2. Create a new user called bidder with password bidder
    3. Run create_db
"""

from sqlalchemy import create_engine
import enums
import overview
import personnel
import stats
import events
import Base, db_url

def create_db():
    Engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(Engine)


if __name__ == '__main__':
    create_db()
