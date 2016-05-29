import os
import sys
sys.path.append(os.path.abspath('.'))

import datetime
from collections import defaultdict
from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, Date, Time, \
                       UniqueConstraint, create_engine, tuple_, or_, and_, func
from sqlalchemy.orm import relationship
import numpy as np 

from . import Session, Base, enums
from stats import TeamMatchStats, TeamSeasonStats, TeamSeasonHomeStats, TeamSeasonAwayStats


class Country(Base):
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return '%s' % (self.name,)


class City(Base):
    __tablename__ = 'cities'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    country_id = Column(ForeignKey('countries.id'), index=True)
    country = relationship('Country', backref='cities')
    teams = relationship('Team', secondary='cities_teams')

    UniqueConstraint(name, country_id)


class CityDistance(Base):
    __tablename__ = 'cities_distances'

    id = Column(Integer, primary_key=True)
    city1_id = Column(ForeignKey('cities.id'), nullable=False, index=True)
    city2_id = Column(ForeignKey('cities.id'), nullable=False, index=True)
    city1 = relationship('City', foreign_keys=[city1_id])
    city2 = relationship('City', foreign_keys=[city2_id])
    distance = Column(Numeric, nullable=False)


class CityTeam(Base):
    __tablename__ = 'cities_teams'

    id = Column(Integer, primary_key=True)
    city_id = Column(ForeignKey('cities.id'), index=True, nullable=False)
    team_id = Column(ForeignKey('teams.id'), index=True, nullable=False)


class Stadium(Base):
    __tablename__ = 'stadiums'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    country_id = Column(ForeignKey('countries.id'), nullable=True)
    country = relationship('Country', backref='stadiums')
    city_id = Column(ForeignKey('cities.id'), index=True)
    city = relationship('City', backref='stadiums')
    state = Column(String)
    address = Column(String)
    zipcode = Column(String)
    teams = relationship('Team', secondary='stadiums_teams')

    UniqueConstraint(name, country_id)

    def __repr__(self):
        #return '{name: %s, country: %s, local_teams: %s' % (self.name,
        #    self.country.name, [team.name for team in self.teams])
        return self.name


class StadiumTeam(Base):
    __tablename__ = 'stadiums_teams'

    id = Column(Integer, primary_key=True)
    stadium_id = Column(ForeignKey('stadiums.id'), index=True, nullable=False)
    team_id = Column(ForeignKey('teams.id'), index=True, nullable=False)


class League(Base):
    __tablename__ = 'leagues'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    season = Column(String, nullable=False)
    country_id = Column(ForeignKey('countries.id'), nullable=False, index=True)
    country = relationship('Country', backref='leagues', uselist=False)

    UniqueConstraint(name, season, country_id)

    def __repr__(self):
        return '{league: %s - %s, country: %s}' % (self.name, self.season, self.country)


class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    country_id = Column(ForeignKey('countries.id'), nullable=False, index=True)
    country = relationship('Country', backref='teams')
    cities = relationship('City', secondary='cities_teams')
    coast = Column(String)
    division = Column(String)
    players = relationship('Player', secondary='contracts')
    stadiums = relationship('Stadium', secondary='stadiums_teams')

    UniqueConstraint(name, country_id)

    def __repr__(self):
        return '{name: %s, country: %s}' % (self.name, self.country.name)


class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=True)
    city_id = Column(ForeignKey('cities.id'), nullable=True, index=True)
    city = relationship('City')
    league_id = Column(ForeignKey('leagues.id'), nullable=False, index=True)
    league = relationship('League', backref='matches')
    type = Column(enums.matches_types)
    home_id = Column(ForeignKey('teams.id'), nullable=False, index=True)
    home = relationship('Team', foreign_keys=[home_id], backref='home_matches')
    away_id = Column(ForeignKey('teams.id'), nullable=False, index=True)
    away = relationship('Team', foreign_keys=[away_id], backref='away_matches')
    stadium_id = Column(ForeignKey('stadiums.id'), nullable=True, index=True)
    stadium = relationship('Stadium', backref='matches')
    attendance = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    result = Column(String, nullable=False)

    UniqueConstraint(date, home_id, away_id)

    def __repr__(self):
        return '{date: %s, league: %s, home: %s, away: %s, result: %s}' \
                    % (self.date, self.league.name, self.home.name,
                            self.away.name, self.result)


class MatchSquawkaCode(Base):
    __tablename__ = 'matches_b_reference_codes'

    id = Column(Integer, primary_key=True)
    match_id = Column(ForeignKey('matches.id'), index=True, nullable=False)
    match = relationship('Match', backref='b_reference', uselist=False)
    code = Column(String, nullable=False)

    UniqueConstraint(match_id, code)

    def __repr__(self):
        return '{match: %s, code: %s}' % (str(self.match), self.code)


class MatchOdds(Base):
    __tablename__ = 'matches_odds'

    id = Column(Integer, primary_key=True)
    match_id = Column(ForeignKey('matches.id'), index=True, nullable=False)
    match = relationship('Match', backref='odds', uselist=False)
    home_odds = Column(Numeric, nullable=True)
    away_odds = Column(Numeric, nullable=True)
    draw_odds = Column(Numeric, nullable=True)
    home_spread = Column(Numeric, nullable=True)
    home_spread_odds = Column(Numeric, nullable=True)
    away_spread = Column(Numeric, nullable=True)
    away_spread_odds = Column(Numeric, nullable=True)

