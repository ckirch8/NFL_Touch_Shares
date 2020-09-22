from bs4 import BeautifulSoup, Comment
from urllib.request import urlopen
import pandas as pd
import re
import urllib.request, urllib.error
import csv
import sys

"""open url to scrape"""
def open_page(url):
    try:
        page = urlopen(url).read()
    except urllib.error.HTTPError as e:
        return False
    soup = BeautifulSoup(page, 'html.parser')
    return soup

"""some tables on sports reference pages are initially commented out thus dont show up in the first soup"""
def commented_table(soup, id):
    id = '#' + id
    if(soup.select_one(id)):
        table = soup.select_one(id)
    else:
        print('nah')
        return False
    comments = table.find(string=lambda text:isinstance(text,Comment))
    s = BeautifulSoup(comments, 'html.parser')
    return s

"""get the raw text for the data pice you are looking for"""
def get_text(s, feature):
    if(s.find('td', {'data-stat': feature})):
        cell = s.find('td', {'data-stat': feature})
        a = cell.text.strip().encode()
        text=a.decode("utf-8")
        return text
    else:
        return False

"""Grab the team name from the bottom of the page, for seome reasy the only place where its fully listed on its own"""
def get_team_name(soup):
    breadcrumbs = soup.select_one('.breadcrumbs')
    # print(breadcrumbs)
    cell = breadcrumbs.find_all('span', {'itemprop': 'name'})
    a = cell[-1].text.strip().encode()
    name=[a.decode("utf-8")]
    return name

def main(argvs):
    teams = ['nwe', 'buf', 'mia', 'nyj', 'rav', 'pit', 'cle', 'cin', 'jax', 'oti', 'clt', 'htx', 'sdg', 'kan', 'rai', 'den',
            'was', 'nyg', 'phi', 'dal', 'gnb', 'chi', 'min', 'det', 'nor', 'atl', 'tam', 'car', 'ram', 'crd', 'sea', 'sfo']

    features = ['player', 'pos', 'g', 'rush_att', 'targets', 'rec']

    foot_features = ['targets', 'rec']
    rush_features = ['player', 'pos', 'g', 'rush_att']
    rec_features = ['player', 'pos', 'g', 'targets', 'rec']

    header = ['player', 'pos', 'g', 'rush att', 'targets', 'rec', 'touches', 'avg att', 'avg targets', 'avg rec', 'avg touches', 'rush share', 'target share', 'touch share']

    week = argvs[0]
    outputfile = argvs[1] + '_' + argvs[0] + '.csv'
    print_lines = []
    names = []

    for team in teams:
        names = []
        url =  'https://www.pro-football-reference.com/teams/' + team + '/2020_advanced.htm'
        soup = open_page(url)
        # print(soup)
        team_name = get_team_name(soup)
        print_lines.append(team_name)

        """Seperate tables for rushing and receiving stats"""
        rush_soup = commented_table(soup, 'all_advanced_rushing')
        rec_soup = commented_table(soup, 'all_advanced_receiving')

        """Get the totals for rushing and receiving stats from table footers"""
        rush_footer = rush_soup.find('tfoot')
        rec_footer = rec_soup.find('tfoot')
        totals = ['totals', '', week]
        totals.append(get_text(rush_footer, 'rush_att'))
        for f in foot_features:
            totals.append(get_text(rec_footer, f))
        totals.append(int(totals[3])+int(totals[5]))
        for i in range(3, 7):
            totals.append(int(totals[i])/int(totals[2]))

        """Grab the bodies of the tables, with rows for each player"""
        rush_body = rush_soup.find('tbody')
        rec_body = rec_soup.find('tbody')

        print_lines.append(header)

        """get all the rushing rows"""
        rows = rush_body.find_all('tr')
        for row in rows:
            line = ['', '', '', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            for f in range(len(rush_features)):
                # print(rush_features[f])
                text = get_text(row, rush_features[f])
                line[f] = text
                if (f == 0):
                    names.append(text)
            """calculate the shares for rushing, targets, and touches"""
            line[6] = int(line[3]) + int(line[5])
            line[7] = int(line[3])/int(line[2])
            line[8] = int(line[4])/int(line[2])
            line[9] = int(line[5])/int(line[2])
            line[10] = int(line[6])/int(line[2])
            line[11] = '{:.2f}'.format(int(line[3])*100/int(totals[3]))
            line[12] = '{:.2f}'.format(int(line[4])*100/int(totals[4]))
            line[13] = '{:.2f}'.format(int(line[6])*100/int(totals[6]))
            print_lines.append(line)

        """move to receiving rows"""
        rows = rec_body.find_all('tr')
        for row in rows:
            name = get_text(row, 'player')
            new_name = True
            """check if line was already created for this player from rushing table"""
            try:
                """if exists, find where"""
                n = names.index(name)
                new_name = False
                line = print_lines[len(print_lines) - (len(names) - n)]
                # print(name)
                # print(line)
                i = 4
            except ValueError:
                names.append(name)
                i = 0
                line = ['', '', '', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            """skip player, g, pos, rush_att if player was already there"""
            # print(line)
            for f in range(i, len(features)):
                # print(f)
                text = get_text(row, features[f])
                if(text):
                    line[f] = text
            """calculate/recalculate target and touch shares"""
            line[6] = int(line[3]) + int(line[5])
            line[8] = int(line[4])/int(line[2])
            line[9] = int(line[5])/int(line[2])
            line[10] = int(line[6])/int(line[2])
            line[12] = '{:.2f}'.format(int(line[4])*100/int(totals[4]))
            line[13] = '{:.2f}'.format(int(line[6])*100/int(totals[6]))
            if(new_name):
                print_lines.append(line)
            # print(line)
        print_lines.append(totals)
        print_lines.append([])
        # print(print_lines)
        # break
    """print to csv"""
    with open(outputfile, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(print_lines)

if __name__ == "__main__":
	main(sys.argv[1:])
