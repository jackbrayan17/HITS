from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import sqlite3
import os
import json  # Add JSON module for serialization/deserialization
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd
import random
import datetime
from werkzeug.utils import secure_filename
import requests

UPLOAD_FOLDER = 'static/profile_pictures'
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png','jpg','jpeg','jfif','gif'}

os.makedirs(app.config['UPLOAD_FOLDER'],exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('app.db')
    return db


# Function to close the database connection at the end of the request
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Create users table
def update_following_count(username):
    with app.app_context():
        db=get_db()
        cur = db.cursor()
        cur.execute('''SELECT COUNT(*) FROM user_relationships WHERE follower_id = ?''', (username,))

        following_count = cur.fetchone()[0]
        cur.execute('''UPDATE users SET following_count = ? WHERE username=?''',(following_count,username))
        db.commit()
def init_db():
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        age INTEGER,
                        country TEXT,
                        sex TEXT,
                        email TEXT,
                        relationship_status TEXT,
                        preferred_genres TEXT,
                        following_count INTEGER
                    )''')
        db.commit()

def init_db_recommendations():
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS recommendations (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        song_name TEXT,
                        artist TEXT,
                        genre TEXT,
                        popularity INTEGER,
                        release_date TEXT,
                        music_link TEXT,
                        track_id TEXT,
                        image TEXT,
                        date_added DATE,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )''')
        db.commit()

init_db_recommendations()

# Create user_genres table
def init_db_user_genres():
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS user_genres (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        genre TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )''')
        db.commit()


# Create user_relationships table
def init_db_user_relationships():
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS user_relationships (
                        id INTEGER PRIMARY KEY,
                        follower_id INTEGER NOT NULL,
                        followed_id INTEGER NOT NULL,
                        follow_date TEXT, 
                        FOREIGN KEY (follower_id) REFERENCES users (id),
                        FOREIGN KEY (followed_id) REFERENCES users (id)
                    )''')
        db.commit()


init_db()
init_db_user_genres()
init_db_user_relationships()


# Define authentication function
def authenticate(username, password):
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        if user:
            return True
        return False


def get_follower_recommendations(user_id):
    with app.app_context():
        db = get_db()
        cur = db.cursor()

        # Fetch followed users
        cur.execute('''SELECT followed_id FROM user_relationships WHERE follower_id = ?''', (user_id,))
        followed_users = cur.fetchall()

        # Fetch recommendations for each followed user
        follower_recommendation = []
        for followed_user in followed_users:
            cur.execute('''SELECT * FROM recommendations WHERE user_id = ?''', (followed_user[0],))
            recommendations = cur.fetchall()
            follower_recommendation.extend(recommendations)

        return follower_recommendation

# Define route to show followed users
@app.route('/show_followed_users')
def show_followed_users():
    if 'logged_in' in session and session['logged_in']:
        # Get the username of the currently logged-in user
        username = session['username']
        db = get_db()
        cur = db.cursor()
        # Query the database to retrieve the list of users that the current user is following
        cur.execute('''SELECT users.username
                       FROM users
                       JOIN user_relationships ON users.id = user_relationships.followed_id
                       WHERE user_relationships.follower_id = ?''', (session['user_id'],))
        followed_users = cur.fetchall()
        # Render a template to display the followed users
        return render_template('followed_users.html', username=username, followed_users=followed_users)
    else:
        return redirect(url_for('login_form'))


# Define route to search users
@app.route('/search_users', methods=['GET', 'POST'])
def search_users():

    if request.method == 'POST':
        search_query = request.form.get('search_query', '')
        print("Search Query:", search_query)  # Debugging statement
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username LIKE ?", ('%' + search_query + '%',))
        search_results = cur.fetchall()
        print("Search Results:", search_results)  # Debugging statement
        return render_template('search_users.html', search_results=search_results)
    return render_template('search_users.html', search_results=[])

