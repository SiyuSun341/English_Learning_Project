"""
Authentication module for the English learning application
"""
import streamlit as st
from utils.database import Database

def login_page():
    """
    Display login page and handle authentication
    
    Returns:
        bool: True if user is authenticated, False otherwise
    """
    st.title("Login")
    
    # Create database instance
    db = Database()
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if not username or not password:
                st.error("Please enter both username and password")
                return False
                
            # Attempt login
            user = db.login_user(username, password)
            
            if user:
                # Set user in session state
                st.session_state.user = user
                st.session_state.authenticated = True
                st.success(f"Welcome back, {user['username']}!")
                return True
            else:
                st.error("Invalid username or password")
                return False
    
    # Link to registration page
    st.write("Don't have an account?")
    if st.button("Register"):
        st.session_state.show_register = True
        st.session_state.show_login = False

    return False

def register_page():
    """
    Display registration page and handle user registration
    
    Returns:
        bool: True if registration is successful, False otherwise
    """
    st.title("Register")
    
    # Create database instance
    db = Database()
    
    # Registration form
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Register")
        
        if submit_button:
            # Validate input
            if not username or not email or not password:
                st.error("Please fill in all required fields")
                return False
                
            if password != confirm_password:
                st.error("Passwords do not match")
                return False
                
            # Attempt registration
            user = db.register_user(username, email, password)
            
            if user:
                # Set user in session state
                st.session_state.user = user
                st.session_state.authenticated = True
                st.success("Registration successful! You are now logged in.")
                return True
            else:
                st.error("Username or email already exists")
                return False
    
    # Link to login page
    st.write("Already have an account?")
    if st.button("Login"):
        st.session_state.show_register = False
        st.session_state.show_login = True

    return False

def init_auth_state():
    """Initialize authentication state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'show_login' not in st.session_state:
        st.session_state.show_login = True
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False

def logout():
    """Log out the current user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.show_login = True
    st.session_state.show_register = False