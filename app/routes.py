from flask import Flask, render_template, request, redirect, url_for
import sys
import spotipy
import spotipy.util as util
from spotipy import oauth2
import os
from config import *
from helpers import *
from flask_s3 import FlaskS3
import json
import requests

webapp = Flask(__name__, static_url_path = '/static', static_folder = 'static')
webapp.config['FLASKS3_BUCKET_NAME'] = S3_BUCKET
s3 = FlaskS3(webapp)

sp_oauth = oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope=SCOPE, cache_path=CACHE)

@webapp.route('/')
@webapp.route('/index')
def index():
    access_token = ''
    token_info = sp_oauth.get_cached_token()
    if token_info:
        access_token = token_info['access_token']
    
    # s3 file urls
    css_url = S3_URL_PREFIX+'/static/css/style.css'
    particles_js_url = S3_URL_PREFIX+'/static/js/particles.js'
    app_js_url = S3_URL_PREFIX+'/static/js/app.js'
    logo_url = S3_URL_PREFIX+'/static/img/logo_fade_round.png'
    login_url = S3_URL_PREFIX+'/static/img/icon/spotify.png'
    particle_shape_url = S3_URL_PREFIX+'/static/img/particle_shape_1.png'
    background_urls = []
    for i in range(3):
        background_urls.append(S3_URL_PREFIX+'/static/img/background/'+str(i)+'.jpg')
    
    if access_token:
        return render_template('index.html', auth_url=url_for('home'), css_url=css_url, particles_js_url=particles_js_url,\
                               app_js_url=app_js_url, logo_url=logo_url, login_url=login_url, particle_shape_url=particle_shape_url,\
                               background_urls=background_urls)
    else:
        return render_template('index.html', auth_url=sp_oauth.get_authorize_url(), css_url=css_url, particles_js_url=particles_js_url,\
                               app_js_url=app_js_url, logo_url=logo_url, login_url=login_url, particle_shape_url=particle_shape_url,\
                               background_urls=background_urls)

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

    sp = spotipy.Spotify(access_token)
#me = sp.me()
#print(json.dumps(me, indent=2))




    sp = spotipy.Spotify(access_token)
    artist_uri_or_url_or_id = 'spotify:artist:36QJpDe2go2KgaRleHCDTp'
    results = sp.artist(artist_uri_or_url_or_id)
    print(json.dumps(results, indent=2))






    # provide the following vars with data collected from spotify
    playlist_names = ['playlist1', 'playlist2', 'playlist3']
    playlist_descriptions = ['yoyo', 'yeah', 'happyasfsadgsdfgrsdrtersfgsddsfdasdsaewrtewrewrewr']
    playlist_covers = ['https://m.media-amazon.com/images/I/615enb8in0L._SS500_.jpg', 'https://m.media-amazon.com/images/I/615enb8in0L._SS500_.jpg', 'https://m.media-amazon.com/images/I/615enb8in0L._SS500_.jpg']
    playlist_tracks = [[{ 'name': 'p1-t1', 'artist': 'aaa' }, { 'name': 'p1-t2', 'artist': 'bbb' },],
                       [{ 'name': 'p2-t1', 'artist': 'aaa' }, { 'name': 'p2-t2', 'artist': 'bbb' },],
                       [{ 'name': 'p3-t1', 'artist': 'aaa' }, { 'name': 'p3-t2', 'artist': 'bbb' },]]
    user_avator = sp.me()['images'][0]['url']

    return render_template('home.html', playlist_names=playlist_names, playlist_descriptions=playlist_descriptions,\
                           playlist_covers=playlist_covers, playlist_tracks=playlist_tracks, user_avator=user_avator)

@webapp.route('/logout')
def logout():
    # delete cached token
    os.remove(sp_oauth.cache_path)
    '''f = open(sp_oauth.cache_path, "w")
    f.write("{\"a\":\"b\"}")
    f.close()'''
    return redirect(url_for('index'))
