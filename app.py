import os
import logging
import re
import json
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import custom modules
from chatbot import Chatbot
from user_management import UserManager
from models import Admin, User as UserModel, LoginLog
from extensions import db
from database import email_directory
from update_chatbot import ChatbotDB

app = Flask(__name__)
app.template_folder = 'htdocs'
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Add SQLAlchemy configuration for MySQL
mysql_url = os.environ.get('MYSQL_URL')
if mysql_url and mysql_url.startswith('mysql://'):
    mysql_url = mysql_url.replace('mysql://', 'mysql+pymysql://', 1)

# Database URLs - separate databases for different data types
# User data database (doran) - users, feedback, guests, chat history, etc.
local_user_db_url = 'mysql+pymysql://root:@localhost/doran'
railway_user_db_url = 'mysql+pymysql://root:smxcYzdpwUJTAiRdJWQFPJNbfsbVTAGC@trolley.proxy.rlwy.net:10349/doran_db'

# Chatbot data database (chatbot_db) - rules, categories, locations, visuals, etc.
local_chatbot_db_url = 'mysql+pymysql://root:@localhost/chatbot_db'
railway_chatbot_db_url = 'mysql+pymysql://root:smxcYzdpwUJTAiRdJWQFPJNbfsbVTAGC@trolley.proxy.rlwy.net:10349/chatbot_db'

# Try local databases first, fallback to Railway
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or mysql_url or local_user_db_url
app.config['CHATBOT_DATABASE_URI'] = os.environ.get('CHATBOT_DATABASE_URL') or local_chatbot_db_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False  # Disable SQL echo for cleaner logs
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Check connection before using
    'pool_recycle': 300,    # Recycle connections after 5 minutes
    'pool_size': 1,         # Very small pool size for reliability
    'max_overflow': 2,      # Minimal overflow connections
    'pool_timeout': 10,     # Shorter timeout
    'connect_args': {
        'connect_timeout': 5,  # Shorter connect timeout
        'read_timeout': 10,    # Shorter read timeout
        'write_timeout': 10,   # Shorter write timeout
    }
}

# Configure binds for multiple databases
app.config['SQLALCHEMY_BINDS'] = {
    'chatbot_db': app.config['CHATBOT_DATABASE_URI']
}

# Create separate engine for chatbot database
from sqlalchemy import create_engine
chatbot_engine = create_engine(app.config['CHATBOT_DATABASE_URI'], **app.config['SQLALCHEMY_ENGINE_OPTIONS'])

# Connection pool settings to handle connection drops
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600  # Recycle connections every hour
app.config['SQLALCHEMY_POOL_PRE_PING'] = True  # Check connection before use

