// script.js
document.addEventListener("DOMContentLoaded", function() {
    const playButtons = document.querySelectorAll('.play-btn');
    
    playButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const spotifyUri = this.getAttribute('data-uri');
            
            try {
                // Fetch access token from Spotify API
                const response = await fetch('https://accounts.spotify.com/api/token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Authorization': 'Basic ' + btoa('5aedae7298d84cf08129420e03a0e059:d3470da294bc478da1c60a351dde56c4')
                    },
                    body: 'grant_type=client_credentials'
                });

                const data = await response.json();
                const accessToken = data.access_token;

                // Play song using the access token
                const audio = new Audio();
                audio.src = `https://api.spotify.com/v1/tracks/${spotifyUri}`;
                audio.crossOrigin = 'anonymous';
                audio.setAttribute('type', 'audio/mpeg');
                audio.setAttribute('preload', 'auto');
                audio.setAttribute('controls', 'controls');
                audio.setAttribute('autoplay', 'autoplay');
                audio.setAttribute('token', accessToken);
                document.body.appendChild(audio);
            } catch (error) {
                console.error('Error:', error);
            }
        });
    });
});
// slice
function showMore() {
    var songs = document.querySelectorAll('.song');
    for (var i = 5; i < songs.length; i++) {
        songs[i].style.display = 'block';
    }
    var moreButton = document.querySelector('button');
    moreButton.style.display = 'none';
}