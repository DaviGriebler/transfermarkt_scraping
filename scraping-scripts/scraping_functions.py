import requests
from bs4 import BeautifulSoup

# ------------------------------------------------------------------
# leagues dictionary
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
# All available scraping functions
# ------------------------------------------------------------------
def get_events(headers, league, n_season, n_round):
    """
    Scrape match events from a specific league, season, and round.

    The function accesses the Transfermarkt matchday page and extracts
    events such as goals, penalties, own goals, missed penalties, and
    red cards. Each event is associated with its season, match, team,
    minute, type, and player.

    Parameters
    ----------
    headers : dict
        HTTP headers used in the request to Transfermarkt.

    league : str
        League name used in the Transfermarkt URL and as a key in the
        all_leagues dictionary.

    n_season : int
        Starting year of the season.

    n_round : int
        Round number to be scraped.

    Returns
    -------
    list
        A list containing the event records. The first element contains
        the column names, while the remaining elements contain the
        extracted event data.
    """
    # Initialize the output list and identifier counters
    events_list = []
    count_event = 0
    n_match = 0

    # Create a unique identifier for the selected league and season
    season_id = f'{all_leagues[league]}-{n_season}'
    
    # Build the matchday URL and parse the page content
    url = f'https://www.transfermarkt.com/{league}/spieltag/wettbewerb/{all_leagues[league]}/saison_id/{n_season}/spieltag/{n_round}'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "lxml")

    # Find all tables containing individual match information
    all_matches = soup.find_all('table', {'style':'border-top: 0 !important;'})
    
    # Process each match found on the page
    for match in all_matches:
        # Create a sequential identifier for the current match
        n_match += 1
        match_id = f'M-{n_season}-{n_round:02d}-{n_match:02d}'
        
        # Find all event rows associated with the current match
        event = match.find_all('tr', {'class':'no-border spieltagsansicht-aktionen'})

        # Locate the HTML containers holding the home and away team names
        gross_h_team = match.find('td', {'class':'rechts hauptlink no-border-rechts hide-for-small spieltagsansicht-vereinsname'})
        gross_a_team = match.find('td', {'class':'hauptlink zentriert no-border-rechts no-border-links hide-for-small spieltagsansicht-wappen'})

        # Check whether an additional forum link appears before the team link
        home_forum_check = gross_h_team.find('a').get('href')
        away_forum_check = gross_a_team.find('a').get('href')

        # Extract team names while accounting for optional forum links
        if 'forum' in home_forum_check and 'forum' in away_forum_check:
            h_team = gross_h_team.find_all('a')[1].get('title')
            a_team = gross_a_team.find_all('a')[1].get('title')
        elif 'forum' in home_forum_check:
            h_team = gross_h_team.find_all('a')[1].get('title')
            a_team = gross_a_team.find('a').get('title')
        elif 'forum' in away_forum_check:
            h_team = gross_h_team.find('a').get('title')
            a_team = gross_a_team.find_all('a')[1].get('title')
        else:
            h_team = gross_h_team.find('a').get('title')
            a_team = gross_a_team.find('a').get('title')

        # Process each event recorded for the current match
        for row in event:
            # Start a new record with its season and match identifiers
            temp = []
            temp.append(season_id)
            temp.append(match_id)

            # Create a unique sequential identifier for the event
            count_event += 1
            event_id = f"E-{n_season}-{n_round:02d}-{count_event:04d}"
            temp.append(event_id)

            # Transfermarkt separates home and away team events
            try: 
                # Extract event information from the home-team side
                event_type = row.find('td', {'class':'rechts no-border-rechts spieltagsansicht'}).find_all('span')[2].get('class')[1]
                event_minute = row.find('td', {'class':'zentriert no-border-links'}).string
                temp.append(h_team)
                temp.append(event_minute)
            
            except: 
                # Extract event information from the away-team side
                event_type = row.find('td', {'class':'links no-border-links spieltagsansicht'}).find('span').get('class')[1]
                event_minute = row.find('td', {'class':'zentriert no-border-rechts'}).string
                temp.append(a_team)
                temp.append(event_minute)

            # Convert Transfermarkt event icons into numeric event codes
            if event_type == 'icon-tor-formation': temp.append(1) # Regular goal
            elif event_type == 'icon-elfmeter-formation': temp.append(2) # Penalty Goal
            elif event_type == 'icon-eigentor-formation': temp.append(3) # Own Goal
            elif event_type == 'icon-verschossener-elfmeter-formation': temp.append(-1) # Missed penalty
            elif event_type == 'icon-rotekarte-formation': temp.append(-2) # # Direct red card
            elif event_type == 'icon-gelbrotekarte-formation': temp.append(-3) # Second yellow card
            else: temp.append(0) # Unmapped or exceptional event

            # Extract the player responsible for the event
            player = row.find('a').get('title')
            temp.append(player)    

            # Add the completed event record to the output list
            events_list.append(temp)

    # Add column names as the first row of the returned dataset
    events_list.insert(0,['season_id', 'match_id', 'event_id','event_team','event_minute','event_type', 'event_player'])
    return events_list

