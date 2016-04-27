from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

db_url = 'postgresql+psycopg2://bidder:bidder@localhost:5432/basketball'
Engine = create_engine(db_url, echo=False)
SessionMaker = sessionmaker(bind=Engine, autoflush=False)
Session = scoped_session(SessionMaker)

Base = declarative_base()


FOUR_FACTORS_TEAMS = FOUR_FACTORS_PLS = [ 
					                       'EFGP',
					                       'TOVP',
					                       'ORBP',
					                       'FT_to_FGA',
					                     ]


CRITICAL_FACTORS_TEAMS = CRITICAL_FACTORS_PLS = FOUR_FACTORS_TEAMS + ['ORtg', 'DRtg']


ALL_METRICS_TEAMS = [  
                       'MP',
                       'FG',
                       'FGA',
                       'PTS',
                       'TWO',
                       'TWOA',
                       'THR',
                       'THRA',
                       'FT',
                       'FTA',
                       'PACE',
                       'ORB',
                       'DRB',
                       'TRB',
                       'AST',
                       'STL',
                       'BLK',
                       'TOV',
                       'PF',
                       'ORBP',
                       'DRBP',
                       'TRBP',
                       'ASTP',
                       'STLP',
                       'BLKP',
                       'TOVP',
                       'USGP',
                       'ORtg',
                       'DRtg',
                       'FGP',
                       'TWOP',
                       'TWOAr',
                       'THRP',
                       'THRAr',
                       'FTP',
                       'FTAr',
                       'FT_to_FGA',
                       'EFGP',
                       'TSA',
                       'TSP',
                       'FIC',
                       'ORBr',
                       'DRBr',
                       'AST_to_TOV',
                       'STL_to_TOV',
                       'PLUS_MINUS',
                    ]



ALL_METRICS_PLS = [  
                       'MP',
                       'FG',
                       'FGA',
                       'PTS',
                       'TWO',
                       'TWOA',
                       'THR',
                       'THRA',
                       'FT',
                       'FTA',
                       'ORB',
                       'DRB',
                       'TRB',
                       'AST',
                       'STL',
                       'BLK',
                       'TOV',
                       'PF',
                       'ORBP',
                       'DRBP',
                       'TRBP',
                       'ASTP',
                       'STLP',
                       'BLKP',
                       'TOVP',
                       'USGP',
                       'ORtg',
                       'DRtg',
                       'PLUS_MINUS',
                       'FGP',
                       'TWOP',
                       'TWOAr',
                       'THRP',
                       'THRAr',
                       'FTP',
                       'FTAr',
                       'FT_to_FGA',
                       'EFGP',
                       'TSA',
                       'TSP',
                       'FIC',
                       'ORBr',
                       'DRBr',
                       'AST_to_TOV',
                       'STL_to_TOV',
                    ]