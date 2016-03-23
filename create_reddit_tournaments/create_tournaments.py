from __future__ import unicode_literals

import time
import json
import get_auth
import datetime

try:
    from urllib import urlencode
    from urllib2 import urlopen
    from urllib2 import HTTPError, URLError, Request
except ImportError:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode


def get_page_with_wait(url, wait=1, max_retries=1, current_retry_count=0):
    if wait < 0.1:
        wait = 0.1
    try:
        time.sleep(wait)
        response = urlopen(url)
    except HTTPError as e:
        if e.code == 429:  # too many requests
            print("Too many requests / minute, falling back to {} seconds between fetches.".format(int(1.5 * wait)))
            # exponential falloff
            return get_page_with_wait(url, wait=(1.5 * wait))
        raise
    except URLError as e:
        # sometimes DNS or the network temporarily falls over, and will come back if we try again
        if current_retry_count < max_retries:
            return get_page_with_wait(url, 5, current_retry_count=current_retry_count + 1)  # Wait 5 seconds between retries
        print("Can't fetch '{}'.  Check your network connection.".format(url))
        raise
    else:
        return response.read()

def results(url):
    while url is not None:
        data = json.loads(get_page_with_wait(url, 0.1).decode('utf-8'))
        for r in data["results"]:
            yield r
        url = data["next"]

def kyu_to_rank(k):
    if k > 0:
        return 30 - k
    elif k < 0:
        return 29 - k
    else:
        raise RuntimeError("0 is not a valid rank")

def kyu_to_name(k):
    # ranks are > 0: kyu
    #           < 0: dan
    if k > 0:
        return '{}k'.format(k)
    else:
        return '{}d'.format(-k)

def get_open_tournaments(group_id):
    url = 'https://online-go.com/api/v1/tournaments/?group={}&started__isnull=true'.format(group_id)
    tournament_list = [t for t in results(url)]
    return tournament_list

def create_tournament(name, group, lo, hi):
    ''' see http://docs.ogs.apiary.io/#reference/tournaments/tournaments/create-tournament '''
    values = {"name": name,
              "description": name,
              "group": group,
              "min_ranking": lo,
              "max_ranking": hi,
              "tournament_type": "roundrobin",
              "time_control_parameters": {
                  "time_control": "fischer",
                  "initial_time": 259200,
                  "max_time": 604800,
                  "time_increment": 86400
              },
              "exclusivity": "open",
              "handicap": -1,
              "exclude_provisional": True,
              "auto_start_on_max": True,
              "settings": {"maximum_players": 10},
              "time_start": (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat()}
    print (values)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(get_auth.token())
    }
    data = urlencode(values).encode('UTF-8')
    request = Request('https://online-go.com/api/v1/tournaments/', data=data, headers=headers)
    response_body = urlopen(request).read()
    print("RESPONSE: {}".format(response_body))

if __name__ == "__main__":
    # ranks are > 0: kyu
    #           < 0: dan
    ranking_limits = [(25, 16),
                      (20, 11),
                      (15, 6),
                      (10, 1),
                      (6, -4),
                      (4, -6)]

    token = get_auth.token()
    print ("accces " + token)

    open_tourneys = get_open_tournaments(38)

    for rlo, rhi in ranking_limits:
        rklo = kyu_to_rank(rlo)
        rkhi = kyu_to_rank(rhi)
        nklo = kyu_to_name(rlo)
        nkhi = kyu_to_name(rhi)

        for t in open_tourneys:
            if t['min_ranking'] == rklo and t['max_ranking'] == rkhi:
                print('found tournament for {}-{}: https://online-go.com/tournament/{}'.
                      format(kyu_to_name(rlo), kyu_to_name(rhi), t['id']))
                break
        else:
            print('Creating  tournament for {}-{}'.
                  format(kyu_to_name(rlo), kyu_to_name(rhi)))
            create_tournament("Reddit Round Robin Handicap Correspondence - {}-{}".format(nklo, nkhi),
                              38, rklo, rkhi)