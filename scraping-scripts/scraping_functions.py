import requests
from bs4 import BeautifulSoup
import time
import re

# ------------------------------------------------------------------
# Leagues Dictionary
# ------------------------------------------------------------------
all_leagues = {
	'premier-league' : 'GB1',
	'bundesliga' : 'L1',
	'serie-a' : 'IT1',
	'laliga' : 'ES1',
	'ligue-1' : 'FR1',
	'campeonato-brasileiro-serie-a' : 'BRA1'
}

# ------------------------------------------------------------------
# Request Function
# ------------------------------------------------------------------
def get_page(url, headers, retries=5):
    """
    Sends an HTTP GET request to a given URL and retries the request
    if the page is not successfully retrieved.

    The function attempts to access the requested page up to the specified
    number of retries. If a request returns HTTP status code 200, the
    response is immediately returned. Otherwise, the function waits
    three seconds before trying again.

    Parameters:
        url (str): URL of the page to be requested.
        headers (dict): HTTP headers used when sending the request.
        retries (int): Maximum number of request attempts. Defaults to 5.

    Returns:
        requests.Response: The successful response, or the response from
        the final attempt if all retries fail.
    """
    for attempt in range(retries):
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response

        time.sleep(3)
    # If every attempt fails, return the response from the final request
    return response

# ------------------------------------------------------------------
# All available scraping functions
# ------------------------------------------------------------------
def get_events(headers, league, n_season, n_round):
    """
    Extracts all match events from a specific league round on Transfermarkt.

    The function accesses the Transfermarkt matchday page for the selected
    league, season, and round. It collects the events registered for each
    match, including player information, event type, score at the time of
    the event, and the minute in which the event occurred.

    Parameters:
        headers (dict): HTTP headers used when sending the request.
        league (str): League identifier used in the Transfermarkt URL.
        n_season (int): Starting year of the season.
        n_round (int): Round number to be scraped.

    Returns:
        list: A list of dictionaries where each dictionary represents
        one match event.
    """
    # Build the Transfermarkt URL for the selected league, season, and round
    # Request the page and create a BeautifulSoup object for HTML parsing
    url = f'https://www.transfermarkt.com/{league}/spieltag/wettbewerb/{all_leagues[league]}/saison_id/{n_season}/spieltag/{n_round}'
    response = get_page(url, headers)
    soup = BeautifulSoup(response.content, "lxml")

    # Find the tables containing the matches from the selected round
    all_matches = soup.find_all('table',{'style':'border-top: 0 !important;'})

    # Create a unique identifier for the season
    season_id = f'{all_leagues[league]}-{n_season}'

    # Store all extracted match events
    output_list = []

    # Iterate through every match in the round
    for m, match in enumerate(all_matches):
        # Create a unique identifier for the match
        match_id = f'M-{n_season}-{n_round:02d}-{m+1:02d}'
        # Extract the URL of the match page
        match_url = match.find('td',{'class':'spieltagsansicht-ergebnis'}).find('a').get('href')

        # Find all rows containing events from the current match
        match_event = match.find_all('tr',{'class':'no-border spieltagsansicht-aktionen'})
        # Extract information from each event
        for event in match_event:
            # PLAYER INFORMATION

            # Extract the player's Transfermarkt URL
            player_url = event.find('td',{'class':'spieltagsansicht'}).find('a').get('href')
            # Extract the player ID from the end of the URL
            player_id = int(player_url.split('/')[-1])
            # Extract the player's name from the link title
            player_name = event.find('td',{'class':'spieltagsansicht'}).find('a').get('title')

            # EVENT INFORMATION

            # Identify the event type from the icon's CSS class
            event_type = event.find('span',{'class':'icons_sprite'}).get('class')[-1]
            # Check whether a score is associated with the event
            check = event.find('td',{'class':'zentriert hauptlink'})
            # Store the score when available
            event_score = None if check == None else check.string

            # EVENT TIME INFORMATION

            # Transfermarkt stores event times in different columns
            # depending on whether the event belongs to the home or away team
            home='links'
            away='rechts'

            # Helper function for extracting the time value from either column
            check = lambda x: event.find('td',{'class':f'zentriert no-border-{x}'}).string
            # Select the column containing the actual event time
            event_time_label = check(away) if check(home) == '\xa0' else check(home)

            # Remove the apostrophe and separate regular and stoppage time
            time_list = re.sub("[']",'', event_time_label).split('+')
            # Extract the regular match minute
            event_time_minute = int(time_list[0])
            # Extract stoppage time when available, otherwise default to zero
            event_time_extra = int(time_list[-1]) if len(time_list) > 1 else 0

            # Combine all extracted values into a single event record
            temp = {
                'season_id': season_id,
                'match_id': match_id,
                'match_url': match_url,
                'player_url': player_url,
                'player_id': player_id,
                'player_name': player_name,
                'event_type': event_type,
                'event_score': event_score,
                'event_time_label': event_time_label,
                'event_time_minute': event_time_minute,
                'event_time_extra': event_time_extra
            }

            # Add the event record to the final output
            output_list.append(temp)
    # Return all events extracted from the selected round
    return output_list

