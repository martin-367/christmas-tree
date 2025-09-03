import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="4bde9deafa664b0fb1398ca7cdd0c9c1",
    client_secret="93c308c1a9d74793ae0aa617d8e594eb",
    redirect_uri="http://127.0.0.1:3000",
    scope="user-read-playback-state,user-modify-playback-state"
))

# Example: get currently playing track
track = sp.current_playback()
print(track)
