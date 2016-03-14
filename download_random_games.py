from __future__ import unicode_literals
import random

try:
    from urllib2 import urlopen
    from urllib2 import HTTPError, URLError
except ImportError:
    from urllib.request import urlopen
    from urllib.error import HTTPError, URLError

import time
import json
import sys
import os
import os.path

def get_page_with_wait(url, wait=6, max_retries=1, current_retry_count=0):  # SGF throttling is 10/minute
    if wait < 0.01:
        wait = 0.01

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
        data = json.loads(get_page_with_wait(url, 0).decode('utf-8'))
        for r in data["results"]:
            yield r
        url = data["next"]

def user_games(user_id):
    url = "https://online-go.com/api/v1/players/{}/games/?format=json".format(user_id)
    for r in results(url):
        yield r["id"]

def user_reviews(user_id):
    return
    url = "https://online-go.com/api/v1/reviews/?owner__id={}&format=json".format(user_id)
    for r in results(url):
        yield r["id"], r["game"]["id"]

def reviews_for_game(game_id):
    return
    url = "https://online-go.com/api/v1/games/{}/reviews?format=json".format(game_id)
    for r in results(url):
        yield r["id"]

def save_sgf(out_filename, SGF_URL, name):
    if os.path.exists(out_filename):
        print("Skipping {} because it has already been downloaded.".format(name))
    else:
        print("Downloading {}...".format(name))
        sgf = get_page_with_wait(SGF_URL)
        with open(out_filename, "wb") as f:
            f.write(sgf)

def get_user_ids_from_game(game_id):
    url = "https://online-go.com/api/v1/games/{}?format=json".format(game_id)
    data = json.loads(get_page_with_wait(url, 0).decode('utf-8'))
    return data["black"], data["white"], data["width"], data["height"]

def get_num_games(player_id):
    url = "https://online-go.com/api/v1/players/{}/games?format=json".format(player_id)
    data = json.loads(get_page_with_wait(url, 0).decode('utf-8'))
    return data["count"]

if __name__ == "__main__":
    max_game = 360000

    dest_dir = "random_games"

    for game_num in range(10000):
        print(game_num)
        gid = random.randint(max_game // 2, max_game)
        player1, player2, w, h = get_user_ids_from_game(gid)
        if not (w == h == 19):
            print("bad wh {} {}".format(w, h))
            continue
        counts1 = get_num_games(player1)
        counts2 = get_num_games(player2)
        if counts1 > 100 and counts2 > 100:
            print("found 1: {} {}  with {} {}\n".format(player1, player2, counts1, counts2))
            save_sgf(os.path.join(dest_dir, "OGS_game_{}.sgf".format(gid)),
                     "https://online-go.com/api/v1/games/{}/sgf".format(gid),
                     "game {}".format(gid))