def get_matches(headers, league, n_season, n_round):
    """
    Extracts information about all matches from a specific league round
    on Transfermarkt.

    The function accesses the Transfermarkt matchday page for the selected
    league, season, and round. For each match, it collects information about
    the home and away teams, final result, match date, referee, attendance,
    kickoff time, and the corresponding Transfermarkt match URL.

    Parameters:
        headers (dict): HTTP headers used when sending the request.
        league (str): League identifier used in the Transfermarkt URL.
        n_season (int): Starting year of the season.
        n_round (int): Round number to be scraped.

    Returns:
        list: A list of dictionaries where each dictionary contains
        information about one match from the selected round.
    """
    # Build the Transfermarkt URL for the selected league, season, and round
    # Request the page and create a BeautifulSoup object for HTML parsing
    url = f'https://www.transfermarkt.com/{league}/spieltag/wettbewerb/{all_leagues[league]}/saison_id/{n_season}/spieltag/{n_round}'
    response = get_page(url, headers)
    soup = BeautifulSoup(response.content, "lxml")

    # Find all tables containing matches from the selected round
    all_matches = soup.find_all('table',{'style':'border-top: 0 !important;'})

    # CSS classes used to identify the home and away team cells
    home_team = 'hauptlink zentriert no-border-links no-border-rechts hide-for-small spieltagsansicht-wappen'
    away_team = 'hauptlink zentriert no-border-rechts no-border-links hide-for-small spieltagsansicht-wappen'

    # Create a unique identifier for the season
    season_id = f'{all_leagues[league]}-{n_season}'

    # Store the information extracted from each match
    output_list = []

    # Iterate through every match found in the round
    for m, match in enumerate(all_matches):
        # Create a unique identifier for the current match
        match_id = f'M-{n_season}-{n_round:02d}-{m+1:02d}'
        # Extract the URL of the individual match page
        match_url = match.find('td',{'class':'spieltagsansicht-ergebnis'}).find('a').get('href')

        # AWAY TEAM INFORMATION

        # Locate the cell containing the away team information
        away_team_info = match.find_all('td',{'class':away_team})
        # Extract the team's Transfermarkt URL
        away_team_url = away_team_info[0].find('a').get('href')
        # Extract the team ID from the Transfermarkt URL
        away_team_id = int(away_team_url.split('/')[-3])
        # Extract the official team name
        away_team_name = away_team_info[0].find('a').get('title')

        # HOME TEAM INFORMATION

        # Locate the cell containing the home team information
        home_team_info = match.find_all('td',{'class':home_team})
        # Extract the team's Transfermarkt URL
        home_team_url = home_team_info[0].find('a').get('href')
        # Extract the team ID from the Transfermarkt URL
        home_team_id = int(home_team_url.split('/')[-3])
        # Extract the official team name
        home_team_name = home_team_info[0].find('a').get('title')

        # Extract the final score of the match
        match_result = match.find('span',{'class':'matchresult finished'}).string

        # ADDITIONAL MATCH INFORMATION

        # Locate the cells containing date, referee, attendance, and time data
        match_info = match.find_all('td',{'class':'zentriert no-border'})

        # Extract the match date from the URL linked to the date
        match_day = match_info[0].find('a').get('href').split('/')[-1]
        # Extract the referee's name
        match_referee = match_info[1].find('a').string
        # Extract the attendance value as displayed on the page
        match_attendance = match_info[2].get_text().strip()
        # If match attendance is not null, remove the thousands separator and convert attendance to an integer
        if match_attendance:
            match_attendance = int(re.sub(r'[.]', '', match_attendance).split()[0])
        else:
            match_attendance = None
        # Extract the kickoff time text located after the match date link
        # Separate the kickoff time from its AM/PM period
        time_info = match_info[0].find('a').next_sibling.strip().removeprefix('-').strip().split(' ')
        match_time = time_info[0]
        match_time_period = time_info[-1]

        # Combine all extracted values into a single match record
        temp = {
            'season_id': season_id,
            'match_id': match_id,
            'match_url': match_url,
            'home_team_url': home_team_url,
            'home_team_id': home_team_id,
            'home_team_name': home_team_name,
            'match_result': match_result,
            'away_team_url': away_team_url,
            'away_team_id': away_team_id,
            'away_team_name': away_team_name,
            'match_day': match_day,
            'match_referee': match_referee,
            'match_attendance': match_attendance,
            'match_time': match_time,
            'match_time_period': match_time_period
        }

        # Add the current match record to the final output
        output_list.append(temp)
    # Return all matches extracted from the selected round
    return output_list

