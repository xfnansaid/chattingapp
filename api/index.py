from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from supabase import create_client, Client

app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

# Initialize Supabase Client using environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

USERS = {
    "user1": "pass123", 
    "user2": "pass456"
}

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username in USERS and USERS[username] == password:
        session['user'] = username
        return redirect(url_for('chat'))
    return "Invalid credentials", 401

@app.route('/chat')
def chat():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('chat.html', current_user=session['user'])

@app.route('/send', methods=['POST'])
def send_message():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    
    # Insert message into Supabase
    message_data = {
        "sender": session['user'],
        "text": data['text']
    }
    supabase.table("messages").insert(message_data).execute()
    
    return jsonify({"success": True})

@app.route('/messages')
def get_messages():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Fetch last 50 messages, ordered by creation time
        response = (
            supabase.table("messages")
            .select("sender, text")
            .order("created_at", desc=False) # <--- The bug is fixed here
            .limit(50)
            .execute()
        )
        return jsonify(response.data)
        
    except Exception as e:
        # If any other error happens, this will catch it and send it to your screen
        return str(e), 500
