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
from pprint import pprint

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
    playlists = sp.current_user_playlists()
    print("playlists")
    print(json.dumps(playlists, indent=2))

    pl_names = []
    pl_image_urls =[]
    pl_ids = []
    pl_descriptions = []

    for i, playlist in enumerate(playlists['items']):
        print("%d %s" % (i, playlist['name']))
        pl_names.append(playlist['name'])
        pl_image_urls.append(playlist['images'][0]['url'])
        pl_ids.append(playlist['id'])
        pl_descriptions.append(playlist['description'])
    print(pl_names)
    print(pl_image_urls)
    print(pl_ids)
    print(pl_descriptions)

    pl_track_ids = []
    pl_track_names = []
    pl_art_ids = []
    pl_art_names = []

    for pl_id in pl_ids:
        track_names = []
        track_ids = []
        art_ids = []
        art_names = []
        # sp = spotipy.Spotify(client_credentials_manager=oauth2.SpotifyClientCredentials)
        offset = 0
        while True:
            response = sp.playlist_tracks(pl_id,
                                          offset=offset,
                                          fields='items.track.id,items.track.name,total')
            pprint(response)
            print("items ", response['items'])

            offset = offset + len(response['items'])
            for item in response['items']:
                track_names.append(item['track']['name'])
                track_ids.append(item['track']['id'])
                track_uri = 'spotify:track:' + str(item['track']['id'])
                track = sp.track(track_uri)
                for d in track['artists']:
                    art_names.append(d['name'])
                    art_ids.append(d['id'])
            if len(response['items'])==0:
                break
            print(offset, "/", response['total'])


        """    
            track_names = track_names + [d['track']['name'] for d in response['items']]
            track_ids = track_ids + [d['track']['id'] for d in response['items']]
            print(offset, "/", response['total'])

            if len(response['items']) == 0:
                break
        #pl_track_ids.append(track_ids)
        art_names = []
        art_ids = []
        for track in track_ids:
            # urn = 'spotify:track:6TqXcAFInzjp0bODyvrWEq'
            uri = 'spotify:track:' + str(track)
            track = sp.track(uri)
            # art_name = track['album']['artists'][0]['name']
            art_names = art_names + [d['name'] for d in track['artists']]
            art_ids = art_ids + [d['id'] for d in track['artists']]
        """

        pl_track_ids.append(track_ids)
        pl_track_names.append(track_names)
        pl_art_names.append(art_names)
        pl_art_ids.append(art_ids)


    print("playlist track names: ", pl_track_names)
    print("playlist artisit names: ", pl_art_names)

    # provide the following vars with data collected from spotify
    playlist_names = ['playlist1', 'playlist2', 'playlist3']
    playlist_descriptions = ['yoyo', 'yeah', 'happyasfsadgsdfgrsdrtersfgsddsfdasdsaewrtewrewrewr']
    playlist_covers = ['https://m.media-amazon.com/images/I/615enb8in0L._SS500_.jpg', 'https://m.media-amazon.com/images/I/615enb8in0L._SS500_.jpg', 'https://m.media-amazon.com/images/I/615enb8in0L._SS500_.jpg']
    playlist_tracks = [[{ 'name': 'p1-t1', 'artist': 'aaa' }, { 'name': 'p1-t2', 'artist': 'bbb' },],
                       [{ 'name': 'p2-t1', 'artist': 'aaa' }, { 'name': 'p2-t2', 'artist': 'bbb' },],
                       [{ 'name': 'p3-t1', 'artist': 'aaa' }, { 'name': 'p3-t2', 'artist': 'bbb' },]]
    user_avator = sp.me()['images'][0]['url']

    return render_template('home.html', playlist_names=pl_names, playlist_descriptions=pl_descriptions,\
                           playlist_covers=pl_image_urls, playlist_tracks=playlist_tracks)

@webapp.route('/logout')
def logout():
    # delete cached token
    os.remove(sp_oauth.cache_path)
    '''f = open(sp_oauth.cache_path, "w")
    f.write("{\"a\":\"b\"}")
    f.close()'''
    return redirect(url_for('index'))



webapp.run()