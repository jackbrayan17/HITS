import spotipy
import spotipy.util as util
import pandas as pd

# Your Spotify app credentials
client_id = '5aedae7298d84cf08129420e03a0e059'
client_secret = 'd3470da294bc478da1c60a351dde56c4'
redirect_uri = 'http://localhost:8888/callback'  # This should match the redirect URI set in your Spotify Developer Dashboard

# Set up authentication flow
scope = 'user-library-read'  # Define the scope of access you need
username = 'Jack Brayan'  # Your Spotify username

# Get authentication token
token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)

if token:
    # Authenticate with Spotify API
    sp = spotipy.Spotify(auth=token)
    
    # Define predefined list of genres
    predefined_genres = ['Afrobeat', 'Hip-Hop', 'Pop', 'Rap']
    
    print("Choose a genre:")
    for i, genre in enumerate(predefined_genres, 1):
        print(f"{i}. {genre}")
    
    choice = input("Enter the number corresponding to the genre you want to explore: ")
    
    try:
        choice = int(choice)
        if 1 <= choice <= len(predefined_genres):
            selected_genre = predefined_genres[choice - 1]
            print(f"You've chosen: {selected_genre}")
        else:
            print("Invalid choice. Please enter a number within the range.")
    except ValueError:
        print("Invalid input. Please enter a number.")

    # Retrieve track information for the selected genre
    results = sp.search(q=f'genre:"{selected_genre}"', type='track')
    
    # Initialize an empty list to store track information
    tracks_info = []
    
    # Extract relevant information for each track
    for track in results['tracks']['items']:
        track_info = {
            'Track Name': track['name'],
            'Artist(s)': ', '.join([artist['name'] for artist in track['artists']]),
            'Album Name': track['album']['name'],
            'Release Date': track['album']['release_date'],
            'Genre': selected_genre,
            'Popularity': track['popularity']
        }
        tracks_info.append(track_info)

    # Convert the list of dictionaries into a DataFrame
    tracks_df = pd.DataFrame(tracks_info)

    # Write the DataFrame to a CSV file
    tracks_df.to_csv('music_dataset.csv', index=False)

    print("Music dataset has been successfully created and saved as 'music_dataset.csv'")
else:
    print("Unable to get token for", username)
