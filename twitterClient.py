#!/usr/bin/python
# -*- coding: utf-8; mode: python -*-

from flask import Flask, request, redirect, url_for, flash, render_template
from flask_oauthlib.client import OAuth

app = Flask(__name__)
app.config['DEBUG'] = True
oauth = OAuth()
mySession = None
currentUser = None

app.secret_key = 'development'

twitter = oauth.remote_app('twitter',
                           base_url='https://api.twitter.com/1.1/',
                           request_token_url='https://api.twitter.com/oauth/request_token',
                           access_token_url='https://api.twitter.com/oauth/access_token',
                           authorize_url='https://api.twitter.com/oauth/authenticate',
                           consumer_key='xRxFoWzorAAgN8C2KGEUvFDdH',
                           consumer_secret='8PiaFxKpSHKYQNCpjd86Unwirlx5aW48Tn1YSB1a4q9Dx77EbI'
                           )


# Obtener token para esta sesion
@twitter.tokengetter
def get_twitter_token(token=None):
    global mySession

    if mySession is not None:
        return mySession['oauth_token'], mySession['oauth_token_secret']

# Limpiar sesion anterior e incluir la nueva sesion
@app.before_request
def before_request():
    global mySession
    global currentUser

    currentUser = None
    if mySession is not None:
        currentUser = mySession
    else:
        flash("You need to log in", "error")


# Pagina principal
@app.route('/')
def index():
    global currentUser

    tweets = None
    if currentUser is not None:
        resp = twitter.request('statuses/user_timeline.json' + '?screen_name=' + currentUser['screen_name'])
        if statusOK(resp.status):
            tweets = resp.data
        else:
            flash('Imposible acceder a Twitter.')
    return render_template('index.html', user=currentUser, tweets=tweets)


# Get auth token (request)
@app.route('/login')
def login():
    callback_url = url_for('oauthorized', next=request.args.get('next'))
    return twitter.authorize(callback=callback_url or request.referrer or None)


# Eliminar sesion
@app.route('/logout')
def logout():
    global mySession

    mySession = None
    return redirect(url_for('index'))


# Callback
@app.route('/oauthorized')
def oauthorized():
    global mySession

    resp = twitter.authorized_response()
    if resp is None:
        flash('You denied the request to sign in.')
    else:
        mySession = resp

    return redirect(url_for('index'))


# Operaciones
@app.route('/deleteTweet', methods=['POST'])
def deleteTweet():
    response = twitter.post('statuses/destroy/' + request.form["tweetId"] + ".json")
    if not statusOK(response.status):
        flash(response.data['errors'][0]['message'], "error")
    else:
        flash("Tweet has been deleted")
    return redirect(url_for('index'))


@app.route('/retweet', methods=['POST'])
def retweet():
    response = twitter.post('statuses/retweet/' + request.form["tweetId"] + ".json")
    if not statusOK(response.status):
        flash(response.data['errors'][0]['message'], "error")
    else:
        flash("Tweet has been retweeted")
    return redirect(url_for('index'))


@app.route('/follow', methods=['POST'])
def follow():
    userId = request.form["userId"]
    userName = request.form["username"]
    checkFields(userId, userName)
    if len(userId) != 0:
        response = twitter.post('friendships/create.json', data={'user_id': userId})
    else:
        response = twitter.post('friendships/create.json', data={'screen_name': userName})
    if not statusOK(response.status):
        flash(response.data['errors'][0]['message'], "error")
    else:
        flash("User has been followed")
    return redirect(url_for('index'))


@app.route('/tweet', methods=['POST'])
def tweet():
    response = twitter.post('statuses/update.json', data={'status': request.form["tweetText"]})
    if not statusOK(response.status):
        flash(response.data['errors'][0]['message'], "error")
    else:
        flash("Tweet sent")
    return redirect(url_for('index'))


@app.route('/unfollow', methods=['POST'])
def unfollow():
    userId = request.form["userId"]
    userName = request.form["username"]
    checkFields(userId, userName)
    if len(userId) != 0:
        response = twitter.post('friendships/destroy.json', data={'user_id': userId})
    else:
        response = twitter.post('friendships/destroy.json', data={'screen_name': userName})
    if not statusOK(response.status):
        flash(response.data['errors'][0]['message'], "error")
    else:
        flash("User has been unfollowed")
    return redirect(url_for('index'))


@app.route('/like', methods=['POST'])
def likeTweet():
    response = twitter.post('favorites/create.json', data={'id': request.form["tweetId"]})

    if not statusOK(response.status):
        flash(response.data['errors'][0]['message'], "error")
    else:
        flash("Tweet has been liked")
    return redirect(url_for('index'))


@app.route('/dislike', methods=['POST'])
def dislikeTweet():
    response = twitter.post('favorites/destroy.json', data={'id': request.form["tweetId"]})
    if not statusOK(response.status):
        flash(response.data['errors'][0]['message'], "error")
    else:
        flash("Tweet has been unliked")
    return redirect(url_for('index'))


def checkFields(field1, field2):
    if len(field1) != 0 and len(field2) != 0:
        flash("You must enter the user id or username, not both.", "error")
    elif len(field1) == 0 and len(field2) == 0:
        flash("You must enter the user id or username.", "error")

def statusOK(status):
    return 200 <= status < 300


if __name__ == '__main__':
    app.run()