def get_placements(headers, league, n_season, n_round):
    """
    Extracts the league table standings for a specific round and season
    from Transfermarkt.

    The function accesses the standings page for the selected league,
    season, and round. For each team, it collects its current position,
    team information, matches played, wins, draws, losses, goals,
    goal difference, and total points.

    Parameters:
        headers (dict): HTTP headers used when sending the request.
        league (str): League identifier used in the Transfermarkt URL.
        n_season (int): Starting year of the season to be scraped.
        n_round (int): Round number used to retrieve the standings.

    Returns:
        list: A list of dictionaries where each dictionary contains
        the league-table information for one team after the selected round.
    """
    # Build the Transfermarkt standings URL for the selected league, season, and round
    # Request the page and create a BeautifulSoup object for HTML parsing
    url = f'https://www.transfermarkt.com/{league}/spieltagtabelle/wettbewerb/{all_leagues[league]}/saison_id/{n_season}/spieltag/{n_round}'
    response = get_page(url, headers)
    soup = BeautifulSoup(response.content, "lxml")

    # Locate the tables containing the league standings
    # Extract all rows from the main standings table
    all_info = soup.find_all('table',{'class':'items'})
    table_info = all_info[0].find_all('tr')

    # Create a unique identifier for the selected league and season
    season_id = f'{all_leagues[league]}-{n_season}'

    # Store the standings information for all teams
    output_list = []

    # Skip the first row because it contains the table headers,
    # then process each team according to its current table position
    for i, row in enumerate(table_info[1:]):
        # TEAM INFORMATION

        # Locate the cell containing the team's name and profile link
        team_info = row.find('td',{'class':'no-border-links hauptlink'})

        # Extract the team's Transfermarkt profile URL
        team_url = team_info.find('a').get('href')
        # Extract the Transfermarkt team ID from the profile URL
        team_id = int(team_url.split('/')[-3])
        # Extract the team name from the link title
        team_name = team_info.find('a').get('title')

        # STANDINGS INFORMATION

        # Locate the cells containing the team's statistical information
        stats_info = row.find_all('td',{'class':'zentriert'})

        # Extract the statistics in the same order in which they appear
        # in the standings table. The first centered cell is excluded
        # because it does not belong to these performance statistics.
        (
            matches_played,
            matches_won,
            matches_draw,
            matches_losses,
            matches_goals,
            goals_dif,
            points
        ) = [stat.string for stat in stats_info[1:8]]

        # Combine the team information and statistics into a single record
        temp = {
            'season_id': season_id,
            'team_url': team_url,
            'team_id': team_id,
            'team_name': team_name,
            'position': i+1,
            'matches_played': int(matches_played),
            'matches_won': int(matches_won),
            'matches_draw': int(matches_draw),
            'matches_losses': int(matches_losses),
            'matches_goals': matches_goals,
            'goals_dif': int(goals_dif),
            'points': int(points)
        }

        # Add the current team's standings record to the final output
        output_list.append(temp)
    # Return the complete league table for the selected round
    return output_list