# File upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads', 'locations')
app.config['VISUALS_UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads', 'visuals')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
<<<<<<< HEAD
    # Retry database table creation up to 5 times with exponential backoff
    max_retries = 5
    for attempt in range(max_retries):
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
            break  # Success, exit retry loop
        except Exception as e:
            app.logger.warning(f"Database table creation attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                import time
                delay = 2 ** attempt  # Exponential backoff: 1, 2, 4, 8 seconds
                app.logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                continue
            else:
                app.logger.error(f"Failed to create database tables after {max_retries} attempts: {str(e)}")
                # Don't raise exception, allow app to continue

    # Initialize user manager with retry logic
    user_manager = UserManager(db)
=======
    try:
        db.create_all()
        app.logger.info("Database tables created successfully")
    except Exception as e:
        app.logger.error(f"Error creating database tables: {str(e)}")
        # Don't initialize user_manager if DB connection fails
        user_manager = None
    else:
        user_manager = UserManager(db)
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82

# Auto-upload JSON files to Railway volume on startup
def auto_upload_json_files():
    """
    Automatically copy JSON files from local database directory to Railway volume (/app/database)
    if the volume is mounted and writable.
    """
    import shutil

    volume_path = '/app/database'
    local_db_path = os.path.join(app.root_path, 'database')

    # Check if volume is mounted and writable
    if os.path.exists(volume_path) and os.access(volume_path, os.W_OK):
        app.logger.info("Railway volume detected at /app/database, copying JSON files...")

        # Ensure volume subdirectories exist
        for subdir in ['user_database', 'guest_database', 'visuals', 'locations', 'feedback']:
            vol_subdir = os.path.join(volume_path, subdir)
            os.makedirs(vol_subdir, exist_ok=True)

        # Copy all JSON files from local database to volume
        for root, dirs, files in os.walk(local_db_path):
            for file in files:
                if file.endswith('.json'):
                    local_file = os.path.join(root, file)
                    # Get relative path from database directory
                    rel_path = os.path.relpath(local_file, local_db_path)
                    volume_file = os.path.join(volume_path, rel_path)

                    try:
                        # Ensure destination directory exists
                        os.makedirs(os.path.dirname(volume_file), exist_ok=True)
                        # Copy file
                        shutil.copy2(local_file, volume_file)
                        app.logger.info(f"Copied {rel_path} to volume")
                    except Exception as e:
                        app.logger.error(f"Failed to copy {rel_path}: {str(e)}")

        # Update chatbot to use volume paths if available
        if os.path.exists(volume_path):
            app.logger.info("JSON files uploaded to Railway volume successfully")
    else:
        app.logger.info("Railway volume not detected or not writable, using local files")

# Run auto-upload before initializing chatbot
auto_upload_json_files()

<<<<<<< HEAD
# Initialize chatbot within app context
with app.app_context():
    chatbot = Chatbot()  # Rules are now loaded from MySQL automatically
=======
# Initialize chatbot first (works with local JSON files)
chatbot = Chatbot()  # Rules are now loaded from soict.py automatically
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82

# Initialize database connection for admin operations (may fail, but app can still run)
try:
    chatbot_db = ChatbotDB()
    app.logger.info("Database connection established successfully")
except Exception as e:
    app.logger.error(f"Failed to connect to database: {str(e)}")
    chatbot_db = None

@login_manager.user_loader
def load_user(user_id):
    """
    Load user by ID for Flask-Login.
    """
    try:
        user_type = session.get('user_type')
        if user_type == 'admin':
            admin = Admin.query.get(int(user_id))
            if admin:
                return admin
        elif user_type == 'user':
            user = user_manager.get_user_by_id(user_id)
            if user:
                return user
    except Exception as e:
        app.logger.error(f"Database error in load_user: {str(e)}")
    return None

def is_admin(user):
    """
    Helper function to check if a user is an admin.
    """
    if user is None:
        return False
    if isinstance(user, Admin):
        return True
    if hasattr(user, 'role') and user.role == 'admin':
        return True
    return False

def retry_db_operation(operation, max_retries=3, delay=1):
    """
    Retry a database operation with exponential backoff.
    """
    import time
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if attempt < max_retries - 1:
                app.logger.warning(f"Database operation failed (attempt {attempt + 1}): {str(e)}")
                time.sleep(delay * (2 ** attempt))
            else:
                app.logger.error(f"Database operation failed after {max_retries} attempts: {str(e)}")
                raise

@app.route('/favicon.ico')
def favicon():
    """
    Suppress favicon requests by returning 204 No Content.
    """
    return '', 204

@app.route('/welcome')
def welcome_api():
    """
    Returns a welcome message via API.
    """
    app.logger.info(f"Request received: {request.method} {request.path}")
    return jsonify({'message': 'Welcome to the Flask API Service!'})

@app.route('/')
def welcome():
    """
    Render the welcome page.
    """
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login for regular users and guests.
    """
    user_type = request.args.get('user_type', 'user')
    if request.method == 'POST':
        if user_type == 'guest':
            username = request.form.get('username')
            if not username:
                flash('Please enter a username', 'danger')
                return render_template('login.html', user_type=user_type)
            session['guest_username'] = username
            session['user_type'] = 'guest'
            session['logged_in'] = True
            # Log guest login
            login_log = LoginLog(user_type='guest', identifier=username)
            db.session.add(login_log)
            db.session.commit()
            flash('Guest login successful!', 'success')
            return redirect(url_for('chat'))
        else:
            username_or_email = request.form.get('username') or request.form.get('email')
            password = request.form.get('password')

            if not username_or_email or not password:
                flash('Please enter both username/email and password', 'danger')
                return render_template('login.html', user_type=user_type)

            user = UserModel.query.filter(
                (UserModel.username == username_or_email) |
                (UserModel.email == username_or_email)
            ).first()

            if user and user.check_password(password.strip()):
                if not user.is_confirmed:
                    flash('Your account is pending admin confirmation. Please wait for approval.', 'warning')
                    return redirect(url_for('login', user_type='user'))
                login_user(user, remember=True)
                session['user_id'] = user.id
                session['user_type'] = 'user'
                session['logged_in'] = True
                # Log user login
                login_log = LoginLog(user_type='user', identifier=user.email)
                db.session.add(login_log)
                db.session.commit()
                flash('Login successful!', 'success')
                return redirect(url_for('chat'))

            flash('Invalid username or password')
    return render_template('login.html', user_type=user_type)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """
    Handle admin login.
    """
    from models import Admin as AdminModel
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please enter both email and password', 'danger')
            return render_template('admin_login.html')

        try:
            def get_admin():
                return AdminModel.query.filter_by(email=email).first()

            admin = retry_db_operation(get_admin)

            if admin and admin.check_password(password.strip()):
                login_user(admin, remember=True)
                session['user_id'] = admin.id
                session['user_type'] = 'admin'
                session['logged_in'] = True
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard'))

            flash('Invalid username or password')
        except Exception as e:
            app.logger.error(f"Database error during admin login: {str(e)}")
            flash('Database connection error. Please try again later.', 'danger')
    return render_template('admin_login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Handle user signup with validation.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not email or not re.match(r'^[^@]+@wvsu\.edu\.ph$', email):
            flash('Email must be a wvsu.edu.ph email address', 'danger')
            return render_template('signup.html')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')

        existing_user_email = user_manager.get_user_by_email(email)
        if existing_user_email:
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('login', user_type='user'))

        existing_user_username = user_manager.get_user_by_username(username)
        if existing_user_username:
            flash('Username already taken. Please choose another.', 'danger')
            return render_template('signup.html')

        # Create user with is_confirmed=False
        user = user_manager.create_user(username, email, password, 'user')
        # Set is_confirmed to False explicitly (in case create_user does not set it)
        user.is_confirmed = False
        user_manager.db.session.commit()

        flash('Account created! Please wait for admin confirmation before logging in.', 'info')
        return redirect(url_for('login', user_type='user'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    """
    Log out the current user or guest.
    """
    if current_user.is_authenticated:
        logout_user()
    if 'guest_username' in session:
        session.pop('guest_username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('welcome'))

@app.route('/chat')
def chat():
    """
    Render the chat page with user info and chat history.
    """
    from database import email_directory

    username = None
    role = session.get('user_type', 'guest')

    # Debug logging for role and authentication
    # app.logger.debug(f"User role in session: {role}")
    # app.logger.debug(f"Current user authenticated: {current_user.is_authenticated}")

    if current_user.is_authenticated:
        if role == 'admin':
            username = current_user.email
        elif role == 'user':
            username = current_user.username
        else:
            # Handle other user types safely
            if hasattr(current_user, 'username'):
                username = current_user.username
            elif hasattr(current_user, 'email'):
                username = current_user.email
            else:
                username = str(current_user.id)  # Fallback to user ID
    elif 'guest_username' in session:
        username = session['guest_username']
    else:
        return redirect(url_for('welcome'))

    session_date = request.args.get('session_date')
    chat_history = None
    chat_sessions_summary = None

    if current_user.is_authenticated and role == 'user':
        chat_sessions_summary = user_manager.get_chat_sessions_summary(current_user.id)
        if session_date:
            try:
                selected_date = datetime.strptime(session_date, "%Y-%m-%d").date()
            except ValueError:
                selected_date = None

            if selected_date:
                full_history = user_manager.get_chat_history(current_user.id)
                if selected_date in full_history:
                    chat_history = full_history[selected_date]
        else:
            chat_history = None

    emails = email_directory.get_all_emails()

    return render_template(
        'chat.html', username=username, role=role,
        chat_history=chat_history, chat_sessions_summary=chat_sessions_summary,
        emails=emails
    )

@app.route('/send_message', methods=['POST'])
def send_message():
    """
    Handle sending a message from the user and return chatbot response.
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', '')
        user_role = session.get('user_type', None)
        bot_response = chatbot.get_response(user_message, user_role=user_role)

        if current_user.is_authenticated and isinstance(current_user, UserModel) and session_id:
            user_manager.add_chat_message(current_user.id, session_id, 'user', user_message)
            user_manager.add_chat_message(current_user.id, session_id, 'bot', bot_response)
        elif 'guest_username' in session and session_id:
            # Store guest messages directly in database
            from models import ChatMessage
            guest_username = session['guest_username']
            guest_user_message = ChatMessage(
                user_id=None,
                guest_username=guest_username,
                session_id=session_id,
                sender_type='user',
                message=user_message
            )
            guest_bot_message = ChatMessage(
                user_id=None,
                guest_username=guest_username,
                session_id=session_id,
                sender_type='bot',
                message=bot_response
            )
            db.session.add(guest_user_message)
            db.session.add(guest_bot_message)
            db.session.commit()

        return jsonify({
            'response': bot_response,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        app.logger.error(f"Error in send_message: {e}")
        return jsonify({
            'response': "I'm sorry, I encountered an error. Please try again.",
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@app.route('/clear_history', methods=['POST'])
@login_required
def clear_history():
    """
    Clear chat history for the current user.
    """
    user_manager.clear_chat_history(current_user.id)
    return jsonify({'status': 'success'})

@app.route('/get_chat_history')
@login_required
def get_chat_history():
    """
    Get chat history for the current user.
    """
    history = user_manager.get_chat_history(current_user.id)
    return jsonify(history)

@app.route('/get_chat_sessions_summary')
@login_required
def get_chat_sessions_summary():
    """
    Get chat sessions summary for sidebar display.
    """
    sessions = user_manager.get_chat_sessions_summary(current_user.id)
    return jsonify(sessions)

@app.route('/get_chat_session_history/<session_id>')
@login_required
def get_chat_session_history(session_id):
    """
    Get full chat history for a specific session.
    """
    history = user_manager.get_chat_session_history(current_user.id, session_id)
    return jsonify(history)

@app.route('/delete_chat_session/<session_id>', methods=['DELETE'])
@login_required
def delete_chat_session(session_id):
    """
    Delete a chat session and all its messages.
    """
    success = user_manager.delete_chat_session(current_user.id, session_id)
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Session not found or could not be deleted'}), 404

@app.route('/admin')
@login_required
def admin_dashboard():
    """
    Render the admin dashboard landing page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    # Get pending counts for badges
    pending_accounts = len(user_manager.get_pending_users())
    from models import Feedback
    pending_feedbacks = Feedback.query.count()

    return render_template('admin_dashboard.html', pending_accounts=pending_accounts, pending_feedbacks=pending_feedbacks)

@app.route('/admin/rules')
@login_required
def admin_rules():
    """
    Render the admin rules page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    rules = chatbot.rules
    guest_rules = chatbot.guest_rules

    # Add category to each rule if missing (default to 'soict' for user rules)
    def add_category(rules_list, default_category='soict'):
        new_list = []
        for rule in rules_list:
            if 'category' not in rule:
                rule['category'] = default_category
            new_list.append(rule)
        return new_list

    rules = add_category(rules, default_category='soict')
    guest_rules = add_category(guest_rules, default_category='guest')

    # Group rules by category for categorized display
    categorized_user_rules = {}
    categorized_guest_rules = {}

    for rule in rules:
        category = rule.get('category', 'soict')
        if category not in categorized_user_rules:
            categorized_user_rules[category] = []
        categorized_user_rules[category].append(rule)

    for rule in guest_rules:
        category = rule.get('category', 'guest')
        if category not in categorized_guest_rules:
            categorized_guest_rules[category] = []
        categorized_guest_rules[category].append(rule)

    return render_template('admin_rules.html',
                         rules=rules,
                         guest_rules=guest_rules,
                         categorized_user_rules=categorized_user_rules,
                         categorized_guest_rules=categorized_guest_rules)

@app.route('/admin/accounts')
@login_required
def admin_accounts():
    """
    Render the admin accounts page for managing user confirmations.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    pending_users = user_manager.get_pending_users()
    return render_template('admin_accounts.html', pending_users=pending_users)

@app.route('/admin/accounts/approve/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    """
    Approve a user's account.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    success = user_manager.confirm_user(user_id)
    if success:
        return jsonify({'status': 'success', 'message': 'User approved successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'User not found'})

@app.route('/admin/accounts/reject/<int:user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    """
    Reject a user's account (delete the user).
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    success = user_manager.reject_user(user_id)
    if success:
        return jsonify({'status': 'success', 'message': 'User rejected successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'User not found'})

@app.route('/admin/faqs')
@login_required
def admin_faqs():
    """
    Render the admin FAQs management page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

<<<<<<< HEAD
    from chatbot_models import Faq
    from sqlalchemy.orm import sessionmaker
    try:
        # Use direct session with chatbot_engine to ensure correct database connection
        Session = sessionmaker(bind=chatbot_engine)
        session = Session()
        faqs_list = session.query(Faq).order_by(Faq.created_at.desc()).all()
        session.close()
        # Convert to list format expected by template
        faqs_data = [{"id": faq.id, "question": faq.question, "answer": faq.answer} for faq in faqs_list]
    except Exception as e:
        faqs_data = []
        app.logger.error(f"Failed to load FAQs from MySQL: {e}")

    return render_template('admin_faqs.html', info_list=faqs_data)
=======
    try:
        faqs_list = chatbot_db.get_faqs()
        # Format for admin template
        formatted_faqs = []
        for faq in faqs_list:
            formatted_faqs.append({
                'id': faq.get('id', ''),
                'question': faq.get('question', ''),
                'answer': faq.get('answer', '')
            })
        faqs_list = formatted_faqs
    except Exception as e:
        faqs_list = []
        app.logger.error(f"Failed to load FAQs from database: {e}")

    # Prevent caching to ensure fresh data on reload
    response = make_response(render_template('admin_faqs.html', info_list=faqs_list))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82

@app.route('/add_info', methods=['POST'])
@login_required
def add_info():
    """
<<<<<<< HEAD
    Add a new FAQ entry to MySQL Faq table.
=======
    Add a new FAQ entry to MySQL database.
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()

    if not question or not answer:
        return jsonify({'status': 'error', 'message': 'Question and answer are required'})

<<<<<<< HEAD
    from chatbot_models import Faq
    from sqlalchemy.orm import sessionmaker
    try:
        # Use direct session with chatbot_engine to ensure correct database connection
        Session = sessionmaker(bind=chatbot_engine)
        session = Session()
        new_faq = Faq(question=question, answer=answer)
        session.add(new_faq)
        session.commit()
        session.close()
=======
    try:
        # Add to MySQL database
        success = chatbot_db.add_faq({'question': question, 'answer': answer})
        if not success:
            return jsonify({'status': 'error', 'message': 'Failed to add FAQ to database'})

>>>>>>> 8710c27839fde026e4785074edbae5663a380a82
        # Reload FAQs in chatbot memory
        chatbot.reload_faqs()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save FAQ: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/edit_info', methods=['POST'])
@login_required
def edit_info():
    """
<<<<<<< HEAD
    Edit an existing FAQ entry in MySQL Faq table.
=======
    Edit an existing FAQ entry in MySQL database.
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    info_id = data.get('info_id')
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()

    app.logger.info(f"Editing FAQ with ID: {info_id}, question: {question[:50]}..., answer: {answer[:50]}...")

    if info_id is None or not question or not answer:
        return jsonify({'status': 'error', 'message': 'ID, question, and answer are required'})

<<<<<<< HEAD
    from chatbot_models import Faq
    from sqlalchemy.orm import sessionmaker
    try:
        # Use direct session with chatbot_engine to ensure correct database connection
        Session = sessionmaker(bind=chatbot_engine)
        session = Session()
        faq = session.query(Faq).get(info_id)
        if not faq:
            session.close()
            return jsonify({'status': 'error', 'message': 'FAQ not found'})

        faq.question = question
        faq.answer = answer
        session.commit()
        session.close()
        # Reload FAQs in chatbot memory
        chatbot.reload_faqs()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to update FAQ: {str(e)}'})
=======
    try:
        # Edit in MySQL database
        success = chatbot_db.edit_faq(info_id, {'question': question, 'answer': answer})
        app.logger.info(f"Database edit result: {success}")
        if not success:
            return jsonify({'status': 'error', 'message': 'Failed to update FAQ in database'})

        # Reload FAQs in chatbot memory
        chatbot.reload_faqs()
        app.logger.info("FAQs reloaded in chatbot memory")
    except Exception as e:
        app.logger.error(f"Failed to save FAQ: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Failed to save FAQ: {str(e)}'})
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82

    return jsonify({'status': 'success'})

@app.route('/delete_info', methods=['POST'])
@login_required
def delete_info():
    """
<<<<<<< HEAD
    Delete an FAQ entry from MySQL Faq table.
=======
    Delete an FAQ entry from MySQL database.
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    info_id = data.get('info_id')

    if info_id is None:
        return jsonify({'status': 'error', 'message': 'ID is required'})

<<<<<<< HEAD
    from chatbot_models import Faq
    try:
        faq = Faq.query.get(info_id)
        if not faq:
            return jsonify({'status': 'error', 'message': 'FAQ not found'})

        db.session.delete(faq)
        db.session.commit()
        # Reload FAQs in chatbot memory
        chatbot.reload_faqs()
    except Exception as e:
        db.session.rollback()
=======
    try:
        # Delete from MySQL database
        success = chatbot_db.delete_faq(info_id)
        if not success:
            return jsonify({'status': 'error', 'message': 'Failed to delete FAQ from database'})

        # Reload FAQs in chatbot memory
        chatbot.reload_faqs()
    except Exception as e:
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82
        return jsonify({'status': 'error', 'message': f'Failed to delete FAQ: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/admin/locations')
@login_required
def admin_locations():
    """
    Render the admin locations page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    return render_template('admin_locations.html')

@app.route('/admin/add_locations')
@login_required
def admin_add_locations():
    """
    Render the admin add locations page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    return render_template('admin_add_locations.html')

@app.route('/admin/existing_locations')
@login_required
def admin_existing_locations():
    """
    Render the admin existing locations page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    try:
        locations = chatbot_db.get_location_rules()
        # Format for admin template - extract basic info
        formatted_locations = []
        for loc in locations:
            formatted_locations.append({
                'id': loc.get('id'),
                'description': loc.get('description', ''),
                'user_type': loc.get('user_type', 'both'),
                'urls': loc.get('urls', []),
                'url': loc.get('url', '')
            })
        locations = formatted_locations
    except Exception as e:
        locations = []
        app.logger.error(f"Failed to load locations from database: {e}")

    return render_template('admin_existing_locations.html', locations=locations)

@app.route('/admin/visuals')
@login_required
def admin_visuals():
    """
    Render the admin visuals page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    return render_template('admin_visuals.html')

@app.route('/admin/add_visuals')
@login_required
def admin_add_visuals():
    """
    Render the admin add visuals page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    return render_template('admin_add_visuals.html')

@app.route('/admin/existing_visuals')
@login_required
def admin_existing_visuals():
    """
    Render the admin existing visuals page.
    """
<<<<<<< HEAD
    from chatbot_models import Visual

=======
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

<<<<<<< HEAD
    # Load visuals from MySQL Visual table
    try:
        visuals_data = Visual.query.all()
        visuals = []
        for visual in visuals_data:
            visual_dict = {
                "id": visual.id,
                "questions": visual.questions,
                "description": visual.description,
                "user_type": visual.user_type,
                "urls": visual.urls,
                "url": visual.url
            }
            visuals.append(visual_dict)
    except Exception as e:
        visuals = []
        app.logger.error(f"Failed to load visuals from MySQL: {e}")
=======
    try:
        visuals = chatbot_db.get_visual_rules()
        # Format for admin template - extract basic info
        formatted_visuals = []
        for vis in visuals:
            formatted_visuals.append({
                'id': vis.get('id'),
                'description': vis.get('description', ''),
                'user_type': vis.get('user_type', 'both'),
                'urls': vis.get('urls', []),
                'url': vis.get('url', '')
            })
        visuals = formatted_visuals
    except Exception as e:
        visuals = []
        app.logger.error(f"Failed to load visuals from database: {e}")
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82

    return render_template('admin_existing_visuals.html', visuals=visuals)

@app.route('/add_location', methods=['POST'])
@login_required
def add_location():
    """
    Add a new location with images.
    """
    import json
    import os
    import uuid

    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    questions = request.form.get('questions', '').strip()
    description = request.form.get('description', '').strip()
    user_type = request.form.get('user_type', 'both')

    if not questions or not description:
        return jsonify({'status': 'error', 'message': 'Questions and description are required'})

    # Process questions as JSON array of strings, each string is a separate set
    questions_data = json.loads(questions) if questions else []
    questions_list = []
    for set_str in questions_data:
        if isinstance(set_str, str):
            set_list = [set_str.strip()] if set_str.strip() else []
        elif isinstance(set_str, list):
            set_list = [k.strip() for k in set_str if k.strip()]
        else:
            set_list = []
        questions_list.append(set_list)

    # Handle file uploads
    uploaded_files = request.files.getlist('images')
    image_urls = []

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            image_urls.append(f"uploads/locations/{unique_filename}")

    if not image_urls:
        return jsonify({'status': 'error', 'message': 'At least one image is required'})

    # Load existing locations
    locations_path = os.path.join(app.root_path, 'database', 'locations', 'locations.json')
    try:
        with open(locations_path, 'r', encoding='utf-8') as f:
            locations = json.load(f)
    except:
        locations = []

    # Create new location
    new_location = {
        'id': str(uuid.uuid4()),
        'questions': questions_list,
        'description': description,
        'user_type': user_type,
        'urls': image_urls,
        'url': image_urls[0]  # Primary image
    }

    locations.append(new_location)

    # Save updated locations
    try:
        with open(locations_path, 'w', encoding='utf-8') as f:
            json.dump(locations, f, indent=4)
        # Also add to MySQL database
        location_data = {
            'id': new_location['id'],
            'questions': new_location['questions'],
            'description': new_location['description'],
            'user_type': new_location['user_type'],
            'urls': new_location['urls'],
            'url': new_location['url']
        }
        chatbot_db.add_location(location_data)
        # Reload location rules in chatbot memory
        chatbot.reload_location_rules()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save location: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/edit_location/<location_id>', methods=['POST'])
@login_required
def edit_location_with_id(location_id):
    """
    Edit an existing location with images.
    """
    import json
    import os
    import uuid

    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    questions = request.form.get('questions', '').strip()
    description = request.form.get('description', '').strip()
    user_type = request.form.get('user_type', 'both')
    removed_images = json.loads(request.form.get('removedImages', '[]'))

    if not questions or not description:
        return jsonify({'status': 'error', 'message': 'Questions and description are required'})

    # Process questions as JSON array of strings, each string is a separate set
    questions_data = json.loads(questions) if questions else []
    questions_list = []
    for set_str in questions_data:
        if isinstance(set_str, str):
            set_list = [set_str.strip()] if set_str.strip() else []
        elif isinstance(set_str, list):
            set_list = [k.strip() for k in set_str if k.strip()]
        else:
            set_list = []
        questions_list.append(set_list)

    # Load existing locations
    locations_path = os.path.join(app.root_path, 'database', 'locations', 'locations.json')
    try:
        with open(locations_path, 'r', encoding='utf-8') as f:
            locations = json.load(f)
    except:
        locations = []

    # Find location to edit
    location_to_edit = None
    for loc in locations:
        if str(loc.get('id')) == str(location_id):
            location_to_edit = loc
            break

    if not location_to_edit:
        return jsonify({'status': 'error', 'message': 'Location not found'})

    # Update location data
    location_to_edit['questions'] = questions_list
    location_to_edit['description'] = description
    location_to_edit['user_type'] = user_type

    # Handle image removal
    if 'urls' in location_to_edit:
        location_to_edit['urls'] = [url for url in location_to_edit['urls'] if url not in removed_images]

    if 'url' in location_to_edit and location_to_edit['url'] in removed_images:
        del location_to_edit['url']

    # Handle new image uploads
    uploaded_files = request.files.getlist('images')
    new_image_urls = []

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            new_image_urls.append(f"uploads/locations/{unique_filename}")

    # Add new images to existing ones
    if 'urls' not in location_to_edit:
        location_to_edit['urls'] = []

    location_to_edit['urls'].extend(new_image_urls)

    # Ensure primary url exists
    if not location_to_edit.get('url') and location_to_edit['urls']:
        location_to_edit['url'] = location_to_edit['urls'][0]

    # Save updated locations
    try:
        with open(locations_path, 'w', encoding='utf-8') as f:
            json.dump(locations, f, indent=4)
        # Also edit in MySQL database
        location_data = {
            'id': location_to_edit['id'],
            'questions': location_to_edit['questions'],
            'description': location_to_edit['description'],
            'user_type': location_to_edit['user_type'],
            'urls': location_to_edit['urls'],
            'url': location_to_edit['url']
        }
        chatbot_db.edit_location(location_id, location_data)
        # Reload location rules in chatbot memory
        chatbot.reload_location_rules()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save location: {str(e)}'})

    return jsonify({'status': 'success'})

@app.route('/delete_location', methods=['POST'])
@login_required
def delete_location():
    """
    Delete a location entry.
    """
    import json
    import os

    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    location_id = data.get('id')

    if not location_id:
        return jsonify({'status': 'error', 'message': 'ID is required'})

    locations_path = os.path.join(app.root_path, 'database', 'locations', 'locations.json')

    try:
        with open(locations_path, 'r', encoding='utf-8') as f:
            locations = json.load(f)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to load locations: {e}'})

    # Filter out the location to delete
    new_locations = [loc for loc in locations if str(loc.get('id')) != str(location_id)]

    if len(new_locations) == len(locations):
        return jsonify({'status': 'error', 'message': 'Location not found'})

    try:
        with open(locations_path, 'w', encoding='utf-8') as f:
            json.dump(new_locations, f, indent=4)
        # Also delete from MySQL database
        chatbot_db.delete_location(location_id)
        # Reload location rules in chatbot memory
        chatbot.reload_location_rules()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save locations: {e}'})

    return jsonify({'status': 'success'})

@app.route('/add_visual', methods=['POST'])
@login_required
def add_visual():
    """
    Add a new visual with images/videos to MySQL Visual table.
    """
    import json
    import os
    import uuid

    app.logger.info(f"Request received: {request.method} {request.path}")

    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    questions = request.form.get('questions', '').strip()
    description = request.form.get('description', '').strip()
    user_type = request.form.get('user_type', 'both')

    if not description:
        return jsonify({'status': 'error', 'message': 'Description is required'})

    # Process questions as JSON array of strings, each string is a separate set
    questions_data = json.loads(questions) if questions else []
    questions_list = []
    for set_str in questions_data:
        if isinstance(set_str, str):
            set_list = [set_str.strip()] if set_str.strip() else []
        elif isinstance(set_str, list):
            set_list = [k.strip() for k in set_str if k.strip()]
        else:
            set_list = []
        questions_list.append(set_list)

    # Handle file uploads
    uploaded_files = request.files.getlist('images')
    media_urls = []

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = re.sub(r'\.+', '.', filename)  # Replace multiple dots with single dot
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['VISUALS_UPLOAD_FOLDER'], unique_filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            media_urls.append(f"uploads/visuals/{unique_filename}")

    if not media_urls:
        return jsonify({'status': 'error', 'message': 'At least one image or video is required'})

    # Save to MySQL Visual table
    from chatbot_models import Visual
    try:
<<<<<<< HEAD
        new_visual = Visual(
            id=str(uuid.uuid4()),
            questions=questions_list,
            description=description,
            user_type=user_type,
            urls=media_urls,
            url=media_urls[0]  # Primary media
        )
        db.session.add(new_visual)
        db.session.commit()
=======
        with open(visuals_path, 'r', encoding='utf-8') as f:
            visuals = json.load(f)
    except:
        visuals = []

    # Create new visual
    new_visual = {
        'id': str(uuid.uuid4()),
        'questions': questions_list,
        'description': description,
        'user_type': user_type,
        'urls': media_urls,
        'url': media_urls[0]  # Primary media
    }

    visuals.append(new_visual)

    # Save updated visuals
    try:
        with open(visuals_path, 'w', encoding='utf-8') as f:
            json.dump(visuals, f, indent=4)
        # Also add to MySQL database
        visual_data = {
            'id': new_visual['id'],
            'questions': new_visual['questions'],
            'description': new_visual['description'],
            'user_type': new_visual['user_type'],
            'urls': new_visual['urls'],
            'url': new_visual['url']
        }
        chatbot_db.add_visual(visual_data)
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to save visual: {str(e)}'})

    # Update visuals in memory
    chatbot.reload_visual_rules()

    return jsonify({'status': 'success'})

@app.route('/edit_visual/<visual_id>', methods=['POST'])
@login_required
def edit_visual_with_id(visual_id):
    """
    Edit an existing visual with images/videos in MySQL Visual table.
    """
    import json
    import os
    import uuid

    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    questions = request.form.get('questions', '').strip()
    description = request.form.get('description', '').strip()
    user_type = request.form.get('user_type', 'both')
    removed_images = json.loads(request.form.get('removedImages', '[]'))

    if not questions or not description:
        return jsonify({'status': 'error', 'message': 'Questions and description are required'})

    # Process questions as JSON array of strings, each string is a separate set
    questions_data = json.loads(questions) if questions else []
    questions_list = []
    for set_str in questions_data:
        if isinstance(set_str, str):
            set_list = [set_str.strip()] if set_str.strip() else []
        elif isinstance(set_str, list):
            set_list = [k.strip() for k in set_str if k.strip()]
        else:
            set_list = []
        questions_list.append(set_list)

    # Find visual to edit in MySQL
    from chatbot_models import Visual
    visual_to_edit = Visual.query.filter_by(id=visual_id).first()
    if not visual_to_edit:
        return jsonify({'status': 'error', 'message': 'Visual not found'})

    # Update visual data
    visual_to_edit.questions = questions_list
    visual_to_edit.description = description
    visual_to_edit.user_type = user_type

    # Handle image removal
    if visual_to_edit.urls:
        visual_to_edit.urls = [url for url in visual_to_edit.urls if url not in removed_images]

    if visual_to_edit.url in removed_images:
        visual_to_edit.url = None

    # Handle new media uploads
    uploaded_files = request.files.getlist('images')
    new_media_urls = []

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(app.config['VISUALS_UPLOAD_FOLDER'], unique_filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            new_media_urls.append(f"uploads/visuals/{unique_filename}")

    # Add new media to existing ones
    if not visual_to_edit.urls:
        visual_to_edit.urls = []

    visual_to_edit.urls.extend(new_media_urls)

    # Ensure primary url exists
    if not visual_to_edit.url and visual_to_edit.urls:
        visual_to_edit.url = visual_to_edit.urls[0]

    # Save to MySQL
    try:
<<<<<<< HEAD
        db.session.commit()
=======
        with open(visuals_path, 'w', encoding='utf-8') as f:
            json.dump(visuals, f, indent=4)
        # Also edit in MySQL database
        visual_data = {
            'id': visual_to_edit['id'],
            'questions': visual_to_edit['questions'],
            'description': visual_to_edit['description'],
            'user_type': visual_to_edit['user_type'],
            'urls': visual_to_edit['urls'],
            'url': visual_to_edit['url']
        }
        chatbot_db.edit_visual(visual_id, visual_data)
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to save visual: {str(e)}'})

    # Update visuals in memory
    chatbot.reload_visual_rules()

    return jsonify({'status': 'success'})

@app.route('/delete_visual', methods=['POST'])
@login_required
def delete_visual():
    """
    Delete a visual entry from MySQL Visual table.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    visual_id = data.get('id')

    if not visual_id:
        return jsonify({'status': 'error', 'message': 'ID is required'})

    from chatbot_models import Visual
    try:
        visual = Visual.query.filter_by(id=visual_id).first()
        if not visual:
            return jsonify({'status': 'error', 'message': 'Visual not found'})

        db.session.delete(visual)
        db.session.commit()
    except Exception as e:
<<<<<<< HEAD
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to delete visual: {str(e)}'})

    # Update chatbot rules in memory
=======
        return jsonify({'status': 'error', 'message': f'Failed to load visuals: {e}'})

    # Filter out the visual to delete
    new_visuals = [vis for vis in visuals if str(vis.get('id')) != str(visual_id)]

    if len(new_visuals) == len(visuals):
        return jsonify({'status': 'error', 'message': 'Visual not found'})

    try:
        with open(visuals_path, 'w', encoding='utf-8') as f:
            json.dump(new_visuals, f, indent=4)
        # Also delete from MySQL database
        chatbot_db.delete_visual(visual_id)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save visuals: {e}'})

    # Reload visual rules in chatbot memory
>>>>>>> 8710c27839fde026e4785074edbae5663a380a82
    chatbot.reload_visual_rules()

    return jsonify({'status': 'success'})

@app.route('/admin/emails')
@login_required
def admin_emails():
    """
    Render the admin emails page.
    """
    from database import email_directory

    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    emails = email_directory.get_all_emails()

    return render_template('admin_emails.html', emails=emails)

@app.route('/add_category', methods=['POST'])
@login_required
def add_category():
    """
    Add a new category to the system.
    """
    print(f"DEBUG: add_category called. Session: {session}")
    print(f"DEBUG: Current user: {current_user}, is_authenticated: {current_user.is_authenticated}")

    if not is_admin(current_user):
        print("DEBUG: Unauthorized access - user is not admin")
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    print(f"DEBUG: Request data: {data}")

    category_name = data.get('category_name', '').strip()
    print(f"DEBUG: Category name: '{category_name}'")

    if not category_name:
        print("DEBUG: Category name is required")
        return jsonify({'status': 'error', 'message': 'Category name is required'})

    # Logic to store the category in a JSON file
    app.logger.info(f"Attempting to add category: {category_name} by user: {current_user.email}")
    app.logger.info(f"Request data: {data}")  # Log the request data for debugging
    # For now, let's assume we are storing it in a JSON file
    categories_path = os.path.join(app.root_path, 'database', 'categories.json')
    print(f"DEBUG: Categories path: {categories_path}")

    try:
        if os.path.exists(categories_path):
            print("DEBUG: categories.json exists")
            with open(categories_path, 'r', encoding='utf-8') as f:
                categories = json.load(f)
        else:
            print("DEBUG: categories.json does not exist, creating empty list")
            categories = []

        # Check for duplicates (case-insensitive)
        if category_name.lower() in [cat.lower() for cat in categories]:
            print(f"DEBUG: Category '{category_name}' already exists")
            return jsonify({'status': 'error', 'message': 'Category already exists'})

        categories.append(category_name)  # Add the new category to the list
        # Note: Category files are created automatically when rules are added to new categories
        # No need to create empty category files upfront
        print(f"DEBUG: Adding category '{category_name}' to list: {categories}")

        with open(categories_path, 'w', encoding='utf-8') as f:
            json.dump(categories, f, indent=4)
        print("DEBUG: Successfully wrote to categories.json")

        # Add empty category to combined rule files
        from database.user_database import rule_utils
        rule_utils.add_empty_category(category_name, user_type='both')

        # Add the new category to rule_utils CATEGORY_FILES dynamically
        category_lower = category_name.lower()
        if category_lower not in rule_utils.CATEGORY_FILES:
            # Point to combined files instead of creating new ones
            rule_utils.CATEGORY_FILES[category_lower] = {
                "user": os.path.join(app.root_path, 'database', 'user_database', 'all_user_rules.json'),
                "guest": os.path.join(app.root_path, 'database', 'guest_database', 'all_guest_rules.json')
            }
            app.logger.info(f"Added {category_lower} to rule_utils.CATEGORY_FILES pointing to combined files")

        return jsonify({'status': 'success', 'message': 'Category added successfully', 'redirect': url_for('admin_dashboard')})
    except Exception as e:
        app.logger.error(f"Error adding category: {str(e)}")  # Log the error with details
        app.logger.error(f"Request data: {data}")  # Log the request data for debugging
        print(f"DEBUG: Exception occurred: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Failed to add category: {str(e)}. Please check the server logs for more details.'})

@app.route('/remove_category', methods=['POST'])
@login_required
def remove_category():
    """
    Remove a category from the system, including deleting associated rule files and updating all_*_rules.json files.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    category_name = data.get('category_name', '').strip()

    if not category_name:
        return jsonify({'status': 'error', 'message': 'Category name is required'})

    categories_path = os.path.join(app.root_path, 'database', 'categories.json')

    try:
        if os.path.exists(categories_path):
            with open(categories_path, 'r', encoding='utf-8') as f:
                categories = json.load(f)
        else:
            categories = []

        # Remove category if it exists (case-insensitive)
        categories_lower = [cat.lower() for cat in categories]
        if category_name.lower() not in categories_lower:
            return jsonify({'status': 'error', 'message': 'Category not found'})

        # Remove the category (case-insensitive)
        index_to_remove = categories_lower.index(category_name.lower())
        removed_category = categories.pop(index_to_remove)

        # Save updated categories
        with open(categories_path, 'w', encoding='utf-8') as f:
            json.dump(categories, f, indent=4)

        # Remove category from all_user_rules.json and all_guest_rules.json
        from database.user_database import rule_utils
        rule_utils.remove_category(removed_category, user_type='both')

        # Delete associated rule files
        user_rule_file = os.path.join(app.root_path, 'database', 'user_database', f"{removed_category.lower()}_rules.json")
        guest_rule_file = os.path.join(app.root_path, 'database', 'guest_database', f"{removed_category.lower()}_guest_rules.json")

        if os.path.exists(user_rule_file):
            os.remove(user_rule_file)
        if os.path.exists(guest_rule_file):
            os.remove(guest_rule_file)

        # Update chatbot rules in memory
        chatbot.rules = chatbot.get_rules()
        chatbot.guest_rules = chatbot.get_guest_rules()

        return jsonify({'status': 'success', 'message': f'Category {removed_category} removed successfully', 'redirect': url_for('admin_dashboard')})
    except Exception as e:
        app.logger.error(f"Error removing category: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Failed to remove category: {str(e)}'})

@app.route('/get_categories', methods=['GET'])
@login_required
def get_categories():
    """
    Get all categories from categories.json.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    categories_path = os.path.join(app.root_path, 'database', 'categories.json')
    try:
        with open(categories_path, 'r', encoding='utf-8') as f:
            categories = json.load(f)
        return jsonify({'status': 'success', 'categories': categories})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to load categories: {str(e)}'})

@app.route('/create_category', methods=['POST'])
@login_required
def create_category():
    """
    Create JSON files for a new category in both user and guest databases.
    """
    print(f"DEBUG: create_category called. Session: {session}")
    print(f"DEBUG: Current user: {current_user}, is_authenticated: {current_user.is_authenticated}")

    if not is_admin(current_user):
        print("DEBUG: Unauthorized access - user is not admin")
        app.logger.error("Unauthorized access attempt to create category.")
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    print(f"DEBUG: Request data: {data}")

    category = data.get('category', '').strip()
    print(f"DEBUG: Category: '{category}'")

    if not category:
        print("DEBUG: Category name is required.")
        app.logger.error("Category name is required.")
        return jsonify({'status': 'error', 'message': 'Category name is required'})

    try:
        # Create category files using the chatbot's method
        print(f"DEBUG: Calling chatbot.create_category_files('{category}')")
        chatbot.create_category_files(category)
        app.logger.info(f"Category files created for: {category}")
        print(f"DEBUG: Category files created successfully for: {category}")
        return jsonify({'status': 'success', 'message': f'Category files created for {category}'})
    except Exception as e:
        app.logger.error(f"Error creating category files: {str(e)}")
        print(f"DEBUG: Exception occurred in create_category_files: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Failed to create category files: {str(e)}'})

@app.route('/admin/feedback')
@login_required
def admin_feedback():
    """
    Render the admin feedback page.
    """
    from models import Feedback

    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    feedbacks = Feedback.query.order_by(Feedback.timestamp.desc()).all()

    # Format timestamps for display
    for fb in feedbacks:
        fb.formatted_timestamp = fb.timestamp.strftime('%B %d, %Y')

    return render_template('admin_feedback.html', feedbacks=feedbacks)

@app.route('/admin/feedback/mark_done', methods=['POST'])
@login_required
def mark_feedback_done():
    """
    Mark feedback as done: remove from DB, save to feedback.json, send email notification.
    """
    from models import Feedback

    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    feedback_id = data.get('feedback_id')

    if not feedback_id:
        return jsonify({'status': 'error', 'message': 'Feedback ID is required'})

    feedback = Feedback.query.get(feedback_id)
    if not feedback:
        return jsonify({'status': 'error', 'message': 'Feedback not found'})

    # Prepare feedback data to save
    feedback_data = {
        'id': feedback.id,
        'user_id': feedback.user_id,
        'message': feedback.message,
        'timestamp': feedback.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }

    # Path to feedback.json
    feedback_json_path = os.path.join(app.root_path, 'database', 'feedback', 'feedback.json')

    # Load existing feedbacks from JSON file
    try:
        if os.path.exists(feedback_json_path):
            with open(feedback_json_path, 'r', encoding='utf-8') as f:
                existing_feedbacks = json.load(f)
        else:
            existing_feedbacks = []
    except Exception as e:
        existing_feedbacks = []

    # Append new feedback data
    existing_feedbacks.append(feedback_data)

    # Save back to JSON file
    try:
        with open(feedback_json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_feedbacks, f, indent=4)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save feedback to JSON: {str(e)}'})

    # Remove feedback from DB
    try:
        db.session.delete(feedback)
        db.session.commit()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to delete feedback from DB: {str(e)}'})

    # Commenting out email notification logic for now
    # Send email notification
    # try:
    #     # Get admin emails from email directory
    #     from database import email_directory
    #     admin_emails = [entry['email'] for entry in email_directory.get_all_emails()]

    #     if admin_emails:
    #         subject = "Feedback Marked as Done"
    #         body = f"Feedback ID: {feedback_data['id']}\nUser ID: {feedback_data['user_id']}\nMessage: {feedback_data['message']}\nTimestamp: {feedback_data['timestamp']}"
    #         msg = Message(subject=subject, recipients=admin_emails, body=body)

    return jsonify({'status': 'success'})

@app.route('/admin/feedback/finished', methods=['GET'])
@login_required
def get_finished_feedback():
    """
    Return finished feedback loaded from feedback.json as JSON, filtering out feedback older than 30 days.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    feedback_json_path = os.path.join(app.root_path, 'database', 'feedback', 'feedback.json')

    try:
        if os.path.exists(feedback_json_path):
            with open(feedback_json_path, 'r', encoding='utf-8') as f:
                finished_feedback = json.load(f)
        else:
            finished_feedback = []
    except Exception as e:
        app.logger.error(f"Failed to load finished feedback: {str(e)}")
        finished_feedback = []

    # Filter out feedback older than 30 days
    current_time = datetime.now()
    thirty_days_ago = current_time - timedelta(days=30)
    finished_feedback = [
        fb for fb in finished_feedback
        if datetime.strptime(fb['timestamp'], '%Y-%m-%d %H:%M:%S') > thirty_days_ago
    ]

    # Format timestamps for display
    for fb in finished_feedback:
        dt = datetime.strptime(fb['timestamp'], '%Y-%m-%d %H:%M:%S')
        fb['timestamp'] = dt.strftime('%B %d, %Y')

    # Save the filtered feedback back to the file to remove old entries (keeping original format)
    try:
        # Reload and filter again for saving, without formatting
        if os.path.exists(feedback_json_path):
            with open(feedback_json_path, 'r', encoding='utf-8') as f:
                all_feedback = json.load(f)
        else:
            all_feedback = []
        filtered_for_save = [
            fb for fb in all_feedback
            if datetime.strptime(fb['timestamp'], '%Y-%m-%d %H:%M:%S') > thirty_days_ago
        ]
        with open(feedback_json_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_for_save, f, indent=4)
    except Exception as e:
        app.logger.error(f"Failed to save filtered feedback: {str(e)}")

    return jsonify({'status': 'success', 'finished_feedback': finished_feedback})

@app.route('/add_rule', methods=['POST'])
@login_required
def add_rule():
    """
    Add a new chatbot rule via admin interface.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    # Handle both form data and JSON data for backward compatibility
    if request.is_json:
        data = request.get_json()
        question = data.get('keywords', '')  # The form sends question as 'keywords' field
        response = data.get('response', '')
        user_type = data.get('user_type', 'user')
        category = data.get('category', 'soict')
    else:
        # Handle form data
        question = request.form.get('keywords', '').strip()
        response = request.form.get('response', '').strip()
        user_type = request.form.get('user_type', 'user')
        category = request.form.get('category', 'soict')

    if not question or not response:
        return jsonify({'status': 'error', 'message': 'Question and response are required'})

    if category == "locations":
        chatbot.add_rule(question, response, category=category)
    else:
        chatbot.add_rule(question, response, user_type=user_type, category=category)
    return jsonify({'status': 'success'})

@app.route('/delete_rule', methods=['POST'])
@login_required
def delete_rule():
    """
    Delete a chatbot rule via admin interface.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    rule_id = data.get('rule_id')
    user_type = data.get('user_type', 'user')

    if not rule_id:
        return jsonify({'status': 'error', 'message': 'Rule ID is required'})

    # Use chatbot's delete_rule method
    deleted = chatbot.delete_rule(rule_id, user_type)

    if deleted:
        return jsonify({'status': 'success', 'message': 'Rule deleted successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Rule not found or could not be deleted'})

@app.route('/edit_rule', methods=['POST'])
@login_required
def edit_rule():
    """
    Edit a chatbot rule via admin interface.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    rule_id = data.get('rule_id')
    question = data.get('question', '')  # Updated to use 'question' instead of 'keywords'
    response = data.get('response', '')
    user_type = data.get('user_type', 'user')

    if not rule_id or not question or not response:
        return jsonify({'status': 'error', 'message': 'Rule ID, question, and response are required'})

    # Use chatbot's edit_rule method
    edited = chatbot.edit_rule(rule_id, question, response, user_type)

    if edited:
        return jsonify({'status': 'success', 'message': 'Rule updated successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Rule not found or could not be updated'})

@app.route('/add_email', methods=['POST'])
@login_required
def add_email():
    """
    Add a new email entry to the email directory.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    school = data.get('school', '').strip()
    email = data.get('email', '').strip()

    if not school or not email:
        return jsonify({'status': 'error', 'message': 'School and email are required'})

    try:
        email_id = email_directory.add_email(school, email)
        return jsonify({'status': 'success', 'message': 'Email added successfully', 'id': email_id})
    except Exception as e:
        app.logger.error(f"Error adding email: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Failed to add email: {str(e)}'})

@app.route('/update_email', methods=['POST'])
@login_required
def update_email():
    """
    Update an existing email entry.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    email_id = data.get('id')
    school = data.get('school', '').strip()
    email = data.get('email', '').strip()

    if not email_id or not school or not email:
        return jsonify({'status': 'error', 'message': 'ID, school, and email are required'})

    try:
        updated = email_directory.update_email(email_id, school, email)
        if updated:
            return jsonify({'status': 'success', 'message': 'Email updated successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Email not found'})
    except Exception as e:
        app.logger.error(f"Error updating email: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Failed to update email: {str(e)}'})

@app.route('/delete_email', methods=['POST'])
@login_required
def delete_email():
    """
    Delete an email entry from the directory.
    """
    if not is_admin(current_user):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    data = request.get_json()
    email_id = data.get('id')

    if not email_id:
        return jsonify({'status': 'error', 'message': 'ID is required'})

    try:
        deleted = email_directory.delete_email(email_id)
        if deleted:
            return jsonify({'status': 'success', 'message': 'Email deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Email not found'})
    except Exception as e:
        app.logger.error(f"Error deleting email: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Failed to delete email: {str(e)}'})

@app.route('/admin/login_logs')
@login_required
def admin_login_logs():
    """
    Render the admin login logs page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    from models import LoginLog
    login_logs = LoginLog.query.filter(LoginLog.user_type.in_(['user', 'guest'])).order_by(LoginLog.timestamp.desc()).all()

    # Format timestamps for display
    for log in login_logs:
        log.formatted_timestamp = log.timestamp.strftime('%B %d, %Y %H:%M:%S')

    return render_template('admin_login_logs.html', login_logs=login_logs)

@app.route('/admin/login_logs/delete/<int:log_id>', methods=['DELETE'])
@login_required
def delete_login_log(log_id):
    """
    Delete a login log entry.
    """
    print(f"DEBUG: Delete route called for log_id: {log_id}")
    if not is_admin(current_user):
        print(f"DEBUG: Unauthorized access by user: {current_user}")
        app.logger.warning(f"Unauthorized delete attempt by user: {current_user}")
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})

    from models import LoginLog
    log = LoginLog.query.get(log_id)
    print(f"DEBUG: Log found: {log is not None}")
    if not log:
        print(f"DEBUG: Login log not found: ID {log_id}")
        app.logger.warning(f"Login log not found: ID {log_id}")
        return jsonify({'status': 'error', 'message': 'Log not found'})

    print(f"DEBUG: Deleting login log: ID {log_id}, User Type: {log.user_type}, Identifier: {log.identifier}")
    app.logger.info(f"Deleting login log: ID {log_id}, User Type: {log.user_type}, Identifier: {log.identifier}")

    try:
        db.session.delete(log)
        db.session.commit()
        print(f"DEBUG: Successfully deleted login log: ID {log_id}")
        app.logger.info(f"Successfully deleted login log: ID {log_id}")
        # Update chatbot rules in memory
        chatbot.rules = chatbot.get_rules()
        chatbot.guest_rules = chatbot.get_guest_rules()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Error deleting login log: {str(e)}")
        app.logger.error(f"Error deleting login log: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to delete log'})

@app.route('/admin/user_chat_history/<identifier>/<user_type>')
@login_required
def admin_user_chat_history(identifier, user_type):
    """
    Render the admin user chat history page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    from models import ChatMessage
    if user_type == 'user':
        # For users, find by email
        from models import User
        user = User.query.filter_by(email=identifier).first()
        if user:
            chat_messages = ChatMessage.query.filter_by(user_id=user.id).order_by(ChatMessage.timestamp.desc()).all()
        else:
            chat_messages = []
    elif user_type == 'guest':
        # For guests, find by guest_username
        chat_messages = ChatMessage.query.filter_by(guest_username=identifier).order_by(ChatMessage.timestamp.desc()).all()
    else:
        chat_messages = []

    # Group messages by session_id
    chat_sessions = {}
    for msg in chat_messages:
        session_id = msg.session_id
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        chat_sessions[session_id].append(msg)

    # Sort sessions by most recent message
    sorted_sessions = sorted(chat_sessions.items(), key=lambda x: x[1][0].timestamp if x[1] else datetime.min, reverse=True)

    return render_template('admin_user_chat_history.html', identifier=identifier, user_type=user_type, chat_sessions=sorted_sessions)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """
    Handle feedback submission from chat page and save to database.
    """
    from models import Feedback
    data = request.get_json()
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'status': 'error', 'message': 'Feedback message is required'})

    try:
        feedback = Feedback(
            user_id=current_user.id if current_user.is_authenticated else None,
            message=message
        )
        db.session.add(feedback)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Feedback submitted successfully'})
    except Exception as e:
        app.logger.error(f"Error submitting feedback: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Failed to submit feedback'})



@app.route('/admin/json_editor')
@login_required
def admin_json_editor():
    """
    Render the admin JSON editor page.
    """
    if not is_admin(current_user):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('chat'))

    return render_template('admin_json_editor.html')



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
