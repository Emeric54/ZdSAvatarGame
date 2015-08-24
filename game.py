import json
import sqlite3
import requests

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing

from random import randint


# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
SECRET_KEY = 'blablablabla secret key'

API_ROOT = 'https://zestedesavoir.com/api/'

app = Flask(__name__)
app.config.from_object(__name__)

black_list = []  # 404 members


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/')
def home():
    cur = g.db.execute('SELECT pseudo, sum(score) as total FROM round GROUP BY pseudo ORDER BY total DESC')
    score = [dict(pseudo=row[0], score=row[1]) for row in cur.fetchall()]

    max_members = pick_max_members()
    candidates = []
    imageurl = ""
    if max_members < 0:
        flash('Erreur {}'.format(max_members))
    else:
        (erreur, candidates) = pick_candidates(max_members)
        if erreur:
            flash('Erreur {}'.format(erreur))
        else:
            pk = randint(0, 2)
            imageurl = candidates[pk]['avatar']
            session['answer'] = candidates[pk]['id']
            print candidates[pk]['id']
    if 'pseudo' not in session:
        pseudo = ""
    else:
        pseudo = session['pseudo']

    return render_template('home.html', score=score,
                                        candidates=candidates,
                                        imageurl=imageurl,
                                        pseudo=pseudo)


def pick_max_members():
    req = requests.get(API_ROOT + 'membres/')
    if not req.status_code == 200:
        data = -req.status_code
    else:
        data = req.json()
        data = data['count']
    return data


def pick_candidates(max_members):
    """ fetch three pseudos from the API """
    erreur = 0
    candidates = []
    for i in range(0, 3):
        data = []
        ok = False
        while not ok:
            pk = randint(1, max_members)
            if pk not in black_list:
                req = requests.get(API_ROOT + 'membres/{}'.format(pk))
                print '\n\n'
                if req.status_code == 404:
                    print "ERREUR 404"
                    black_list.append(pk)
                    print 'pk {} is now blacklisted'.format(pk)
                    print black_list
                elif req.status_code == 429:
                    print "ERREUR 429"
                    candidates = []
                    return (erreur, candidates)
                elif req.status_code != 200:
                    print "ERREUR {}".format(req.status_code)
                    candidates = []
                    erreur = req.status_code
                    return (erreur, candidates)
                else:
                    data = req.json()
                    current = {'id': data['pk'],
                               'pseudo': data['username'],
                               'avatar': data['avatar_url']}
                    candidates.append(current)
                    ok = True

    import pprint
    pprint.pprint(candidates)

    return (erreur, candidates)


@app.route('/play', methods=['POST'])
def play():
    win = False
    goodid = session['answer']
    form_pseudo = request.form['pseudo']
    form_id = int(request.form['propal'])
    if form_id == goodid:
        win = True
    session['pseudo'] = form_pseudo

    g.db.execute('insert into round (pseudo, score) values (?, ?)',
                 [form_pseudo, win])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=DEBUG)
