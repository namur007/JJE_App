from requests_oauthlib import OAuth1Session

from JJE_Standings.models import YahooKey, YahooStanding
from JJE_Waivers.models import YahooTeam

from JJE_Standings.utils.yahoo_api import refresh_yahoo_token

from bs4 import BeautifulSoup
from datetime import datetime
import math


def create_session():
    refresh_yahoo_token()
    token = YahooKey.objects.first() #type: YahooKey
    yahoo_obj = OAuth1Session(token.consumer_key,
                              client_secret=token.consumer_secret,
                              resource_owner_key=token.access_token,
                              resource_owner_secret=token.access_secret_token)
    return yahoo_obj


def build_team_data():
    yahoo_obj = create_session()
    url = "http://fantasysports.yahooapis.com/fantasy/v2/league/nhl.l.48844/standings"
    result = yahoo_obj.get(url)
    results, status_code = result.text, result.status_code
    if (result.text is None) or (result.status_code != 200):
        'Means an error with the yahoo stuff'
        return False

    standings_soup = BeautifulSoup(result.text, 'html.parser')
    teams = standings_soup.findAll('team')
    for team in teams:
        _process_team(team)


def update_standings():
    yahoo_obj = create_session()
    set_standings_not_current()
    _standings_collection(yahoo_obj)


def set_standings_not_current():
    for item in YahooStanding.objects.all():
        item.current_standings = False
        item.save()


def _standings_collection(yahoo_obj):
    try:
        # yahoo_obj = OAuth1Session()
        url = "http://fantasysports.yahooapis.com/fantasy/v2/league/nhl.l.48844/standings"

        result = yahoo_obj.get(url)
        results, status_code = result.text, result.status_code
        if (result.text is None) or (result.status_code != 200):
            'Means an error with the yahoo stuff'
            return False

        standings_soup = BeautifulSoup(result.text, 'html.parser')
        team_list = league_standings(standings_soup)

        return True
    except Exception as e:
        print(e)


def league_standings(xml_data=None):
    """
    Pass the xmlData in AS a beautiful soup object
    team_list is a series of model objects that can be saved on return
    """
    team_list = []
    teams = xml_data.findAll('team')
    for team in teams:
        team_class, new_team = _process_team(team)
        standings_class = _process_standings(team_class, team, team_class.team_id)
        team_list.append({'team': team_class, 'standings': standings_class, 'new_team': new_team})
    return team_list


def _process_team(team_row_xml):
    new_team = False
    # get the team id
    team_id = team_row_xml.find('team_id').text
    # Check if exists in the db
    team_class = YahooTeam.objects.filter(team_id=team_id).first()

    # If it doesn't exist then make a new one -> won't return None if it exists
    if team_class is None:
        new_team = True
        team_class = YahooTeam()

    team_class.team_id = team_row_xml.find('team_id').text
    team_class.team_name = team_row_xml.find('name').text
    team_class.logo_url = team_row_xml.find('team_logo').find('url').text

    manager = team_row_xml.find('manager')
    team_class.manager_name = manager.find('nickname').text
    team_class.manager_email = manager.find('email').text
    team_class.manager_guid = manager.find('guid').text

    team_class.save()

    return [team_class, new_team]


def _process_standings(team_class, team_row_xml, team_id):
    standings_class = YahooStanding()

    standings_class.team = team_class

    standings_class.rank = _process_rank(team_row_xml)

    standings_class = _process_team_stats(standings_class, team_row_xml)
    standings_class = _process_team_points(standings_class, team_row_xml)

    starting_week = datetime.strptime("2016-10-03 00:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
    standings_class.standings_week = math.floor(((datetime.utcnow() - starting_week).days / 7))

    standings_class.current_standings = True

    standings_class.save()

    return standings_class


def _process_team_stats(standings_class=None, team_row_xml=None):
    stats_rows = team_row_xml.find('team_stats').find('stats')
    standings_class.stat_1 = _stat_value(stats_rows.find('stat_id', text="1"))
    standings_class.stat_2 = _stat_value(stats_rows.find('stat_id', text="2"))
    standings_class.stat_3 = _stat_value(stats_rows.find('stat_id', text="3"))
    standings_class.stat_4 = _stat_value(stats_rows.find('stat_id', text="4"))
    standings_class.stat_5 = _stat_value(stats_rows.find('stat_id', text="5"))
    standings_class.stat_8 = _stat_value(stats_rows.find('stat_id', text="8"))
    standings_class.stat_12 = _stat_value(stats_rows.find('stat_id', text="12"))
    standings_class.stat_31 = _stat_value(stats_rows.find('stat_id', text="31"))
    standings_class.stat_19 = _stat_value(stats_rows.find('stat_id', text="19"))
    standings_class.stat_22 = _stat_value(stats_rows.find('stat_id', text="22"))
    standings_class.stat_23 = _stat_value(stats_rows.find('stat_id', text="23"))
    standings_class.stat_25 = _stat_value(stats_rows.find('stat_id', text="25"))
    standings_class.stat_24 = _stat_value(stats_rows.find('stat_id', text="24"))
    standings_class.stat_26 = _stat_value(stats_rows.find('stat_id', text="26"))
    standings_class.stat_27 = _stat_value(stats_rows.find('stat_id', text="27"))
    return standings_class


def _process_team_points(standings_class=None, team_row_xml=None):
    points_row = team_row_xml.find('team_points')

    try:
        point_total = float(points_row.find('total').text)
    except:
        point_total = 0.0

    standings_class.stat_point_total = point_total
    stats_rows = points_row.find('stats')
    standings_class.stat_points_1 = _stat_value(stats_rows.find('stat_id', text="1"))
    standings_class.stat_points_2 = _stat_value(stats_rows.find('stat_id', text="2"))
    standings_class.stat_points_3 = _stat_value(stats_rows.find('stat_id', text="3"))
    standings_class.stat_points_4 = _stat_value(stats_rows.find('stat_id', text="4"))
    standings_class.stat_points_5 = _stat_value(stats_rows.find('stat_id', text="5"))
    standings_class.stat_points_8 = _stat_value(stats_rows.find('stat_id', text="8"))
    standings_class.stat_points_12 = _stat_value(stats_rows.find('stat_id', text="12"))
    standings_class.stat_points_31 = _stat_value(stats_rows.find('stat_id', text="31"))
    standings_class.stat_points_19 = _stat_value(stats_rows.find('stat_id', text="19"))
    standings_class.stat_points_22 = _stat_value(stats_rows.find('stat_id', text="22"))
    standings_class.stat_points_23 = _stat_value(stats_rows.find('stat_id', text="23"))
    standings_class.stat_points_25 = _stat_value(stats_rows.find('stat_id', text="25"))
    standings_class.stat_points_24 = _stat_value(stats_rows.find('stat_id', text="24"))
    standings_class.stat_points_26 = _stat_value(stats_rows.find('stat_id', text="26"))
    standings_class.stat_points_27 = _stat_value(stats_rows.find('stat_id', text="27"))
    return standings_class


def _process_rank(team_row):
    team_standings = team_row.find('team_standings')
    try:
        rank = float(team_standings.find("rank").text)
    except:
        rank = 0.0
    return rank


def _stat_value(stat_row):
    try:
        value = float(stat_row.parent.find('value').text)
    except:
        value = 0.0
    return value
