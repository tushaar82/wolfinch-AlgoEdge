#! /usr/bin/env python
'''
 Wolfinch Auto trading Bot
 Desc: User Authentication Module
 Copyright: (c) 2024 Wolfinch Contributors
'''

import json
import bcrypt
from pathlib import Path
from datetime import datetime

from utils import getLogger

log = getLogger('Auth')
log.setLevel(log.INFO)


class User:
    """User model for authentication"""

    def __init__(self, username, password_hash, email=None, created_at=None):
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.created_at = created_at or datetime.now().isoformat()
        self.is_authenticated = False
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return self.username

    def check_password(self, password):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at
        }


class UserManager:
    """Manages user authentication"""

    def __init__(self, users_file='data/users.json'):
        self.users_file = Path(users_file)
        self.users = {}
        self._load_users()

    def _load_users(self):
        """Load users from file"""
        try:
            if self.users_file.exists():
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        self.users[username] = User(
                            username=username,
                            password_hash=user_data['password_hash'],
                            email=user_data.get('email'),
                            created_at=user_data.get('created_at')
                        )
                log.info(f"Loaded {len(self.users)} users")
            else:
                # Create default admin user
                self.create_default_admin()
        except Exception as e:
            log.error(f"Error loading users: {e}")
            self.create_default_admin()

    def _save_users(self):
        """Save users to file"""
        try:
            self.users_file.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            for username, user in self.users.items():
                data[username] = {
                    'password_hash': user.password_hash,
                    'email': user.email,
                    'created_at': user.created_at
                }
            with open(self.users_file, 'w') as f:
                json.dump(data, f, indent=2)
            log.info("Users saved successfully")
        except Exception as e:
            log.error(f"Error saving users: {e}")

    def create_default_admin(self):
        """Create default admin user"""
        default_password = 'admin123'  # Change this in production!
        password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())

        admin = User(
            username='admin',
            password_hash=password_hash.decode('utf-8'),
            email='admin@wolfinch.local'
        )
        self.users['admin'] = admin
        self._save_users()

        log.warning("Created default admin user (username: admin, password: admin123)")
        log.warning("CHANGE THE DEFAULT PASSWORD IMMEDIATELY!")

    def create_user(self, username, password, email=None):
        """Create a new user"""
        if username in self.users:
            return False, "Username already exists"

        if len(password) < 6:
            return False, "Password must be at least 6 characters"

        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user = User(
                username=username,
                password_hash=password_hash.decode('utf-8'),
                email=email
            )
            self.users[username] = user
            self._save_users()
            log.info(f"Created user: {username}")
            return True, "User created successfully"
        except Exception as e:
            log.error(f"Error creating user: {e}")
            return False, str(e)

    def authenticate(self, username, password):
        """Authenticate a user"""
        user = self.users.get(username)
        if user and user.check_password(password):
            user.is_authenticated = True
            log.info(f"User authenticated: {username}")
            return user
        log.warning(f"Authentication failed for: {username}")
        return None

    def get_user(self, username):
        """Get user by username"""
        return self.users.get(username)

    def change_password(self, username, old_password, new_password):
        """Change user password"""
        user = self.users.get(username)
        if not user:
            return False, "User not found"

        if not user.check_password(old_password):
            return False, "Incorrect old password"

        if len(new_password) < 6:
            return False, "New password must be at least 6 characters"

        try:
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            user.password_hash = password_hash.decode('utf-8')
            self._save_users()
            log.info(f"Password changed for user: {username}")
            return True, "Password changed successfully"
        except Exception as e:
            log.error(f"Error changing password: {e}")
            return False, str(e)

    def delete_user(self, username):
        """Delete a user"""
        if username == 'admin':
            return False, "Cannot delete admin user"

        if username in self.users:
            del self.users[username]
            self._save_users()
            log.info(f"Deleted user: {username}")
            return True, "User deleted successfully"
        return False, "User not found"


# Global user manager instance
_user_manager = None


def get_user_manager():
    """Get global user manager instance"""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager


# EOF