# ------------------------------------------------------------------
# get_match() function
# ------------------------------------------------------------------
def get_match(headers, league, n_season, n_round):
    all_rounds = []
    n_match = 0

    url = f'https://www.transfermarkt.com/{league}/spieltag/wettbewerb/{all_leagues[league]}/saison_id/{n_season}/spieltag/{n_round}'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "lxml")
    
    all_information = soup.find_all('table', {'style':'border-top: 0 !important;'})

    # Gathering Useful Information
    for row in all_information:
        temp = []
        n_match += 1

        season_key = f'{all_leagues[league]}-{n_season}'
        match_key = f'M-{n_season}-{n_round:02d}-{n_match:03d}'

        if n_round < 10: round_key = f'R-{n_season}-0' + str(n_round)
        else: round_key = f'R-{n_season}-' + str(n_round)

        temp.append(season_key)
        temp.append(round_key)
        temp.append(match_key)

        # List with the entire class necesaire to get the home and away team's names
        gross_home_team = row.find('td', {'class':'rechts hauptlink no-border-rechts hide-for-small spieltagsansicht-vereinsname'})
        gross_away_team = row.find('td', {'class':'hauptlink zentriert no-border-rechts no-border-links hide-for-small spieltagsansicht-wappen'})

        # Checking for a possible forum buttom
        home_forum_check = gross_home_team.find('a').get('href')
        away_forum_check = gross_away_team.find('a').get('href')

        # Different ways to get the title depending if it has the forum buttom
        if 'forum' in home_forum_check and 'forum' in away_forum_check:
            home_team = gross_home_team.find_all('a')[1].get('title')
            away_team = gross_away_team.find_all('a')[1].get('title')
        elif 'forum' in home_forum_check:
            home_team = gross_home_team.find_all('a')[1].get('title')
            away_team = gross_away_team.find('a').get('title')
        elif 'forum' in away_forum_check:
            home_team = gross_home_team.find('a').get('title')
            away_team = gross_away_team.find_all('a')[1].get('title')
        else:
            home_team = gross_home_team.find('a').get('title')
            away_team = gross_away_team.find('a').get('title')

        # Getting the final score
        final_score = row.find('span', {'class':'matchresult finished'}).string

        # Appending data from a single match together
        temp.append(home_team)
        temp.append(final_score)
        temp.append(away_team)

        # Storing adicional info separately, easier to extract right information
        adicional_info = row.find_all('td', {'class':'zentriert no-border'})

        for i, item in enumerate(adicional_info):
            if i == 2:
                text = item.get_text(" ", strip=True)
                try: 
                    attendance = text.split()[0]
                    temp.append(attendance)
                except: temp.append(text)
            else:
                day_ref = item.find('a').string
                temp.append(day_ref.strip())

        all_rounds.append(temp)

    all_rounds.insert(0,['season_id','round_id', 'match_id', 'home_team', 'final_score', 'away_team', 'date', 'referee', 'attendance'])
    return all_rounds

