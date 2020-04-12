# spotipy oauth
SPOTIPY_CLIENT_ID = '5ec5a760341246d489abaa3767016822'
SPOTIPY_CLIENT_SECRET = '607c55218f39417a969c7bd89a089207'
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback/'
#SPOTIPY_REDIRECT_URI = 'https://jr8hyu6lsl.execute-api.us-east-1.amazonaws.com/dev/callback/'
SCOPE = 'user-library-read playlist-modify-public user-top-read'
CACHE = '.spotipyoauthcache1'

# aws
S3_REGION = 'us-east-1'
S3_BUCKET = 'ece1779-pj-bucket-new'
S3_URL_PREFIX = 'https://'+S3_BUCKET+'.s3.amazonaws.com'
DYNAMO_USER_TABLE_NAME = 'mugic_user'
DYNAMO_PLAYLIST_TABLE_NAME = 'mugic_playlist'
