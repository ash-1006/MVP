# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import uuid # To generate unique session IDs
import time

app = Flask(__name__)
# This secret key is needed to manage sessions in Flask
app.secret_key = 'your-super-secret-hackathon-key'

# --- DUMMY DATABASE ---
# In a real app, this would be a database. For the MVP, dictionaries are perfect.
USERS = {
    'teacher': {'password': '1234', 'role': 'teacher', 'name': 'Prof. Ada'},
    'student1': {'password': '1234', 'role': 'student', 'name': 'Grace Hopper'},
    'student2': {'password': '1234', 'role': 'student', 'name': 'Charles Babbage'}
}

# This will store our active attendance sessions
ATTENDANCE_SESSIONS = {}

# --- ROUTES ---

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = USERS.get(username)
        # Check if user exists and password is correct
        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            session['name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Render different dashboards based on user role
    if session['role'] == 'teacher':
        return render_template('teacher_dashboard.html', name=session['name'])
    else:
        return render_template('student_dashboard.html', name=session['name'])

@app.route('/logout')
def logout():
    session.clear() # Clear the session
    return redirect(url_for('login'))

# --- TEACHER-SPECIFIC ROUTES ---

@app.route('/api/create_session', methods=['POST'])
def create_session():
    # Only allow teachers to create sessions
    if session.get('role') != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Generate a unique ID for the session
    session_id = str(uuid.uuid4())
    
    # Store the session with an empty list for attendees
    ATTENDANCE_SESSIONS[session_id] = {
        'attendees': [],
        'timestamp': time.time()
    }
    
    # The URL the student will scan. We pass the server's address.
    # In a real scenario, you'd use your public IP or ngrok address here.
    base_url = request.host_url 
    attendance_url = f"{base_url}attend/{session_id}"
    
    return jsonify({'session_id': session_id, 'url': attendance_url})

@app.route('/api/get_attendance/<session_id>')
def get_attendance(session_id):
    if session.get('role') != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
        
    current_session = ATTENDANCE_SESSIONS.get(session_id)
    if not current_session:
        return jsonify({'error': 'Session not found'}), 404
        
    return jsonify({'attendees': current_session['attendees']})


# --- STUDENT-SPECIFIC ROUTES ---

@app.route('/attend/<session_id>', methods=['GET'])
def mark_attendance_from_qr(session_id):
    # Student must be logged in on their device's browser to mark attendance
    if 'username' not in session or session['role'] != 'student':
        # Redirect to login, but save where they were trying to go
        return redirect(url_for('login', next=request.url))

    current_session = ATTENDANCE_SESSIONS.get(session_id)
    if not current_session:
        return "<h1>Error: Attendance session not found or expired.</h1>", 404

    student_name = session['name']
    
    # Simple check to prevent duplicate marking
    if student_name not in current_session['attendees']:
        current_session['attendees'].append(student_name)
    
    return f"<h1>Welcome, {student_name}!</h1><p>Your attendance has been marked successfully. You can now close this tab.</p>"


if __name__ == '__main__':
    # Use 0.0.0.0 to make it accessible on your local network for QR scanning from a phone
    app.run(host='0.0.0.0', debug=True)