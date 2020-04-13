from flask import Flask, render_template, request, redirect, url_for, flash
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
import boto3
from datetime import datetime
import decimal
from flask_cors import CORS


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return int(o)
        return super(DecimalEncoder, self).default(o)

webapp = Flask(__name__, static_url_path = '/static', static_folder = 'static')
webapp.config['FLASKS3_BUCKET_NAME'] = S3_BUCKET
s3 = FlaskS3(webapp)
CORS(webapp, resources=r'/*')

# oauth
sp_oauth = oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope=SCOPE, cache_path=CACHE)
sp_token = {}

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
gen_track_previews = []
gen_track_ids = []

# useless index page
@webapp.route('/')
@webapp.route('/index')
def index():
    '''access_token = ''
    token_info = sp_oauth.get_cached_token()
    if token_info:
        access_token = token_info['access_token']'''
    access_token = ''
    try:
        access_token = sp_token['access_token']
    except:
        pass
    
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

# used by oauth, will redirect to home page if auth succeeds
@webapp.route('/callback/')
def callback():
    access_token = ''
    url = request.url
    code = sp_oauth.parse_response_code(url)
    if code:
        token_info = sp_oauth.get_access_token(code, check_cache=False)
        access_token = token_info['access_token']
        global sp_token
        sp_token = token_info
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(DYNAMO_USER_TABLE_NAME)
        sp = spotipy.Spotify(access_token)
        uid = sp.me()['id']
        response = table.get_item(Key={'id':uid})
        # put new user to dynamodb
        if 'Item' not in response:
            table.put_item(Item={
                           'id': uid,
                           'playlist_ids': ['placeholder'],
                           'user_token': sp_token
                           })
        else:
            table.update_item(
                              Key={
                              'id': uid
                              },
                              UpdateExpression='SET user_token = :i',
                              ExpressionAttributeValues={
                              ':i': sp_token
                              }
                              )

    if access_token:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('index'))

