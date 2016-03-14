from __future__ import unicode_literals

import time
import json
import sys
import os
import os.path

try:
    from urllib2 import urlopen
    from urllib2 import HTTPError, URLError
except ImportError:
    from urllib.request import urlopen
    from urllib.error import HTTPError, URLError

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
        data = json.loads(get_page_with_wait(url, 0.1).decode('utf-8'))
        for r in data["results"]:
            yield r
        url = data["next"]

def save_sgf(out_filename, SGF_URL, name):
    if os.path.exists(out_filename):
        print("Skipping {} because it has already been downloaded.".format(name))
    else:
        print("Downloading {}...".format(name))
        sgf = get_page_with_wait(SGF_URL)
        with open(out_filename, "wb") as f:
            f.write(sgf)

if __name__ == "__main__":
    dest_dir = sys.argv[1]
    assert os.path.isdir(dest_dir)

    for ct, gp in enumerate(results("https://online-go.com/api/v1/games/?ladder=313&annulled=false")):
        if gp["outcome"] in ("", "Timeout", "Cancellation", "Annulled"):
            continue
        gid = gp["id"]
        save_sgf(os.path.join(dest_dir, "OGS_game_{}.sgf".format(gid)),
                 "https://online-go.com/api/v1/games/{}/sgf".format(gid),
                 "game {}".format(gid))