# ------------------------------------------------------------------
# get_placements() function
# ------------------------------------------------------------------
def get_placements(headers, league, n_season, n_round):
    all_placements = []
    
    url = f'https://www.transfermarkt.com/{league}/spieltagtabelle/wettbewerb/{all_leagues[league]}/saison_id/{n_season}/spieltag/{n_round}'
    response = requests.get(url,headers=headers)
    soup = BeautifulSoup(response.content,'lxml')

    info = soup.find_all('tbody')
    table_info = info[2].find_all('tr')

    for i,row in enumerate(table_info):
        temp = []

        season_key = f'{all_leagues[league]}-{n_season}'
        round_key = f'R-{n_season}-{n_round:02d}'
        placement = i+1
        team = row.find('a').get('title')
        
        temp.append(season_key)
        temp.append(round_key)
        temp.append(placement)
        temp.append(team)

        # Extracting: 'matches','wins','draws','losses','goals','goal_dif','points'
        team_info = row.find_all('td', {'class':'zentriert'})
        for i, item in enumerate(team_info):
            if i == 0: continue
            temp.append(item.string)

        all_placements.append(temp)

    all_placements.insert(0,['season_id','round_id','placement','team_name','matches','wins','draws','losses','goals','goal_dif','points'])
    return all_placements

# ------------------------------------------------------------------
# get_squad() function
# ------------------------------------------------------------------
def get_squad(headers, league, n_season):
    all_squads = []

    url = f'https://www.transfermarkt.com/{league}/startseite/wettbewerb/{all_leagues[league]}/plus/?saison_id={n_season}'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "lxml")

    tables = soup.find_all('table', {'class':'items'})
    main_table = tables[0]

    even_info = main_table.find_all('tr', {'class':'even'})
    odd_info = main_table.find_all('tr', {'class':'odd'})

    info = odd_info + even_info

    season_key = f'{all_leagues[league]}-{n_season}'

    for row in info:
        temp = []

        temp.append(season_key)

        team_name = row.find('a').get('title')
        
        if row.find_all('a')[2].get('href') == '#': team_value = row.find_all('a')[-1].string
        else: team_value = row.find_all('a')[3].string

        if team_value[-1] == 'm': 
            team_value = team_value[1:-1]+'0.000'
            team_value = float(team_value.replace(".", ""))
        elif team_value[-1] == 'n': 
            team_value = team_value[1:-2]+'0.000.000'
            team_value = float(team_value.replace(".", ""))

        temp.append(team_name)
        temp.append(team_value)

        squad_info = row.find_all('td', {'class':'zentriert'})
        for i, item in enumerate(squad_info):
            if i != 0: temp.append(item.string)

        all_squads.append(temp)

    all_squads.insert(0, ['season_id', 'team_name','team_value','team_squad','team_avg_age','team_foreigners'])
    return all_squads

# ------------------------------------------------------------------
# get_title() function
# ------------------------------------------------------------------
def get_title(headers, league):
    titles = []

    url = f'https://www.transfermarkt.com/{league}/erfolge/wettbewerb/{all_leagues[league]}'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "lxml")

    all_info = soup.find_all('tbody')
    info = all_info[0].find_all('tr')

    for row in info:
        temp = []

        season = row.find('td', {'class':'zentriert'}).string
        if season == '91/92': break # First season of the current format of the Premier League, maybe add a parameter to stop
        
        x = int(season.split('/')[0])
        if x > 90: n_season = x+1900
        else: n_season = x+2000
        season_key = f'{all_leagues[league]}-{n_season}'
        
        team_manager = row.find_all('a')
        temp.append(season_key)
        temp.append(season)

        for i, item in enumerate(team_manager):
            if i == 0: continue
            temp.append(item.string)
        
        titles.append(temp)

    titles.insert(0,['season_id', 'season_name','team_name', 'manager_name'])
    return titles