def get_squad(headers, league, n_season):
    """
    Extracts squad and market value information for every team in a
    specific league and season from Transfermarkt.

    The function accesses the league overview page and collects information
    about each team, including the team name, Transfermarkt ID, squad size,
    average player age, number of foreign players, and total market value.
    The displayed market value is also converted into a numeric integer
    value to simplify future analysis.

    Parameters:
        headers (dict): HTTP headers used when sending the request.
        league (str): League identifier used in the Transfermarkt URL.
        n_season (int): Starting year of the season to be scraped.

    Returns:
        list: A list of dictionaries where each dictionary contains
        squad and market value information for one team.
    """
    # Build the Transfermarkt league overview URL for the selected season
    # Request the page and create a BeautifulSoup object for HTML parsing
    url = f'https://www.transfermarkt.com/{league}/startseite/wettbewerb/{all_leagues[league]}/plus/?saison_id={n_season}'
    response = get_page(url, headers)
    soup = BeautifulSoup(response.content, "lxml")

    # Create a unique identifier for the selected league and season
    season_id = f'{all_leagues[league]}-{n_season}'

    # Locate all tables with the "items" class on the league overview page
    all_info = soup.find_all('table',{'class':'items'})

    # Store the extracted information for all teams
    output_list = []

    # Extract all team rows from the main league table
    table_info = all_info[0].find_all('tr',{'class':['odd','even']})

    # Process each team in the league
    for row in table_info:

        # TEAM INFORMATION

        # Locate all links contained in the current team row
        team_info = row.find_all('a')

        # Extract the team's Transfermarkt profile URL
        team_url = team_info[0].get('href')
        # Extract the Transfermarkt team ID from the profile URL
        team_id = int(team_url.split('/')[-3])
        # Extract the team name
        team_name = team_info[1].string
        # Extract the number of players registered in the squad
        team_squad = int(team_info[-2].string)
        # Extract the team's total market value as displayed by Transfermarkt
        team_value = team_info[-1].string

        # Identify the abbreviation used in the market value
        # (bn = billion, m = million, k = thousand)
        abv_index = team_value[-1]
        if abv_index == 'n': team_value_int = int(float(team_value.replace('€', '').replace('bn', '')) * 1_000_000_000)
        elif abv_index == 'm': team_value_int = int(float(team_value.replace('€', '').replace('m', '')) * 1_000_000)
        elif abv_index == 'k': team_value_int = int(float(team_value.replace('€', '').replace('k', '')) * 1_000)
        else: team_value_int = int(team_value.replace('-', '0'))

        # ADDITIONAL SQUAD INFORMATION

        # Locate the centered cells containing age and foreign-player data
        add_info = row.find_all('td',{'class':'zentriert'})
        # Extract the average age of the squad
        team_avg_age = float(add_info[-2].string)
        # Extract the number of foreign players in the squad
        team_foreigners = int(add_info[-1].string)

        # Combine all extracted values into a single team record
        temp = {
            'season_id': season_id,
            'team_url': team_url,
            'team_id': team_id,
            'team_name': team_name,
            'team_squad': team_squad,
            'team_value': team_value,
            'team_value_int': team_value_int,
            'team_avg_age': team_avg_age,
            'team_foreigners': team_foreigners
        }

        # Add the current team record to the final output
        output_list.append(temp)
    # Return squad information for all teams in the selected season
    return output_list

def get_title(headers, league):
    """
    Extracts the championship history for a specific league from Transfermarkt.

    The function accesses the league's title-history page and collects
    information about each championship season, including the winning team,
    the team's Transfermarkt ID and URL, and the manager responsible for
    the title. The extraction stops after the 1992/93 season.

    Parameters:
        headers (dict): HTTP headers used when sending the request.
        league (str): League identifier used in the Transfermarkt URL.

    Returns:
        list: A list of dictionaries where each dictionary represents
        one championship season and its corresponding winner and manager.
    """
    # Build the Transfermarkt URL containing the league's title history
    # Request the page and create a BeautifulSoup object for HTML parsing
    url = f'https://www.transfermarkt.com/{league}/erfolge/wettbewerb/{all_leagues[league]}'
    response = get_page(url, headers)
    soup = BeautifulSoup(response.content, "lxml")

    # Locate the table containing the championship history
    all_info = soup.find_all('table',{'class':'items'})
    # Extract all season rows from the title-history table
    table_info = all_info[0].find_all('tr',{'class':['odd','even']})

    # Store the extracted championship records
    output_list = []

    # Process each championship season
    for row in table_info:

        # TEAM AND MANAGER INFORMATION

        # Locate all links containing team and manager information
        team_info = row.find_all('a')

        # Extract the winning team's Transfermarkt URL
        team_url = team_info[0].get('href')
        # Extract the team's Transfermarkt ID from its URL
        team_id = team_url.split('/')[-3]
        # Extract the name of the championship-winning team
        team_name = team_info[1].string
        # Extract the manager's Transfermarkt profile URL
        manager_url = team_info[2].get('href')
        # Extract the manager ID stored in the HTML element
        manager_id = team_info[2].get('id')
        # Extract the manager's name
        manager_name = team_info[2].string

        # SEASON INFORMATION

        # Locate the centered table cells containing season information
        add_info = row.find_all('td',{'class':'zentriert'})
        # Extract the displayed season label, such as "23/24"
        season_name = add_info[0].string
        # Extract the season starting year from the team URL
        season = team_url.split('/')[-1]
        # Create a unique identifier combining league and season
        season_id = f'{all_leagues[league]}-{season}'

        # Combine all extracted values into a single title record
        temp = {
            'season_id': season_id,
            'season_name': season_name,
            'team_url': team_url,
            'team_id': team_id,
            'team_name': team_name,
            'manager_url': manager_url,
            'manager_id': manager_id,
            'manager_name': manager_name
        }

        # Add the current championship record to the final output
        output_list.append(temp)

        # Stop after the first Premier League season,
        # excluding records from before the competition was created
        if season_name == '92/93': break

    # Return the championship history from 1992/93 onward
    return output_list

