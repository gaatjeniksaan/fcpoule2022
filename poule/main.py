from collections import Counter
import logging
import time

import requests
from bs4 import BeautifulSoup


def main():
    matches = get_matches_urls()
    results = aggregate_results(matches)
    print(results)


def get_matches_urls():
    with requests.Session() as session:
        r = session.get("https://fbref.com/en/comps/1/schedule/World-Cup-Scores-and-Fixtures")
        if r.status_code != 200:
            raise ValueError(f"issue connecting to get matches: {r.status_code}")
    
    s = BeautifulSoup(r.text)
    
    table = s.find('table', { 'class' : 'stats_table' })
    body = table.tbody
    table_lines = body.find_all("td", class_="center")
    
    matches = []
    for match in table_lines:
        try:
            matches.append(match.contents[0].attrs["href"])
        except IndexError as e:
            logging.warning(f"can't process match: {match} because of IndexError {e}")
            continue
        except KeyError as e:
            try:
                matches.append(match.a.attrs["href"])
            except AttributeError as e2:
                logging.warning(f"can't process match: {match} because of AttributeError {e}")
                return match

    return matches


def get_corners_for_match(match_url):
    results = Counter()
    with requests.Session() as session:
        r = session.get("https://fbref.com" + match_url)
        if r.status_code != 200:
            raise ValueError(f"something went wrong connecting: {r.status_code}")
    s = BeautifulSoup(r.text)
    tables = s.find_all("div", class_="table_container")
    if len(tables) <= 9:
        logging.warning(f"not enough tables found for match: {match_url}")
        return results

    table_home = tables[2]
    table_away = tables[9]

    home = _get_corners_from_table(table_home)
    away = _get_corners_from_table(table_away)
    
    for result in (home, away):
        results += result
    
    return results


def _get_corners_from_table(table):
    results = {}
    contents = table.tbody.contents
    end = len(contents)
    for i in range(1, end, 2):
        row = contents[i]
        player: str
        for attr in row:
            if attr.attrs.get("data-stat") == "shirtnumber":
                player = str(attr.string)
            if attr.attrs.get("data-stat") == "corner_kicks":
                
                try:
                    n_corners = int(attr.string)
                except TypeError:
                    n_corners = 0
                if n_corners > 0:
                    results[player] = n_corners
    
    return Counter(results)


def aggregate_results(matches):
    results = Counter()
    for match_url in matches:
        time.sleep(1)
        result = get_corners_for_match(match_url)
        
        results += result
        
    return results


if __name__ == "__main__":
    main()