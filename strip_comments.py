from gomill import sgf
import sys

def remove_comments(t):
    if t:
        for child in t:
            remove_comments(child)
    if t.has_property('C'):
        t.unset('C')

for f in sys.argv[1:]:
    s = sgf.Sgf_game.from_string(open(f, "rb").read())
    remove_comments(s.get_root())
    with open(f.replace('games', 'stripped'), 'wb') as f:
        f.write(s.serialise())