def get_top_scorers(headers, league, n_season):
    """
    Extracts the complete top-scorers leaderboard for a specific league
    and season from Transfermarkt.

    The function first accesses the first page of the top-scorers ranking
    to determine how many pages are available. It then iterates through
    every leaderboard page and extracts player, team, nationality,
    ranking, matches played, and goals information.

    Parameters:
        headers (dict): HTTP headers used when sending requests to Transfermarkt.
        league (str): League identifier used in the Transfermarkt URL.
        n_season (int): Starting year of the season to be scraped.

    Returns:
        list: A list of dictionaries where each dictionary contains
        information about one player from the top-scorers leaderboard.
    """
    # Build the URL for the first page of the selected season's top-scorers ranking
    # Request the first page and create a BeautifulSoup object for HTML parsing
    url = f'https://www.transfermarkt.com/{league}/torschuetzenliste/wettbewerb/{all_leagues[league]}/saison_id/{n_season}/altersklasse/alle/detailpos//page/1'
    response = get_page(url, headers)
    soup = BeautifulSoup(response.content, "lxml")

    # Locate the pagination section to determine the total number of pages
    pages_info = soup.find_all('div', {'class':'pager'})
    # Find the link that points to the final leaderboard page
    last_page_link = pages_info[0].find_all('li',{'class':'tm-pagination__list-item tm-pagination__list-item--icon-last-page'})
    # Extract the last page number from the URL
    last_page_number = last_page_link[0].find('a').get('href').split('/')[-1]

    # Store all players extracted from the leaderboard
    output_list = []

    # Iterate through every page of the top-scorers ranking
    for n_page in range(1,int(last_page_number)+1):
        # Build the URL for the current leaderboard page
        # Request and parse the current page
        url = f'https://www.transfermarkt.com/{league}/torschuetzenliste/wettbewerb/{all_leagues[league]}/saison_id/{n_season}/altersklasse/alle/detailpos//page/{n_page}'
        response = get_page(url, headers)
        soup = BeautifulSoup(response.content, "lxml")

        # Locate the table body containing the top-scorers ranking
        all_content = soup.find_all('tbody')
        # Extract all player rows, which alternate between "odd" and "even"
        content = all_content[1].find_all('tr',{'class':['odd','even']})

        # Create a unique identifier for the selected season
        season_id = f'{all_leagues[league]}-{n_season}'

        # Process each player from the current leaderboard page
        for row in content:
            # Locate the centered cells containing most leaderboard information
            td_player_info = row.find_all('td',{'class':'zentriert'})

            # Extract the player's position in the top-scorers leaderboard
            leaderboard_pos = int(td_player_info[0].string)
            # Extract the player's nationality from the flag image
            country_name = td_player_info[1].find('img').get('title')
            # Extract the player's age during the selected season
            player_age = int(td_player_info[2].string)

            # Check how the team information is stored in the HTML.
            # In most cases, the team is inside an <a> tag
            if td_player_info[3].string == None:
                team_name = td_player_info[3].find('a').get('title')
                team_url = td_player_info[3].find('a').get('href')
                team_id = int(team_url.split('/')[-3])
            else:
                # If the team information is stored only as plain text (if the player played for more than one team),
                # keep the displayed name and leave URL and ID unavailable
                team_name = td_player_info[3].string
                team_url = None 
                team_id = 0

            # Extract the player's name from the profile link
            player_name = td_player_info[4].find('a').get('title')
            # Extract the player's Transfermarkt profile URL
            player_url = td_player_info[4].find('a').get('href')
            # Extract the Transfermarkt player ID from the profile URL
            player_id = int(player_url.split('/')[-5])
            # Extract the number of matches played during the season
            matches_played = int(td_player_info[4].string)
            # Extract the total number of goals scored
            goals = int(td_player_info[5].string)

            # Combine all extracted values into a single leaderboard record
            temp = {
                'season_id': season_id,
                'player_url': player_url,
                'player_id': player_id,
                'player_name': player_name,
                'player_age': player_age,
                'country_name': country_name,
                'team_url': team_url,
                'team_id': team_id,
                'team_name': team_name,
                'leaderboard_pos': leaderboard_pos,
                'matches_played': matches_played,
                'goals': goals
            }

            # Add the player record to the final output
            output_list.append(temp)
    # Return the complete top-scorers leaderboard
    return output_list