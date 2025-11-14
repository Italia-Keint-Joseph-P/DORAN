import logging
from datetime import datetime
from werkzeug.security import generate_password_hash
from flask_login import UserMixin
import uuid
from models import User as UserModel, Admin as AdminModel
from extensions import db

class UserManager:
    """
    UserManager class to handle user and admin management and chat history.
    """
    def __init__(self, db):
        """
        Initialize UserManager with database connection and create default admin.
        """
        self.db = db
        admin_email = "admin@wvsu.edu.ph"
        # Retry admin creation/check up to 3 times
        max_retries = 3
        for attempt in range(max_retries):
            try:
                admin = self.get_admin_by_email(admin_email)
                if not admin:
                    admin = AdminModel(email=admin_email)
                    admin.set_password("admin123")
                    self.db.session.add(admin)
                    self.db.session.commit()
                    logging.debug(f"Created default admin user with email: {admin_email}")
                else:
                    logging.debug(f"Admin user already exists with email: {admin_email}")
                break  # Success, exit retry loop
            except Exception as e:
                logging.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)  # Wait 2 seconds before retry
                    continue
                else:
                    logging.error(f"Failed to initialize admin user after {max_retries} attempts: {str(e)}")
                    # Don't raise exception, allow app to continue
                    break

    def get_admin_by_email(self, email):
        """
        Get an admin by their email.

        Args:
            email (str): Admin email.

        Returns:
            AdminModel or None: Admin object if found.
        """
        return AdminModel.query.filter_by(email=email).first()
    
    def create_user(self, username, email, password, role):
        """
        Create a new user and store it in the database.

        Args:
            username (str): Username.
            email (str): Email address.
            password (str): Password.
            role (str): User role.

        Returns:
            UserModel: Created user object.
        """
        user = UserModel(username=username, email=email, role=role)
        user.set_password(password)
        self.db.session.add(user)
        self.db.session.commit()
        logging.debug(f"Created user: {email} with role: {role}")
        return user

    def create_admin(self, email, password):
        """
        Create a new admin and store it in the database.

        Args:
            email (str): Admin email.
            password (str): Password.

        Returns:
            AdminModel: Created admin object.
        """
        admin = AdminModel(email=email)
        admin.set_password(password)
        self.db.session.add(admin)
        self.db.session.commit()
        logging.debug(f"Created admin: {email}")
        return admin
    
    def get_user_by_id(self, user_id):
        """
        Get a user by their ID.

        Args:
            user_id (int): User ID.

        Returns:
            UserModel or None: User object if found.
        """
        return UserModel.query.get(int(user_id))
    
    def get_user_by_email(self, email):
        """
        Get a user by their email.

        Args:
            email (str): Email address.

        Returns:
            UserModel or None: User object if found.
        """
        return UserModel.query.filter_by(email=email).first()
    
    def get_user_by_username(self, username):
        """
        Get a user by their username.

        Args:
            username (str): Username.

        Returns:
            UserModel or None: User object if found.
        """
        return UserModel.query.filter_by(username=username).first()
    
    def add_chat_message(self, user_id, session_id, sender_type, message):
        """
        Add a message to a user's chat history.

        Args:
            user_id (int): User ID.
            session_id (str): Chat session ID.
            sender_type (str): 'user' or 'bot'.
            message (str): Message content.
        """
        from models import ChatMessage
        chat_message = ChatMessage(user_id=user_id, session_id=session_id, sender_type=sender_type, message=message)
        self.db.session.add(chat_message)
        self.db.session.commit()
    
    def get_chat_history(self, user_id):
        """
        Get a user's chat history grouped by session.

        Args:
            user_id (int): User ID.

        Returns:
            dict: Sessions with title and messages.
        """
        from models import ChatMessage
        messages = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.timestamp.asc()).all()

        sessions = {}
        for msg in messages:
            session_id = msg.session_id
            if session_id not in sessions:
                sessions[session_id] = {
                    'title': None,
                    'messages': [],
                    'timestamp': msg.timestamp
                }
            if sessions[session_id]['title'] is None and msg.sender_type == 'user':
                sessions[session_id]['title'] = msg.message
            sessions[session_id]['messages'].append({
                'sender': msg.sender_type,
                'message': msg.message,
                'timestamp': msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
        # Sort sessions by timestamp descending
        sorted_sessions = dict(sorted(sessions.items(), key=lambda x: x[1]['timestamp'], reverse=True))
        return sorted_sessions

    def get_chat_sessions_summary(self, user_id):
        """
        Get a summary of chat sessions for the user.

        Args:
            user_id (int): User ID.

        Returns:
            list: List of session summaries.
        """
        from models import ChatMessage
        messages = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.timestamp.asc()).all()

        sessions = {}
        for msg in messages:
            session_id = msg.session_id
            if session_id not in sessions:
                sessions[session_id] = {
                    'id': session_id,
                    'title': None,
                    'timestamp': msg.timestamp
                }
            if sessions[session_id]['title'] is None and msg.sender_type == 'user':
                sessions[session_id]['title'] = msg.message
        # Sort by timestamp descending
        sorted_sessions = sorted(sessions.values(), key=lambda x: x['timestamp'], reverse=True)
        return sorted_sessions

    def get_chat_session_history(self, user_id, session_id):
        """
        Get the full chat history for a specific session.

        Args:
            user_id (int): User ID.
            session_id (str): Session ID.

        Returns:
            dict: Session data with messages.
        """
        from models import ChatMessage
        messages = ChatMessage.query.filter_by(user_id=user_id, session_id=session_id).order_by(ChatMessage.timestamp.asc()).all()

        session_data = {
            'messages': []
        }
        for msg in messages:
            session_data['messages'].append({
                'sender': msg.sender_type,
                'message': msg.message,
                'timestamp': msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
        return session_data
    
    def clear_chat_history(self, user_id):
        """
        Clear a user's chat history.

        Args:
            user_id (int): User ID.
        """
        from models import ChatMessage
        ChatMessage.query.filter_by(user_id=user_id).delete()
        self.db.session.commit()

    def get_pending_users(self):
        """
        Get all users who are not confirmed yet.

        Returns:
            list: List of pending User objects.
        """
        return UserModel.query.filter_by(is_confirmed=False).all()

    def confirm_user(self, user_id):
        """
        Confirm a user's account.

        Args:
            user_id (int): User ID.

        Returns:
            bool: True if confirmed, False if user not found.
        """
        user = UserModel.query.get(user_id)
        if user:
            user.is_confirmed = True
            self.db.session.commit()
            return True
        return False

    def reject_user(self, user_id):
        """
        Reject a user's account (delete the user).

        Args:
            user_id (int): User ID.

        Returns:
            bool: True if rejected, False if user not found.
        """
        user = UserModel.query.get(user_id)
        if user:
            self.db.session.delete(user)
            self.db.session.commit()
            return True
        return False

    def delete_chat_session(self, user_id, session_id):
        """
        Delete all chat messages for a specific user and session.

        Args:
            user_id (int): User ID.
            session_id (str): Chat session ID.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        from models import ChatMessage
        try:
            ChatMessage.query.filter_by(user_id=user_id, session_id=session_id).delete()
            self.db.session.commit()
            return True
        except Exception as e:
            self.db.session.rollback()
            return False
