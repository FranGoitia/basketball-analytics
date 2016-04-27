import os
import sys
sys.path.append(os.path.abspath('.'))

import datetime
from collections import defaultdict
from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, Date, Time, \
                       UniqueConstraint, create_engine, tuple_, or_, and_, func
from sqlalchemy.orm import relationship
import numpy as np 

from model import Session, Base, enums, CRITICAL_FACTORS_TEAMS, FOUR_FACTORS_TEAMS, \
            ALL_METRICS_TEAMS
from model.stats import TeamMatchStats, TeamSeasonStats, TeamSeasonHomeStats, TeamSeasonAwayStats
from libcommon.constants import RAW_STATS


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

    def season_stats(self, season, date=None, measure='mean', metrics='critical', 
                        loc='all', type_='all', complete=False):
        """
        return season's averages for all the asked stats
        """
        if not date:
            date = self.last_match(season).date

        n = Session.query(Match).join(Match.league).filter(League.season == season
                ).filter(or_(Match.home == self, Match.away == self)
                ).filter(Match.date <= date)
        if loc == 'all':
            table = TeamSeasonStats
        elif loc == 'home':
            n = n.filter(Match.home == self)
            table = TeamSeasonHomeStats
        elif loc == 'away':
            n = n.filter(Match.away == self)
            table = TeamSeasonAwayStats
        n = n.count()

        stats = Session.query(table).join(table.league
                ).filter(League.season == season).filter(table.date == date
                ).filter(table.team == self)
        stats_off = stats.filter(table.type == 'offense').first()
        stats_def = stats.filter(table.type == 'defense').first()

        # calculate team season stats up to date
        stats = None
        if metrics == 'critical':
            metrics = ['O_EFGP', 'O_FT_to_FGA', 'O_TOVP', 'O_ORBP', 
                       'D_EFGP', 'D_FT_to_FGA', 'D_TOVP', 'D_DRBP']
            off_factors = ['EFGP', 'FT_to_FGA', 'TOVP', 'ORBP']
            def_factors = ['EFGP', 'FT_to_FGA', 'TOVP']# , 'STLP', 'BLKP']
            critical_off = [getattr(stats_off, m) for m in off_factors]
            #critical_off += [stats_off.PLUS_MINUS / n]
            critical_def = [getattr(stats_def, m) for m in def_factors]
            critical_def += [stats_off.DRBP]
            stats = np.array(critical_off + critical_def)
        elif metrics == 'raw':
            metrics = RAW_STATS
            # sum all matches raw stats of team in season up to date
            stats = np.array([getattr(stats_off, s) for s in RAW_STATS])
        
        if complete:
            stats = dict(zip(metrics, stats))
        return stats

    def opp_season_stats(self, season, date=None, complete=False):
        """
        return opposition stats allowed up to date
        """
        if not date:
            date = self.last_match(season).date

        cols = [getattr(TeamSeasonStats, s) for s in RAW_STATS]
        opp_stats = Session.query(*cols).filter_by(team=self, date=date, type='defense').first()

        if complete:
            opp_stats = dict(zip(RAW_STATS, opp_stats))

        return opp_stats

    def form(self, season, date=None, loc='All', measure='mean', metrics='critical'):
        """
        calculates stats produced for the last five matches
        """
        pass

    def matches_played(self, date=None):
        """
        matches played by the team in the 7 days previous to date
        """
        if not date:
            date = Session.query(TeamMatchStats).join(TeamMatchStats.match
                            ).join(Match.league).filter(League.season == season
                            ).filter(TeamMatchStats.team == team).filter(Match.type == 'Season'
                            ).order_by(Match.date.desc()).first()
        matches = Session.query(TeamSeasonStats.MATCHES_PLAYED_7).filter_by(date=date, team=self).first()[0]
        
        return matches

    def rest_period(self, date=None):
        """
        calculate days passed since team last match
        """
        if not date:
            date = Session.query(Match.date).filter(or_(Match.home == self, 
                      Match.away == self)).filter(Match.date < date
                      ).order_by(Match.date.desc()).first()[0]
        return (date - last_match_date).days

    def record(self, season, date, loc='all'):
        """
        return team season record (W-D-L) as of date for type_ (home, away) matches
        """
        def reverse(loc):
            if loc == 'Home':
                return 'Away'
            elif loc == 'Away':
                return 'Home'

        loc = loc.capitalize()
        if loc in ['Home', 'Away']:
            col = Match.home if loc == 'Home' else Match.away
            wins = Session.query(Match).join(Match.league).filter(League.season == season
              ).filter(and_(col == self, Match.result == loc)
              ).filter(Match.date < date).count()
            losses = Session.query(Match).join(Match.league).filter(League.season == season
              ).filter(and_(col == self, Match.result == reverse(loc))
              ).filter(Match.date < date).count()
            return np.array([wins, losses])
        else:
            home_matches = self.record(season, date, 'Home')
            away_matches = self.record(season, date, 'Away')
            return home_matches + away_matches

    def last_results(self, date):
        """
        returns per of matches that were win in the last 15 days
        """
        matches = Session.query(Match).filter(or_(Match.home == self, 
                    Match.away == self)).filter(Match.date < (date - datetime.timedelta(days=15)))
        matches_played = matches.count()
        matches_won = matches.filter(or_(and_(Match.home == self, Match.result == 'Home'), 
                    and_(Match.away == self, Match.result == 'Away'))).count()
        return matches_won / matches_played

    def streak(self, season, date=None):
        """
        return consecutive won matches before date
        """
        if not date:
            date = Session.query(TeamMatchStats).join(TeamMatchStats.match
                            ).join(Match.league).filter(League.season == season
                            ).filter(TeamMatchStats.team == team).filter(Match.type == 'Season'
                            ).order_by(Match.date.desc()).first()

        streak = Session.query(TeamSeasonStats.STREAK).filter_by(date=date, team=self).first()[0]
        return streak

    def distance_traveled(self, date, match, criteria='week'):
        """
        returns distance traveled by team in last 15 days
        """
        if not date:
            date = Session.query(TeamMatchStats).join(TeamMatchStats.match
                            ).join(Match.league).filter(League.season == season
                            ).filter(TeamMatchStats.team == team).filter(Match.type == 'Season'
                            ).order_by(Match.date.desc()).first()

        dist = Session.query(TeamSeasonStats.DIST_7).filter_by(date=date, team=self).first()[0]
        return dist

    def last_match(self, season):
        """
        returns last match played by team in given season
        """
        match = Session.query(Match).join(Match.league).filter(League.season == season
                ).filter(or_(Match.home == self, Match.away == self)).filter(Match.type == 'Season'
                ).order_by(Match.date.desc()).first()
        return match

    def prev_match(self, season, date):
        """
        returns the immediate match played by team in season before date
        """
        match = Session.query(Match).filter(or_(Match.home == self, Match.away == self)
                ).filter(Match.date < date).order_by(Match.date.desc()).first()
        return match

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


class MatchBReferenceCode(Base):
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
    home_spread = Column(Numeric, nullable=True)
    home_spread_odds = Column(Numeric, nullable=True)
    away_spread = Column(Numeric, nullable=True)
    away_spread_odds = Column(Numeric, nullable=True)