@app.route('/follow/<username>', methods=['GET', 'POST'])
def follow_user(username):

    if 'username' not in session:
        flash('You need to be logged in to follow users', 'error')
        return redirect(url_for('login_form'))
    update_following_count(session['username'])

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('show_recommendations'))

    if request.method == 'POST':
        cur.execute('''SELECT * 
                       FROM user_relationships 
                       WHERE follower_id = ? AND followed_id = ?''', (session['user_id'], user[0]))
        relationship = cur.fetchone()
        if relationship:
            flash('You are already following this user', 'info')
        else:
            current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute('''INSERT INTO user_relationships (follower_id, followed_id, follow_date) 
                           VALUES (?, ?, ?)''', (session['user_id'], user[0], current_datetime))
            db.commit()
            flash(f'You are now following {username}', 'success')

            return redirect(url_for('show_recommendations'))

    # Handle GET request here
    # This can be used to render a confirmation page or perform other actions
    return redirect(url_for('show_recommendations'))
# Route to unfollow a user
@app.route('/unfollow/<username>')
def unfollow(username):

    if 'username' not in session:
        flash('You need to be logged in to unfollow users', 'error')
        return redirect(url_for('login_form'))
    update_following_count(session['username'])

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('show_recommendations'))

    cur.execute('''DELETE FROM user_relationships 
                   WHERE follower_id = ? AND followed_id = ?''', (session['user_id'], user[0]))
    db.commit()
    flash(f'You have unfollowed {username}', 'success')

    return redirect(url_for('show_recommendations'))

# Define function to check if username is taken
def is_username_taken(username):
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user:
            return True
        return False


# Define function to get recommendations based on preferred genres
song_dataset = pd.read_csv('songs.csv')