# ------------------------------------------------------------------
# get_table() function
# ------------------------------------------------------------------
def get_table(headers, league, n_season):
    final_placement = []

    url = f'https://www.transfermarkt.com/{league}/tabelle/wettbewerb/{all_leagues[league]}/saison_id/{n_season}'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "lxml")

    all_info = soup.find_all('tbody')
    info = all_info[1].find_all('tr')

    season_key = f'{all_leagues[league]}-{n_season}'

    for i,row in enumerate(info):
        temp = []

        temp.append(season_key)

        position = i+1
        team = row.find('a').get('title')
        data_info = row.find_all('td', {'class':'zentriert'})

        temp.append(position)
        temp.append(team)

        for i, item in enumerate(data_info):
            if i == 0: continue
            temp.append(item.string)
        
        final_placement.append(temp)

    final_placement.insert(0,['season_id', 'pos','team_name','played','wins','draws','losses','goals','goal_dif','points'])
    return final_placement

# ------------------------------------------------------------------
# get_top_scorers() function
# ------------------------------------------------------------------
def get_top_scorers(headers, league, n_season):
    top_scorers = []

    url = f'https://www.transfermarkt.com/{league}/torschuetzenliste/wettbewerb/{all_leagues[league]}/saison_id/{n_season}/altersklasse/alle/detailpos//page/1'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content,'lxml')

    # --------------------------------------------------
    # Finding the last page
    # --------------------------------------------------
    pages_info = soup.find_all('div', {'class':'pager'})
    last_page_link = pages_info[0].find_all('li',{'class':'tm-pagination__list-item tm-pagination__list-item--icon-last-page'})
    last_page_number = last_page_link[0].find('a').get('href').split('/')[-1]


    # --------------------------------------------------
    # Getting information
    # --------------------------------------------------
    for n_page in range(1,int(last_page_number)+1):
        url = f'https://www.transfermarkt.com/{league}/torschuetzenliste/wettbewerb/{all_leagues[league]}/saison_id/{n_season}/altersklasse/alle/detailpos//page/{n_page}'
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content,'lxml')
        
        # --------------------------------------------------
        # Extrating only the usefull information in the transfermarkt source page
        # --------------------------------------------------
        all_info = soup.find_all('table')
        # Transfermarkt separates information by index (odd, even)
        odd_info = all_info[1].find_all('tr',{'class':'odd'})
        even_info = all_info[1].find_all('tr',{'class':'even'})

        player_list = [odd_info,even_info]

        for player in player_list:
            for row in player:
                temp = []

                # --------------------------------------------------
                # Extracting data information
                # --------------------------------------------------
                # Creating a list containing only the main data points
                data = row.find_all('td',{'class':'zentriert'})

                # Extracting all relevant data and storing in different variables, mainly for better understanding
                pos = int(data[0].string)
                country = data[1].find('img').get('alt')
                age = int(data[2].string)
                name = data[4].find('a').get('title')
                matches = int(data[4].find('a').string)
                goals = int(data[5].find('a').string)

                # Some players scored for more than one club, that behaves differently in the transfermarkt source page
                try:team = data[3].find('a').get('title')
                except AttributeError: team = data[3].string
                
                # Creating the season key
                season_key = f'{all_leagues[league]}-{n_season}'

                # Gathering all the information for one player
                temp.append(season_key)
                temp.append(pos)
                temp.append(country)
                temp.append(age)
                temp.append(name)
                temp.append(team)
                temp.append(matches)
                temp.append(goals)

                # Appending the payer information in the main list
                top_scorers.append(temp)
    
    # Informing the headers of the list created
    head = (['season_id','pos','country','age','player_name','team','matches','goals'])
    top_scorers.insert(0,head)
    return top_scorers