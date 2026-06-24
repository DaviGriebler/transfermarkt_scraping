import requests
import pandas as pd
from bs4 import BeautifulSoup


class Transfermarkt:
    def __init__(self, league, headers):
        self.league = league
        self.headers = headers

    def get_squad(self, n_season):
        link_type = 'startseite'
        value = []

        url = f'https://www.transfermarkt.com.br/{self.league}/{link_type}/wettbewerb/GB1/plus/?saison_id={n_season}'
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.content, "lxml")

        tables = soup.find_all('table', {'class':'items'})
        main_table = tables[0]

        even_info = main_table.find_all('tr', {'class':'even'})
        odd_info = main_table.find_all('tr', {'class':'odd'})

        info = odd_info + even_info

        season_key = f'PL-{n_season}'

        for row in info:
            temp = []

            temp.append(season_key)

            team_name = row.find('a').get('title')
            
            if row.find_all('a')[2].get('href') == '#': team_value = row.find_all('a')[-1].string
            else: team_value = row.find_all('a')[3].string

            temp.append(team_name)
            temp.append(team_value)

            squad_info = row.find_all('td', {'class':'zentriert'})
            for i, item in enumerate(squad_info):
                if i != 0: temp.append(item.string)

            value.append(temp)

        value.insert(0, ['season_id', 'team_name','team_value','team_squad','team_avg_age','team_foreigners'])
        return value
    
    # FIX GET ALL THE MATCHES FROM THE SEASON
    def get_goals(self, n_season, n_round):
        goals_list = []
        count_goal = 0
        n_match = 0
        
        link_type = 'spieltag'
        url = f'https://www.transfermarkt.com.br/{self.league}/{link_type}/wettbewerb/GB1/saison_id/{n_season}/spieltag/{n_round}'

        response = requests.get(url, headers=self.headers)
        response.status_code
        soup = BeautifulSoup(response.content, "lxml") # "html.parser"

        all_matches = soup.find_all('table', {'style':'border-top: 0 !important;'})

        season_id = f'PL-{n_season}'
        
        for match in all_matches:
            n_match += 1
            match_id = f'M-{n_season}-{n_match:02d}'
            event = match.find_all('tr', {'class':'no-border spieltagsansicht-aktionen'})

            # List with the entire class necessary to get the home and away team's names
            gross_h_team = match.find('td', {'class':'rechts hauptlink no-border-rechts hide-for-small spieltagsansicht-vereinsname'})
            gross_a_team = match.find('td', {'class':'hauptlink zentriert no-border-rechts no-border-links hide-for-small spieltagsansicht-wappen'})

            # Checking for a possible forum buttom
            home_forum_check = gross_h_team.find('a').get('href')
            away_forum_check = gross_a_team.find('a').get('href')

            # Different ways to get the title depending if it has the forum buttom
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

            
            for row in event:
                temp = []

                temp.append(season_id)
                temp.append(match_id)

                # Goal primary key
                count_goal += 1
                goal_id = f"G-{n_season}-{count_goal:04d}"
                temp.append(goal_id)

                # Home Team Events
                try: 
                    event_type = row.find('td', {'class':'rechts no-border-rechts spieltagsansicht'}).find_all('span')[2].get('class')[1]
                    goal_minute = row.find('td', {'class':'zentriert no-border-links'}).string
                    temp.append(h_team)
                    temp.append(goal_minute)
                
                # Away Team Events
                except: 
                    event_type = row.find('td', {'class':'links no-border-links spieltagsansicht'}).find('span').get('class')[1]
                    goal_minute = row.find('td', {'class':'zentriert no-border-rechts'}).string
                    temp.append(a_team)
                    temp.append(goal_minute)

                # Event Types Information
                if event_type == 'icon-tor-formation': temp.append(0) # Normal Goal
                elif event_type == 'icon-elfmeter-formation': temp.append(1) # Penalty Goal
                elif event_type == 'icon-eigentor-formation': temp.append(2) # Own Goal
                elif event_type == 'icon-verschossener-elfmeter-formation': temp.append(-2) # Penalty Missed
                else: temp.append(-1) # Red Cards

                # Player wich made the action
                player = row.find('a').get('title')
                temp.append(player)    

                goals_list.append(temp)

        goals_list.insert(0,['season_id', 'match_id', 'goal_id','goal_score_team','goal_minute','goal_type', 'goal_scorer_name'])
        return goals_list
    
    # FIX GET ALL THE MATCHES FROM THE SEASON
    def get_match(self, n_season, n_round):
        all_rounds = []
        n_match = 0

        link_type = 'spieltag'
        url = f'https://www.transfermarkt.com.br/{self.league}/{link_type}/wettbewerb/GB1/saison_id/{n_season}/spieltag/{n_round}'

        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.content, "lxml")
        all_information = soup.find_all('table', {'style':'border-top: 0 !important;'})

        # Gathering Useful Information
        for row in all_information:
            temp = []
            n_match += 1

            season_key = f'PL-{n_season}'
            match_key = f'M-{n_season}-{n_match:03d}'

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
    
    def get_table(self, n_season):
        final_placement = []

        link_type = 'tabelle'
        url = f'https://www.transfermarkt.com.br/{self.league}/{link_type}/wettbewerb/GB1/saison_id/{n_season}'

        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.content, "lxml")

        all_info = soup.find_all('tbody')
        info = all_info[1].find_all('tr')

        season_key = f'PL-{n_season}'

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
    
    def get_title(self):
        titles = []

        link_type = 'erfolge'
        url = f'https://www.transfermarkt.com.br/{self.league}/{link_type}/wettbewerb/GB1'

        response = requests.get(url, headers=self.headers)
        response.status_code
        soup = BeautifulSoup(response.content, "lxml")

        all_info = soup.find_all('tbody')
        info = all_info[0].find_all('tr')

        for row in info:
            temp = []

            season = row.find('td', {'class':'zentriert'}).string
            if season == '91/92': break # First season of the current format of the Premier League
            
            team_manager = row.find_all('a')

            temp.append(season)

            for i, item in enumerate(team_manager):
                if i == 0: continue
                temp.append(item.string)
            
            titles.append(temp)

        titles.insert(0,['season_name', 'team_name', 'manager_name'])
        return titles
    
    # FIX GET ALL THE MATCHES FROM THE SEASON
    def get_round_placement(self, n_season):
        round_classification = []
        
        if n_season > 1994: season_round = 39
        else: season_round = 43

        for n_round in range(1,season_round): # THERE ARE SEASONS WITH MORE TEAMS!!!
            link_type = 'spieltagtabelle'
            url = f'https://www.transfermarkt.com.br/{self.league}/{link_type}/wettbewerb/GB1/saison_id/{n_season}/spieltag/{n_round}'

            response = requests.get(url,headers=self.headers)
            soup = BeautifulSoup(response.content,'lxml')

            info = soup.find_all('tbody')
            table_info = info[2].find_all('tr')

            for row in table_info:
                temp = []

                season_key = f'PL-{n_season}'
                round_key = f'R-{n_season}-{n_round:02d}'
                
                temp.append(season_key)
                temp.append(round_key)

                placement = row.find('td',{'class':'rechts hauptlink'}).get_text(strip=True)
                team = row.find('a').get('title')

                temp.append(placement)
                temp.append(team)

                adicional_info = row.find_all('td', {'class':'zentriert'})

                for i, item in enumerate(adicional_info):
                    if i == 0: continue
                    temp.append(item.string)

                round_classification.append(temp)

        round_classification.insert(0,['season_id','round_id','placement','team_name','matches','wins','draws','losses','goals','goal_dif','points'])
        return round_classification