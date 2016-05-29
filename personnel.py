import datetime
from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, Date, UniqueConstraint, \
                    or_, and_
from sqlalchemy.orm import relationship
import numpy as np

from . import Session, Base
from overview import Match, League
from stats import PlayerMatchStats, PlayerSeasonStats, PlayerSeasonHomeStats, PlayerSeasonAwayStats


class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    birth_date = Column(Date, nullable=True)
    country_id = Column(ForeignKey('countries.id'), nullable=True, index=True)
    country = relationship('Country', backref='players')
    position = Column(String, nullable=True)
    teams = relationship('Team', secondary='contracts')
    number = Column(Integer)
    height = Column(Numeric)
    weight = Column(Numeric)
    experience = Column(Numeric)
    #first_year_ncaa = Column(Integer, nullable=True)

    UniqueConstraint(name, birth_date, college_id)
  
    def __repr__(self):
        return 'Player({0}, {1}, {2}, {3})'.format(self.id, self.name, 
                self.birth_date, self.position)

    def season_stats(self, season, date=None, measure='mean', metrics='critical',
                        loc='all', type_='all', per36=False, complete=False):
        """
        return season's averages for all the stats
        """
        if not date:
            date = self.last_match(season).date

        if loc == 'all':
            table = PlayerSeasonStats
        elif loc == 'home':
            table = PlayerSeasonHomeStats
        elif loc == 'away':
            table = PlayerSeasonAwayStats

        stats = Session.query(table).join(table.league
                ).filter(League.season == season).filter(table.date == date
                ).filter(table.player == self).first()

        # calculate player season stats up to date
        if metrics == 'critical':
            factors = metrics = ['EFGP', 'TOVP', 'ORBP', 'FT_to_FGA', 'DRBP']
            stats = [getattr(stats, m) for m in factors]
        elif metrics == 'raw':
            metrics = RAW_STATS
            stats = [getattr(stats, s) for s in RAW_STATS]
        
        if complete:
            stats = dict(zip(metrics, stats))
        return stats

    def form(self, season, date=None, measure='mean',  metrics='critical', loc='all'):
        """
        calculates stats produced for the last five matches
        """
        pass

    def wins_produced(self, date=None):
        if not date:
            date = datetime.date.today()        

    def mins_played(self, date=None):
        """
        minutes played per day by the player in the 15 days previous to date
        """
        if not date:
            date = datetime.date.today()
        MP = Session.query(PlayerMatchStats.MP).join(PlayerMatchStats.match 
                  ).filter(PlayerMatchStats.player == self).filter(Match.date < date
                  ).filter(Match.type == 'Post-Season').all()
        return sum([min[0] for min in MP if min[0]]) / 15

    def rest_period(self, date=None):
        """
        calculate days passed since player last match
        """
        if not date:
            date = datetime.date.today()
        rv = Session.query(PlayerMatchStats).join(PlayerMatchStats.match 
                  ).filter(PlayerMatchStats.player == self).filter(Match.date < date
                  ).order_by(Match.date.desc()).first()
        last_match_date = rv.match.date
        return (date - last_match_date)

    def last_match(self, season):
        """
        returns last match played by team in given season
        """
        match = Session.query(Match).join(Match.league).join(Match.players_stats
                ).filter(PlayerMatchStats.player == self).filter(League.season == season
                ).filter(Match.type == 'Season').order_by(Match.date.desc()).first()
        return match

    def prev_match(self, season, date):
        """
        returns the immediate match played by player in season before date
        """
        match = Session.query(Match).join(Match.players_stats
                ).join(Match.league).filter(PlayerMatchStats.player == self
                ).filter(League.season == season).filter(Match.date < date
                ).order_by(Match.date.desc()).first()
        return match


class Official(Base):
    __tablename__ = 'officials'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    birth_date = Column(Date, nullable=True)
    country_id = Column(ForeignKey('countries.id'), nullable=True, index=True)
    country = relationship('Country', backref='officials')
    #matches = relationship('Match', secondary='matches_officials', backref='officials')


class Contract(Base):
    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey('players.id'), index=True)
    player = relationship('Player', backref='contracts')
    team_id = Column(ForeignKey('teams.id'), index=True)
    team = relationship('Team', backref='contracts')
    starts = Column(Date, nullable=True)
    ends = Column(Date, nullable=True)
    wage = Column(Integer, nullable=True)


class PlayersInjuries(Base):
    __tablename__ = 'players_injuries'

    id = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey('players.id'), index=True)
    player = relationship('Player', backref='injuries')
    description = Column(String)
    starts = Column(Date)
    ends = Column(Date)