# home page showing user playlists and generated playlist
@webapp.route('/home')
def home():
    # check if app is authorized by looking for cached token
    '''access_token = ''
    token_info = sp_oauth.get_cached_token()
    if token_info:
        access_token = token_info['access_token']'''
    global sp_token
    
    access_token = ''
    try:
        access_token = sp_token['access_token']
    except:
        pass
    
    if not access_token:
        return redirect(url_for('index'))

    # test if token valid
    # if not, clear token and ask for authorization
    try:
        sp = spotipy.Spotify(access_token)
        playlists = sp.current_user_playlists()
    except:
        sp_token = {}
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
    global close_def
    global close_hov
    global playlist_icon
    
    pl_names = []
    pl_image_urls = []
    pl_ids = []
    pl_descriptions = []
    pl_track_ids = []
    pl_track_names = []
    pl_track_pop = []
    pl_art_ids = []
    pl_track_dicts = []
    user_arts_dict = {}
    user_avator = S3_URL_PREFIX+'/static/img/icon/spotify.png'
    close_def = S3_URL_PREFIX+'/static/img/icon/close_def.png'
    close_hov = S3_URL_PREFIX+'/static/img/icon/close_hov.png'
    playlist_icon = S3_URL_PREFIX+'/static/img/icon/playlist.png'

    sp = spotipy.Spotify(access_token)
    playlists = sp.current_user_playlists()

    user_id = sp.me()['id']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMO_USER_TABLE_NAME)
    sp = spotipy.Spotify(access_token)
    uid = sp.me()['id']
    response = table.get_item(Key={'id': uid},
                              AttributesToGet=[
                                  'recommendation',
                              ]
    )
    print("recommendation", response)
    recommendation = response['Item']['recommendation']
    print(recommendation)

    for i, playlist in enumerate(playlists['items']):
        track_names = []
        track_ids = []
        track_pop = []
        art_names =[]
        art_ids =[]
        current_tracks_list = list()
        pl_names.append(playlist['name'])
        if len(playlist['images']) != 0:
            pl_image_urls.append(playlist['images'][0]['url'])
        else:
            pl_image_urls.append(S3_URL_PREFIX+'/static/img/icon/spotify.png')
        pl_ids.append(playlist['id'])
        pl_descriptions.append(playlist['description'])
        results = sp.playlist(playlist['id'], fields= "tracks,next")
        tracks = results['tracks']

        for i, item in enumerate(tracks['items']):
            track = item['track']
            popularity = track['popularity']
            track_names.append(track['name'])
            track_ids.append(track['id'])
            track_pop.append(popularity)
            art_names = art_names + [d['name'] for d in track['artists']]
            art_ids = art_ids + [d['id'] for d in track['artists']]
            current_artist = [d['name'] for d in track['artists']]
            current_artist_ids = [d['id'] for d in track['artists']]
            for art_id in current_artist_ids:
                user_arts_dict[art_id] = user_arts_dict.get(art_id, 0) + 1
            current_tracks_list = current_tracks_list + [{'name': track['name'], 'artist': ', '.join([str(elem) for elem in current_artist])} ]
        #art_names = art_names + [d['name'] for d in track['artists']]
        #art_ids = art_ids + [d['id'] for d in track['artists']]



        while tracks['next']:
            tracks = sp.next(tracks)

            for i, item in enumerate(tracks['items']):
                track = item['track']
                popularity = track['popularity']
                track_names.append(track['name'])
                track_ids.append(track['id'])
                track_pop.append(popularity)
                art_names = art_names + [d['name'] for d in track['artists']]
                art_ids = art_ids + [d['id'] for d in track['artists']]
                current_artist = [d['name'] for d in track['artists']]
                current_artist_ids = [d['id'] for d in track['artists']]
                for art_id in current_artist_ids:
                    user_arts_dict[art_id] = user_arts_dict.get(art_id, 0) + 1
                current_tracks_list = current_tracks_list + [{'name': track['name'], 'artist': ', '.join([str(elem) for elem in current_artist])}]


        pl_track_names.append(track_names)
        pl_track_ids.append(track_ids)
        pl_art_ids.append(art_ids)
        pl_track_pop.append(track_pop)
        #pl_art_names.append(art_names)
        pl_track_dicts.append(current_tracks_list)
    """
    user_genre_list = []
    flat_art_ids = [item for sublist in pl_art_ids for item in sublist]
    batched_art_ids = [flat_art_ids[i:i + 50] for i in range(0, len(flat_art_ids), 50)]
    for item in batched_art_ids:
        genres = sp.artists(item)['artists']
        for genre in genres:
            user_genre_list = user_genre_list + genre['genres']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('user_all_playlists')
    table.put_item(Item={
        'user_id': sp.me()['id'],
        'user_track_ids': pl_track_ids,
        'user_track_names': pl_track_names,
        'user_artist_ids': pl_art_ids,
        'user_artist_dict':user_arts_dict,
        'user_genre_list': user_genre_list
    })
    """


    if len(sp.me()['images']) != 0:
        user_avator = sp.me()['images'][0]['url']
    else:
        user_avator = S3_URL_PREFIX+'/static/img/icon/spotify.png'

    return render_template('home.html', playlist_names=pl_names, playlist_descriptions=pl_descriptions,\
                           playlist_covers=pl_image_urls, playlist_tracks=pl_track_dicts, user_avator=user_avator,\
                           playlist_ids=json.dumps(pl_ids), gen_track_names=gen_track_names, gen_track_artists=gen_track_artists,\
                           gen_track_covers=gen_track_covers, gen_track_previews=gen_track_previews, gen_artists=json.dumps(gen_art_names),\

                           gen_genres=json.dumps(gen_art_genres), pl_name=pl_name, close_def=close_def, close_hov=close_hov, playlist_icon=playlist_icon,\
                           recommendation=recommendation)

# logout current user, back to index
@webapp.route('/logout')
def logout():
    # delete cached token
    global sp_token
    sp_token = {}
    #os.remove(sp_oauth.cache_path)
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
    global gen_track_previews

    pl_name = ''
    gen_art_names = []
    gen_art_genres = []
    gen_track_names = []
    gen_track_artists = []
    gen_track_covers = []
    gen_track_previews = []
    
    return redirect(url_for('index'))