# Define function to get recommendations based on preferred genres
def get_recommendations(preferred_genres, user_profile):
    print("Preferred genres:", preferred_genres)
    preferred_genres_l = [genre.lower() for genre in preferred_genres]
    genre_filter = song_dataset['genre'].str.lower().isin(preferred_genres_l)
    genre_songs = song_dataset[genre_filter].copy()

    print("Number of songs after filtering:", len(genre_songs))
    if genre_songs.empty:
        print("No songs match the preferred genres.")
        return []

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(genre_songs['genre'])

    print("Shape of TF-IDF matrix:", tfidf_matrix.shape)

    if tfidf_matrix.shape[1] == 0:
        print("Empty TF-IDF matrix.")
        return []

    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    user_profile_vector = tfidf.transform([user_profile])

    cosine_scores = linear_kernel(user_profile_vector, tfidf_matrix).flatten()

    print("Cosine similarity scores:", cosine_scores)

    recommendations_indices = cosine_scores.argsort()[:-11:-1]

    recommendations = genre_songs.iloc[recommendations_indices]
    print("Recommendations:", recommendations)

    # Adding user_id to recommendations
    for index, recommendation in recommendations.iterrows():
        recommendation_data = {
            'user_id': session['user_id'],
            'song_name': recommendation['song_name'],
            'artist': recommendation['artist'],
            'genre': recommendation['genre'],
            'popularity': recommendation['popularity'],
            'release_date': recommendation['release_date'],
            'music_link': recommendation['music_link'],
            'track_id': recommendation['track_id'],
            'image': recommendation['image'],
            'date_added': datetime.datetime.now().strftime("%Y-%m-%d")
        }
        # Insert recommendation into database
        with app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute('''INSERT INTO recommendations 
                               (user_id, song_name, artist, genre, popularity, release_date, music_link, track_id, image, date_added) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (
                        recommendation_data['user_id'], recommendation_data['song_name'], recommendation_data['artist'],
                        recommendation_data['genre'], recommendation_data['popularity'],
                        recommendation_data['release_date'],
                        recommendation_data['music_link'], recommendation_data['track_id'],
                        recommendation_data['image'],
                        recommendation_data['date_added']))
            db.commit()
    return recommendations.to_dict('records')


# Define route to show signup form
@app.route('/')
def signup_form():
    return render_template('signup.html')


@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    age = request.form['age']
    username = request.form['username']
    country = request.form['country']
    sex = request.form['sex']
    email = request.form['email']
    relationship_status = request.form['relationship_status']
    preferred_genres = json.dumps(request.form.getlist('preferred_genres'))  # Serialize preferred_genres using JSON
    password = request.form['password']

    # Check if the POST request has the file part
    if 'profile_picture' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['profile_picture']

    # If the user does not select a file, the browser submits an empty file without a filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    # If the file is allowed and not empty, save it
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = f"{username}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.split('.')[-1]}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Insert user data into the database
    with sqlite3.connect('app.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users (username, password, age, country, sex, email, relationship_status, preferred_genres, images)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (username, password, age, country, sex, email, relationship_status, preferred_genres, filename))
        conn.commit()

    # if is_username_taken(username):
    #     return 'Username already exists, please choose another.'

    return redirect(url_for('login_form'))


# Define function to fetch user's preferred genres
def get_user_preferred_genres(username):
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT preferred_genres FROM users WHERE username = ?", (username,))
        user_row = cur.fetchone()
        if user_row:
            return json.loads(user_row[0])  # Deserialize preferred_genres using JSON
        return []


# Define route to handle login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if authenticate(username, password):
        session['logged_in'] = True
        session['username'] = username
        # Fetch user's preferred genres and store in session
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user:
            session['user_id'] = user[0]
            session['user_profile'] = user[0]
            print("Profile picture filename:", session['user_profile'])
        session['preferred_genres'] = get_user_preferred_genres(username)

        return redirect(url_for('show_recommendations'))
    else:
        return 'Invalid username or password'


# Define route to show login form
@app.route('/login')
def login_form():
    return render_template('login.html')


# Define route to handle logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login_form'))


# Define route to show recommendations
@app.route('/show_recommendations')
def show_recommendations():
    if 'logged_in' in session and session['logged_in']:
        username = session['username']
        # profile_pic = session['images']
        user_id = session['user_id']
        preferred_genres = session.get('preferred_genres', [])
        if not preferred_genres:
            print("Preferred genres:", preferred_genres)
            return 'No preferred genres found. Please sign up or login.'

        user_profile = session.get('images', '')  # Modify this according to how user profile is stored
        print("User profile:", user_profile)

        recommendations = get_recommendations(preferred_genres, user_profile)
        follower_recommendation = get_follower_recommendations(session['user_id'])
        if recommendations:
            random.shuffle(recommendations)


            for genre in preferred_genres:
                db = get_db()
                cur = db.cursor()
                cur.execute('''INSERT INTO user_genres (user_id, genre) VALUES (?, ?)''', (session['user_id'], genre))
                db.commit()
            print("Recommendations:", recommendations)
            print("Follower Rec.: ", follower_recommendation)
            db = get_db()
            cur = db.cursor()
            cur.execute('''SELECT users.username
                                       FROM users
                                       JOIN user_relationships ON users.id = user_relationships.followed_id
                                       WHERE user_relationships.follower_id = ?''', (session['user_id'],))
            followed_users = cur.fetchall()
            cur.execute('''SELECT users.username
                                                   FROM users
                                                   JOIN user_relationships ON users.id = user_relationships.follower_id
                                                   WHERE user_relationships.followed_id = ?''', (session['user_id'],))
            follower_users = cur.fetchall()
            follower_users = [user for user in follower_users if user not in followed_users ]

            return render_template('recommendation.html', username=username, recommendations=recommendations,followed_users=followed_users,follower_users=follower_users,follower_recommendation=follower_recommendation,user_profile=user_profile)
        else:
            print("No recommendations available.")
            return 'No recommendations available.'
    else:
        return redirect(url_for('login_form'))


if __name__ == '__main__':
    app.run(debug=True)
