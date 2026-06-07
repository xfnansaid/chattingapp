from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from supabase import create_client, Client

app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
else:
    print("WARNING: SUPABASE_URL or SUPABASE_KEY not configured.")
    print("Running in LOCAL IN-MEMORY MOCK MODE for global chat messages.")

# In-memory fallback database for local testing
MOCK_MESSAGES = [
    {"sender": "System", "text": "Supabase offline. In-memory message backup active."}
]

USERS = {
    "xfnkl52": "XkumbaKunja@1.3", 
    "sankjj": "xfnsankjj@1.3"
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
    
    # Insert message into database
    message_data = {
        "sender": session['user'],
        "text": data['text']
    }
    
    if supabase:
        try:
            supabase.table("messages").insert(message_data).execute()
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        MOCK_MESSAGES.append(message_data)
        if len(MOCK_MESSAGES) > 50:
            MOCK_MESSAGES.pop(0)
            
    return jsonify({"success": True})

@app.route('/messages')
def get_messages():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if supabase:
        try:
            # Fetch last 50 messages, ordered by creation time
            response = (
                supabase.table("messages")
                .select("sender, text")
                .order("created_at", desc=False)
                .limit(50)
                .execute()
            )
            return jsonify(response.data)
        except Exception as e:
            return str(e), 500
    else:
        return jsonify(MOCK_MESSAGES)
