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
import requests

webapp = Flask(__name__, static_url_path = '/static', static_folder = 'static')
webapp.config['FLASKS3_BUCKET_NAME'] = S3_BUCKET
s3 = FlaskS3(webapp)

sp_oauth = oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope=SCOPE, cache_path=CACHE)

# for home page user playlists
pl_names = []
pl_image_urls =[]
pl_ids = []
pl_descriptions = []
pl_track_ids = []
pl_track_names = []
pl_art_ids = []
pl_track_dicts = []
user_avator = S3_URL_PREFIX+'/static/img/icon/spotify.png'

# for home page generated playlist
pl_name = ''
gen_art_names = []
gen_art_genres = []
gen_track_names = []
gen_track_artists = []
gen_track_covers = []

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
        return redirect(url_for('index'))

@webapp.route('/home')
def home():
    # check if app is authorized by looking for cached token
    access_token = ''
    token_info = sp_oauth.get_cached_token()
    if token_info:
        access_token = token_info['access_token']
    
    if not access_token:
        return redirect(url_for('index'))

    global pl_names
    global pl_image_urls
    global pl_ids
    global pl_descriptions
    global pl_track_ids
    global pl_track_names
    global pl_art_ids
    global pl_track_dicts
    global user_avator
    
    pl_names = []
    pl_image_urls = []
    pl_ids = []
    pl_descriptions = []
    pl_track_ids = []
    pl_track_names = []
    pl_art_ids = []
    pl_track_dicts = []
    user_avator = S3_URL_PREFIX+'/static/img/icon/spotify.png'

    sp = spotipy.Spotify(access_token)
    playlists = sp.current_user_playlists()
    print(json.dumps(playlists, indent=2))

    for i, playlist in enumerate(playlists['items']):
        track_names = []
        track_ids = []
        art_names =[]
        art_ids =[]
        current_tracks_list = list()
        print("%d %s" % (i, playlist['name']))
        pl_names.append(playlist['name'])
        if len(playlist['images']) != 0:
            pl_image_urls.append(playlist['images'][0]['url'])
        else:
            pl_image_urls.append(S3_URL_PREFIX+'/static/img/icon/spotify.png')
        pl_ids.append(playlist['id'])
        pl_descriptions.append(playlist['description'])
        results = sp.playlist(playlist['id'], fields= "tracks,next")
        print("results:", json.dumps(results, indent=2))
        tracks = results['tracks']
        print("tracks:", json.dumps(tracks, indent=2))

        for i, item in enumerate(tracks['items']):
            track = item['track']
            track_names.append(track['name'])
            track_ids.append(track['id'])
            art_names = art_names + [d['name'] for d in track['artists']]
            art_ids = art_ids + [d['id'] for d in track['artists']]
            current_artist = [d['name'] for d in track['artists']]
            current_tracks_list = current_tracks_list + [{'name': track['name'], 'artist': ', '.join([str(elem) for elem in current_artist])} ]
            print(
                (i, track['artists'][0]['name'], track['name']))
        #art_names = art_names + [d['name'] for d in track['artists']]
        #art_ids = art_ids + [d['id'] for d in track['artists']]



        while tracks['next']:
            tracks = sp.next(tracks)

            for i, item in enumerate(tracks['items']):
                track = item['track']
                track_names.append(track['name'])
                track_ids.append(track['id'])
                art_names = art_names + [d['name'] for d in track['artists']]
                art_ids = art_ids + [d['id'] for d in track['artists']]
                current_artist = [d['name'] for d in track['artists']]
                current_tracks_list = current_tracks_list + [{'name': track['name'], 'artist': ', '.join([str(elem) for elem in current_artist])}]
                print(
                    i, [d['name'] for d in track['artists']], track['name'])


        pl_track_names.append(track_names)
        pl_track_ids.append(track_ids)
        pl_art_ids.append(art_ids)
        #pl_art_names.append(art_names)
        pl_track_dicts.append(current_tracks_list)
        print("current_tracks_list:", current_tracks_list)
    print(pl_names)
    print(pl_image_urls)
    print(pl_ids)
    print(pl_descriptions)
    print("pl_track_dicts[0]:", pl_track_dicts[0])

    print("pl_track_names: ", pl_track_names)
    print("pl_track_ids: ", pl_track_ids)
    #print("pl_art_names: ", pl_art_names)
    print("pl_art_ids: ", pl_art_ids)
    print("num of artists: ", len(pl_art_ids[1]))


    """
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
    """
        pl_track_ids.append(track_ids)
        pl_track_names.append(track_names)
        pl_art_names.append(art_names)
        pl_art_ids.append(art_ids)
    """


    print("playlist track names: ", pl_track_names)
    #print("playlist artisit names: ", pl_art_names)

    if len(sp.me()['images']) != 0:
        user_avator = sp.me()['images'][0]['url']
    else:
        user_avator = S3_URL_PREFIX+'/static/img/icon/spotify.png'

    return render_template('home.html', playlist_names=pl_names, playlist_descriptions=pl_descriptions,\
                           playlist_covers=pl_image_urls, playlist_tracks=pl_track_dicts, user_avator=user_avator,\
                           playlist_ids=json.dumps(pl_ids), gen_track_names=gen_track_names, gen_track_artists=gen_track_artists,\
                           gen_track_covers=gen_track_covers, gen_artists=json.dumps(gen_art_names), gen_genres=json.dumps(gen_art_genres),\
                           pl_name=pl_name)

@webapp.route('/logout')
def logout():
    # delete cached token
    os.remove(sp_oauth.cache_path)
    '''f = open(sp_oauth.cache_path, "w")
    f.write("{\"a\":\"b\"}")
    f.close()'''
    
    # clear user data
    global pl_names
    global pl_image_urls
    global pl_ids
    global pl_descriptions
    global pl_track_ids
    global pl_track_names
    global pl_art_ids
    global pl_track_dicts
    global user_avator
    
    pl_names = []
    pl_image_urls = []
    pl_ids = []
    pl_descriptions = []
    pl_track_ids = []
    pl_track_names = []
    pl_art_ids = []
    pl_track_dicts = []
    user_avator = S3_URL_PREFIX+'/static/img/icon/spotify.png'
    
    global pl_name
    global gen_art_names
    global gen_art_genres
    global gen_track_names
    global gen_track_artists
    global gen_track_covers

    pl_name = ''
    gen_art_names = []
    gen_art_genres = []
    gen_track_names = []
    gen_track_artists = []
    gen_track_covers = []
    
    return redirect(url_for('index'))

@webapp.route('/home/<id>')
def generate(id):
    access_token = ''
    token_info = sp_oauth.get_cached_token()
    if token_info:
        access_token = token_info['access_token']

    if not access_token:
        redirect(url_for('index'))

    global pl_name
    global gen_art_names
    global gen_art_genres
    global gen_track_names
    global gen_track_artists
    global gen_track_covers

    pl_name = ''
    gen_art_names = []
    gen_art_genres = []
    gen_track_names = []
    gen_track_artists = []
    gen_track_covers = []

    sp = spotipy.Spotify(access_token)
    track_ids = []

    pl_name = sp.playlist(id, fields='name')['name']

    offset = 0
    while True:
        response = sp.playlist_tracks(id,
                                      offset=offset,
                                      fields='items.track.id,total')
        #pprint(response)
        #print("items ", response['items'])

        offset = offset + len(response['items'])
        track_ids = track_ids + [d['track']['id'] for d in response['items']]
        #print(offset, "/", response['total'])

        if len(response['items']) == 0:
            break

    '''pl_art_names = []
    pl_art_ids = []
    pl_art_genres = []
    for track in track_ids:
        # urn = 'spotify:track:6TqXcAFInzjp0bODyvrWEq'
        uri = 'spotify:track:' + str(track)
        track = sp.track(uri)
        # art_name = track['album']['artists'][0]['name']
        pl_art_names = pl_art_names + [d['name'] for d in track['artists']]
        pl_art_ids = pl_art_ids + [d['id'] for d in track['artists']]

    for artist in pl_art_ids:
        art_genre = sp.artists(artist)
        pl_art_genres.append(art_genre)'''
    
    pl_art_ids_dict = {}
    pl_art_names_dict = {}
    pl_art_genres_dict = {}
    
    for track in track_ids:
        uri = 'spotify:track:' + str(track)
        track = sp.track(uri)
        art_ids = [d['id'] for d in track['artists']]
        art_names = [d['name'] for d in track['artists']]
        for id in art_ids:
            pl_art_ids_dict[id] = pl_art_ids_dict.get(id, 0) + 1
        for name in art_names:
            pl_art_names_dict[name] = pl_art_names_dict.get(name, 0) + 1
    
    for artist_id in pl_art_ids_dict.keys():
        genres = sp.artist(artist_id)['genres']
        for genre in genres:
            pl_art_genres_dict[genre] = pl_art_genres_dict.get(genre, 0) + 1

    pl_art_ids = sorted(pl_art_ids_dict.items(), key=lambda kv: kv[1], reverse=True)
    pl_art_names = sorted(pl_art_names_dict.items(), key=lambda kv: kv[1], reverse=True)
    pl_art_genres = sorted(pl_art_genres_dict.items(), key=lambda kv: kv[1], reverse=True)

    # recommend tracks based on top (max occurrences) 3 genres and top 2 artists
    recommendations = sp.recommendations(seed_artists=[i[0] for i in pl_art_ids[0:min(2, len(pl_art_ids))]],\
                                         seed_genres=[i[0] for i in pl_art_genres[0:min(3, len(pl_art_genres))]], limit=20)

    gen_art_ids_dict = {}
    gen_art_names_dict = {}
    gen_art_genres_dict = {}

    for t in recommendations['tracks']:
        gen_track_names.append(t['name'])
        gen_track_artists.append(', '.join(elem['name'] for elem in t['artists']))
        for artist in t['artists']:
            gen_art_ids_dict[artist['id']] = gen_art_ids_dict.get(artist['id'], 0) + 1
            gen_art_names_dict[artist['name']] = gen_art_names_dict.get(artist['name'], 0) + 1
        gen_track_covers.append(t['album']['images'][0]['url'])

    for artist_id in gen_art_ids_dict.keys():
        genres = sp.artist(artist_id)['genres']
        for genre in genres:
            gen_art_genres_dict[genre] = gen_art_genres_dict.get(genre, 0) + 1

    gen_art_ids = sorted(gen_art_ids_dict.items(), key=lambda kv: kv[1], reverse=True)
    gen_art_names = sorted(gen_art_names_dict.items(), key=lambda kv: kv[1], reverse=True)
    gen_art_genres = sorted(gen_art_genres_dict.items(), key=lambda kv: kv[1], reverse=True)

    return render_template('home.html', playlist_names=pl_names, playlist_descriptions=pl_descriptions,\
                           playlist_covers=pl_image_urls, playlist_tracks=pl_track_dicts, user_avator=user_avator,\
                           playlist_ids=json.dumps(pl_ids), gen_track_names=gen_track_names, gen_track_artists=gen_track_artists,\
                           gen_track_covers=gen_track_covers, gen_artists=json.dumps(gen_art_names), gen_genres=json.dumps(gen_art_genres),\
                           pl_name=pl_name)







webapp.run()
