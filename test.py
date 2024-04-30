import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Set up Spotify credentials
client_id = '5aedae7298d84cf08129420e03a0e059'
client_secret = 'd3470da294bc478da1c60a351dde56c4'
redirect_uri = 'http://localhost:8888/callback'  

# Authenticate with Spotify API
auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)
