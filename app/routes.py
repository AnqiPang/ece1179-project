from flask import Flask, render_template, request, redirect, url_for
import sys
import spotipy
import spotipy.util as util
from spotipy import oauth2
import os

webapp = Flask(__name__, static_url_path = '/static', static_folder = 'static')

SPOTIPY_CLIENT_ID = '5ec5a760341246d489abaa3767016822'
SPOTIPY_CLIENT_SECRET = '607c55218f39417a969c7bd89a089207'
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback/'
SCOPE = 'user-library-read'
CACHE = '.spotipyoauthcache1'

sp_oauth = oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope=SCOPE, cache_path=CACHE)

@webapp.route('/')
@webapp.route('/index')
def index():
    access_token = ''
    token_info = sp_oauth.get_cached_token()
    if token_info:
        access_token = token_info['access_token']
    
    if access_token:
        return render_template('index.html', auth_url=url_for('home'))
    else:
        return render_template('index.html', auth_url=sp_oauth.get_authorize_url())

@webapp.route('/callback/')
def callback():
    access_token = ''
    url = request.url
    code = sp_oauth.parse_response_code(url)
    if code:
        token_info = sp_oauth.get_access_token(code)
        access_token = token_info['access_token']

    if access_token:
        return redirect(url_for('home'))
    else:
        return render_template('index.html', auth_url=sp_oauth.get_authorize_url())

@webapp.route('/home')
def home():
    # check if app is authorized by looking for cached token
    access_token = ''
    token_info = sp_oauth.get_cached_token()
    if token_info:
        access_token = token_info['access_token']
    
    if not access_token:
        return render_template('index.html', auth_url=sp_oauth.get_authorize_url())

    # print info of user's playlists on console
    sp = spotipy.Spotify(access_token)
    playlists = sp.current_user_playlists()
    print(playlists)

    for i, playlist in enumerate(playlists['items']):
        print("%d %s" % (i, playlist['name']))


    return '<div>'+str(playlists)+'</div>\
            <br><br>\
            <a href=' + url_for('index') + '>Back to Index</a>\
            <br><br>\
            <a href=' + url_for('logout') + '>Logout</a>'

@webapp.route('/logout')
def logout():
    # delete cached token
    os.remove(sp_oauth.cache_path)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    webapp.run()