# generate new playlist based on selected user playlist
@webapp.route('/generation/<id>')
def generate(id):
    '''access_token = ''
    token_info = sp_oauth.get_cached_token()
    if token_info:
        access_token = token_info['access_token']'''
    global sp_token
        
    access_token = ''
    try:
        access_token = sp_token['access_token']
    except:
        pass

    if not access_token:
        redirect(url_for('index'))

    # test if token valid
    # if not, clear token and ask for authorization
    try:
        sp = spotipy.Spotify(access_token)
        playlists = sp.current_user_playlists()
    except:
        sp_token = {}
        return redirect(url_for('index'))

    global pl_name
    global gen_art_names
    global gen_art_genres
    global gen_track_names
    global gen_track_ids
    global gen_track_artists
    global gen_track_covers
    global gen_track_previews

    pl_name = ''
    gen_art_names = []
    gen_art_genres = []
    gen_track_names = []
    gen_track_artists = []
    gen_track_covers = []
    gen_track_previews = []
    gen_track_ids = []

    close_def = S3_URL_PREFIX+'/static/img/icon/close_def.png'
    close_hov = S3_URL_PREFIX+'/static/img/icon/close_hov.png'
    playlist_icon = S3_URL_PREFIX+'/static/img/icon/playlist.png'

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
        gen_track_ids.append(t['id'])
        gen_track_artists.append(', '.join(elem['name'] for elem in t['artists']))
        for artist in t['artists']:
            gen_art_ids_dict[artist['id']] = gen_art_ids_dict.get(artist['id'], 0) + 1
            gen_art_names_dict[artist['name']] = gen_art_names_dict.get(artist['name'], 0) + 1
        gen_track_covers.append(t['album']['images'][0]['url'])
        gen_track_previews.append(t['preview_url'])

    for artist_id in gen_art_ids_dict.keys():
        genres = sp.artist(artist_id)['genres']
        for genre in genres:
            gen_art_genres_dict[genre] = gen_art_genres_dict.get(genre, 0) + 1

    gen_art_ids = sorted(gen_art_ids_dict.items(), key=lambda kv: kv[1], reverse=True)
    gen_art_names = sorted(gen_art_names_dict.items(), key=lambda kv: kv[1], reverse=True)
    gen_art_genres = sorted(gen_art_genres_dict.items(), key=lambda kv: kv[1], reverse=True)

    # save generated playlist to dynamodb
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMO_PLAYLIST_TABLE_NAME)
    uid = sp.me()['id']
    pid = datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' by '+uid
    table.put_item(Item={
                      'created_on_by': pid,
                      'inspired_by': pl_name,
                      'track_names': gen_track_names,
                      'track_artists': gen_track_artists,
                      'track_covers': gen_track_covers,
                      'track_previews': gen_track_previews,
                      'artist_names': gen_art_names_dict,
                      'genres': gen_art_genres_dict
                      })

    table = dynamodb.Table(DYNAMO_USER_TABLE_NAME)
    response = table.get_item(Key={'id':uid})
    # put new user to dynamodb
    if 'Item' not in response:
        table.put_item(Item={
                       'id': uid,
                       'playlist_ids': [pid],
                       'user_token': sp_token
                       })
    else:
        table.update_item(
                            Key={
                            'id': uid
                            },
                            UpdateExpression='SET playlist_ids = list_append(playlist_ids, :i)',
                            ExpressionAttributeValues={
                            ':i': [pid]
                            }
                            )

    return render_template('home.html', playlist_names=pl_names, playlist_descriptions=pl_descriptions,\
                           playlist_covers=pl_image_urls, playlist_tracks=pl_track_dicts, user_avator=user_avator,\
                           playlist_ids=json.dumps(pl_ids), gen_track_names=gen_track_names, gen_track_artists=gen_track_artists,\
                           gen_track_covers=gen_track_covers, gen_track_previews=gen_track_previews, gen_artists=json.dumps(gen_art_names),\
                           gen_genres=json.dumps(gen_art_genres), pl_name=pl_name, close_def=close_def, close_hov=close_hov, playlist_icon = playlist_icon)

