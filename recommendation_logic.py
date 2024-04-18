import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import csv

# Spotify API credentials
CLIENT_ID = '5aedae7298d84cf08129420e03a0e059'
CLIENT_SECRET = 'd3470da294bc478da1c60a351dde56c4'


# Initialize Spotipy client
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=CLIENT_ID,client_secret=CLIENT_SECRET))

# Dictionary mapping genres to artists
genre_artists = {
    'Pop': ['Adele', 'Doja Cat', 'Camilla Cabello', 'Halsey', 'Usher', 'Beyonce', 'Michael Jackson', 'The Weeknd',
            'Ariane Grande', 'Dadju', 'Bruno Mars', 'Aya Nakamura'],
    'Rap': ['Jay-Z', '21 Savage', 'Kendrick Lamar', 'Cardi B', '50 Cent', 'Jack Harlow', 'Pop Smoke', 'Metro Boomin',
            'Gunna', 'Drake', 'J. Cole', 'Travis Scott', 'Migos', 'Offset', 'Quavo', 'Baby Keem', 'Rae Sremmurd',
            'Ninho', 'Damso', 'SDM', 'Lil Baby', 'Post Malone', 'Roddy Ricch'],
    'Hip-hop': ['Gazo', 'Russ', '4batz', 'Yame', 'Kaza', 'Dave', 'Niska', 'Tiakola', 'Chris Brown', 'Usher', 'SDM',
                'Dosseh', 'Niska', 'Dadju', 'Yame', '50 Cent', 'Takeoff'],
    'RnB': ['Akon', 'SZA', 'Chris Brown', 'Tory Lanez', 'Rihanna', 'Summer Walker', 'Bryson Tiller', 'Brent Faiyaz',
            '6lack', 'Khalid'],
    'Gospel': ['Mercy Chinwo', 'Moses Bliss', 'Franck Edward', 'Eboucka Songs'],
    'Afrobeat': ['Burna Boy', 'Oxlade', 'Victony', 'Gabzy', 'Olamide', 'Crayon', 'Ruger', 'Joeboy', 'Omah Lay',
                 'Davido', 'Wizkid', 'Ayra Starr', 'Rema', 'Asake', 'Tems', 'Bnxn', 'Khaid', 'Cysoul', 'Fally Ipupa',
                 'P-Square']
}

# Function to fetch songs for each artist and write to CSV
def fetch_songs_to_csv():
    with open('hits.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['song_name', 'artist', 'genre', 'popularity', 'release_date', 'music_link', 'track_id', 'image',
                         'duration_ms', 'explicit', 'external_urls', 'danceability', 'energy', 'key', 'loudness',
                         'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo'])

        for genre, artists in genre_artists.items():
            for artist in artists:
                results = sp.search(q=f'artist:{artist}', type='track', limit=25)
                for track in results['tracks']['items']:
                    song_name = track['name']
                    artists = ', '.join([artist['name'] for artist in track['artists']])
                    popularity = track['popularity']
                    release_date = track['album']['release_date']
                    music_link = track['external_urls']['spotify']
                    track_id = track['id']
                    image = track['album']['images'][0]['url']

                    # Additional features
                    audio_features = sp.audio_features(track_id)[0]
                    duration_ms = audio_features['duration_ms']
                    explicit = track.get('explicit', None)
                    external_urls = track.get('external_urls', {}).get('spotify', None)
                    danceability = audio_features['danceability']
                    energy = audio_features['energy']
                    key = audio_features['key']
                    loudness = audio_features['loudness']
                    mode = audio_features['mode']
                    speechiness = audio_features['speechiness']
                    acousticness = audio_features['acousticness']
                    instrumentalness = audio_features['instrumentalness']
                    liveness = audio_features['liveness']
                    valence = audio_features['valence']
                    tempo = audio_features['tempo']

                    writer.writerow([song_name, artists, genre, popularity, release_date, music_link, track_id, image,
                                     duration_ms, explicit, external_urls, danceability, energy, key, loudness,
                                     mode, speechiness, acousticness, instrumentalness, liveness, valence, tempo])

# Fetch songs and write to CSV
fetch_songs_to_csv()
