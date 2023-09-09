from flask import Flask, render_template, request, redirect, session, url_for, flash
import logging
import requests
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
logging.basicConfig(level=logging.INFO)

BASE_URL = "http://api:8000"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            response = requests.post(f"{BASE_URL}/user/register", json={"username": username, "password": password})
            response.raise_for_status()  # raises exception when not a 2xx response
        except requests.RequestException as e:
            logging.error(e)
            flash("Registration failed. Please try again.")
            return render_template('register.html')
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            response = requests.post(f"{BASE_URL}/user/login", data={
                "username": username,
                "password": password,
                "grant_type": "", 
                "scope": "", 
                "client_id": "", 
                "client_secret": ""
            })
            response.raise_for_status()
            session['token'] = response.json().get("access_token")
            if not session['token']:
                flash("Failed to get token. Please try again.")
                return render_template('login.html')
        except requests.RequestException as e:
            logging.error(e)
            flash("Login failed. Please try again.")
            return render_template('login.html')

        return redirect(url_for('timeline'))
    return render_template('login.html')

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'token' not in session:
        flash("Please login first.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        is_private = 'is_private' in request.form
        headers = {"Authorization": f"Bearer {session['token']}"}
        
        try:
            response = requests.post(f"{BASE_URL}/post/create", headers=headers, json={
                "title": title, 
                "content": content, 
                "is_private": is_private
            })
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(e)
            flash("Failed to create post. Please try again.")
            return render_template('create_post.html')

        return redirect(url_for('timeline'))
    return render_template('create_post.html')

@app.route('/')
def timeline():
    if 'token' not in session:
        flash("Please login first.")
        return redirect(url_for('login'))
    headers = {"Authorization": f"Bearer {session['token']}"}
    try:
        response = requests.get(f"{BASE_URL}/posts", headers=headers)
        response.raise_for_status()
        posts = response.json()
    except requests.RequestException as e:
        logging.error(e)
        flash("Failed to fetch timeline. Please try again.")
        return redirect(url_for('login'))

    return render_template('timeline.html', posts=posts)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    if 'token' not in session:
        flash("Please login first.")
        return redirect(url_for('login'))
    headers = {"Authorization": f"Bearer {session['token']}"}
    try:
        response = requests.get(f"{BASE_URL}/post/{post_id}", headers=headers)
        response.raise_for_status()
        post = response.json()
    except requests.RequestException as e:
        logging.error(e)
        flash("Failed to fetch post. Please try again.")
        return redirect(url_for('timeline'))

    return render_template('view_post.html', post=post)

@app.route('/my_page')
def my_page():
    if 'token' not in session:
        flash("Please login first.")
        return redirect(url_for('login'))
    headers = {"Authorization": f"Bearer {session['token']}"}
    try:
        response = requests.get(f"{BASE_URL}/user/image", headers=headers)
        response.raise_for_status()
        response_json = response.json()
        image_url = response_json.get("image_url", "https://via.placeholder.com/150")
    except requests.RequestException as e:
        logging.error(e)
        flash("Failed to fetch user data. Please try again.")
        return redirect(url_for('timeline'))

    return render_template('my_page.html', image_url=image_url)

if __name__ == '__main__':
    app.run(debug=True)
