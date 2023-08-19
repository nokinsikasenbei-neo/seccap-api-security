from flask import Flask, render_template, request, redirect, session, url_for
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
        response = requests.post(f"{BASE_URL}/user/register/", json={"username": username, "password": password})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # APIにPOSTリクエストを送信
        response = requests.post(f"{BASE_URL}/user/login/", data={
            "username": username,
            "password": password,
            "grant_type": "", 
            "scope": "", 
            "client_id": "", 
            "client_secret": ""
        })
        session['token'] = response.json()["access_token"]
        return redirect(url_for('timeline'))
    return render_template('login.html')

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'token' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        is_private = 'is_private' in request.form
        headers = {"Authorization": f"Bearer {session['token']}"}
        response = requests.post(f"{BASE_URL}/post/create", headers=headers, json={
            "title": title, 
            "content": content, 
            "is_private": is_private
        })
        return redirect(url_for('timeline'))
    return render_template('create_post.html')

@app.route('/')
def timeline():
    if 'token' not in session:
        return redirect(url_for('login'))
    headers = {"Authorization": f"Bearer {session['token']}"}
    response = requests.get(f"{BASE_URL}/posts/", headers=headers)
    posts = response.json()
    return render_template('timeline.html', posts=posts)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    if 'token' not in session:
        return redirect(url_for('login'))
    headers = {"Authorization": f"Bearer {session['token']}"}
    response = requests.get(f"{BASE_URL}/post/{post_id}/", headers=headers)
    post = response.json()
    return render_template('view_post.html', post=post[0])

@app.route('/my_page')
def my_page():
    if 'token' not in session:
        return redirect(url_for('login'))
    headers = {"Authorization": f"Bearer {session['token']}"}
    response = requests.get(f"{BASE_URL}/user/image/", headers=headers)
    response_json = response.json()
    if response_json.get("image_url") is None:
        image_url = "https://via.placeholder.com/150"
        return render_template('my_page.html', image_url=image_url)
    image_url = response_json["image_url"]
    return render_template('my_page.html', image_url=image_url)

if __name__ == '__main__':
    app.run(debug=True)