# previuosly generated playlists
@webapp.route('/history')
def history():
    '''access_token = ''
    token_info = sp_oauth.get_cached_token()
    if token_info:
        access_token = token_info['access_token']'''
    global sp_token
    
    access_token = ''
    try:
        access_token = sp_token['access_token']
    except:
        pass
    
    if not access_token:
        redirect(url_for('index'))

    # test if token valid
    # if not, clear token and ask for authorization
    try:
        sp = spotipy.Spotify(access_token)
        playlists = sp.current_user_playlists()
    except:
        sp_token = {}
        return redirect(url_for('index'))


    sp = spotipy.Spotify(access_token)
    uid = sp.me()['id']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMO_USER_TABLE_NAME)
    response = table.get_item(Key={'id':uid})
    # put new user to dynamodb
    if 'Item' not in response:
        table.put_item(Item={
                       'id': uid,
                       'playlist_ids': ['placeholder'],
                       'user_token': sp_token
                       })
        return 'No history'
    else:
        playlists = response['Item']['playlist_ids']
        table = dynamodb.Table(DYNAMO_PLAYLIST_TABLE_NAME)
        info = []
        for playlist in playlists:
            try:
                info.append(table.get_item(Key={'created_on_by':playlist})['Item'])
            except:
                pass
        info = sorted(info, key=lambda kv: kv['created_on_by'], reverse=True)
        info = info[0:min(20, len(info))]
        return render_template('history.html', playlists=json.dumps(info, cls=DecimalEncoder), user_avator=user_avator)

@webapp.route('/export', methods=['POST'])
def export():

    global sp_token

    access_token = ''
    try:
        access_token = sp_token['access_token']
    except:
        pass

    if not access_token:
        redirect(url_for('index'))

    # test if token valid
    # if not, clear token and ask for authorization
    try:
        sp = spotipy.Spotify(access_token)
        playlists = sp.current_user_playlists()
    except:
        sp_token = {}
        return redirect(url_for('index'))

    playlistName_new = request.form.get('plName')

    user_id = sp.me()['id']

    Msg = None

    for item in enumerate(playlists['items']):
        if playlistName_new == item[1]['name']:
            Msg = "The playlist already exists. Please try another name."
            #flash(Msg)
            print(Msg)

            return render_template('home.html', playlist_names=pl_names, playlist_descriptions=pl_descriptions,\
                                   playlist_covers=pl_image_urls, playlist_tracks=pl_track_dicts, user_avator=user_avator,\
                                   playlist_ids=json.dumps(pl_ids), gen_track_names=gen_track_names, gen_track_artists=gen_track_artists,\
                                   gen_track_covers=gen_track_covers, gen_track_previews=gen_track_previews, gen_artists=json.dumps(gen_art_names),\
                                   gen_genres=json.dumps(gen_art_genres), pl_name=pl_name, Msg=Msg)

    sp.user_playlist_create(user_id, playlistName_new)
    playlists = sp.current_user_playlists()
    playlist_id = next(item[1]['id'] for item in enumerate(playlists['items']) if item[1]['name'] == playlistName_new)
    sp.user_playlist_add_tracks(user_id, playlist_id, gen_track_ids)

    return render_template('home.html', playlist_names=pl_names, playlist_descriptions=pl_descriptions,\
                           playlist_covers=pl_image_urls, playlist_tracks=pl_track_dicts, user_avator=user_avator,\
                           playlist_ids=json.dumps(pl_ids), gen_track_names=gen_track_names, gen_track_artists=gen_track_artists,\
                           gen_track_covers=gen_track_covers, gen_track_previews=gen_track_previews, gen_artists=json.dumps(gen_art_names),\
                           gen_genres=json.dumps(gen_art_genres), pl_name=pl_name, Msg=Msg)



@webapp.route('/toggle', methods=['GET','POST'])
def toggle():
    toggle_value = request.get_json()
    print("1111")
    print(request.values['toggle_value'])
    toggle_value_bool =request.values['toggle_value']

    global sp_token

    access_token = ''
    try:
        access_token = sp_token['access_token']
    except:
        pass

    if not access_token:
        redirect(url_for('index'))

    # test if token valid
    # if not, clear token and ask for authorization
    try:
        sp = spotipy.Spotify(access_token)
        playlists = sp.current_user_playlists()
    except:
        sp_token = {}
        return redirect(url_for('index'))

    sp = spotipy.Spotify(access_token)
    uid = sp.me()['id']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMO_USER_TABLE_NAME)
    sp = spotipy.Spotify(access_token)
    uid = sp.me()['id']
    response = table.get_item(Key={'id': uid})
    print("uid", uid)


    table.update_item(
            Key={
                'id': uid
            },
            UpdateExpression='SET recommendation = :r',
            ExpressionAttributeValues={
                ':r': toggle_value_bool

            }
    )

    print("update")
    print(toggle_value_bool)


    return 'ok'


webapp.run()
