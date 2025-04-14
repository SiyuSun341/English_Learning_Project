"""
Database module for the English learning application
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import bcrypt
from datetime import datetime
import json

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        """Initialize database connection"""
        # Get MongoDB connection string from environment variable
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        
        # Connect to MongoDB
        self.client = MongoClient(mongo_uri)
        
        # Create or access the database
        self.db = self.client["english_learning_app"]
        
        # Access collections
        self.users = self.db["users"]
        self.learning_sessions = self.db["learning_sessions"]
        self.vocabulary = self.db["vocabulary"]
        
        # Create indexes for faster queries
        self.users.create_index("username", unique=True)
        self.users.create_index("email", unique=True)
    
    def register_user(self, username, email, password):
        """
        Register a new user
        
        Args:
            username (str): User's username
            email (str): User's email
            password (str): User's password
            
        Returns:
            dict: User document or None if registration failed
        """
        try:
            # Check if username or email already exists
            if self.users.find_one({"$or": [{"username": username}, {"email": email}]}):
                return None
            
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create user document
            user = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "created_at": datetime.now(),
                "last_login": datetime.now()
            }
            
            # Insert user to database
            result = self.users.insert_one(user)
            
            # Return user document without password
            user_doc = self.users.find_one({"_id": result.inserted_id})
            user_doc.pop("password", None)  # Remove password from result
            
            return user_doc
            
        except Exception as e:
            print(f"Error during registration: {str(e)}")
            return None
    
    def login_user(self, username, password):
        """
        Authenticate a user
        
        Args:
            username (str): User's username
            password (str): User's password
            
        Returns:
            dict: User document or None if authentication failed
        """
        try:
            # Find user by username
            user = self.users.find_one({"username": username})
            
            if not user:
                return None
            
            # Check password
            if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
                # Update last login time
                self.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"last_login": datetime.now()}}
                )
                
                # Return user document without password
                user.pop("password", None)
                return user
            else:
                return None
                
        except Exception as e:
            print(f"Error during login: {str(e)}")
            return None
    
    def save_learning_session(self, user_id, passage, questions, answers, feedback, score=None):
        """
        Save a learning session for a user
        
        Args:
            user_id: User's ID
            passage (str): The reading passage
            questions (list): List of questions
            answers (dict): Dict mapping question index to answers
            feedback (dict): Dict mapping question index to feedback
            score (int, optional): Session score out of 100. If None, will be calculated.
            
        Returns:
            dict: Session document or None if saving failed
        """
        try:
            # Calculate score if not provided
            if score is None:
                score = self._calculate_score(feedback)
            
            # Create session document
            session = {
                "user_id": user_id,
                "passage": passage,
                "questions": questions,
                "answers": answers,
                "feedback": feedback,
                "created_at": datetime.now(),
                "score": score
            }
            
            # Insert session to database
            result = self.learning_sessions.insert_one(session)
            
            # Return session document
            return self.learning_sessions.find_one({"_id": result.inserted_id})
            
        except Exception as e:
            print(f"Error saving learning session: {str(e)}")
            return None
    
    def get_user_learning_sessions(self, user_id):
        """
        Get all learning sessions for a user
        
        Args:
            user_id: User's ID
            
        Returns:
            list: List of session documents
        """
        try:
            # Find sessions by user_id
            sessions = list(self.learning_sessions.find({"user_id": user_id}))
            return sessions
            
        except Exception as e:
            print(f"Error getting learning sessions: {str(e)}")
            return []
    
    def save_vocabulary_item(self, user_id, word, definition, examples, source_passage="", source_question=""):
        """
        Save a vocabulary item for a user
        
        Args:
            user_id: User's ID
            word (str): The vocabulary word
            definition (str): Word definition
            examples (list): Example sentences
            source_passage (str): Original passage where the word was found
            source_question (str): Related question if applicable
            
        Returns:
            dict: Vocabulary document or None if saving failed
        """
        try:
            # Create vocabulary document
            vocab_item = {
                "user_id": user_id,
                "word": word,
                "definition": definition,
                "examples": examples,
                "source_passage": source_passage,
                "source_question": source_question,
                "created_at": datetime.now(),
                "review_count": 0,
                "last_review": None,
                "next_review": None
            }
            
            # Insert vocabulary item to database
            result = self.vocabulary.insert_one(vocab_item)
            
            # Return vocabulary document
            return self.vocabulary.find_one({"_id": result.inserted_id})
            
        except Exception as e:
            print(f"Error saving vocabulary item: {str(e)}")
            return None
    
    def get_user_vocabulary(self, user_id):
        """
        Get all vocabulary items for a user
        
        Args:
            user_id: User's ID
            
        Returns:
            list: List of vocabulary documents
        """
        try:
            # Find vocabulary items by user_id
            vocab_items = list(self.vocabulary.find({"user_id": user_id}))
            return vocab_items
            
        except Exception as e:
            print(f"Error getting vocabulary items: {str(e)}")
            return []
    
    def _calculate_score(self, feedback):
        """
        Calculate a score based on feedback (improved implementation)
        
        Args:
            feedback (dict): Dict mapping question index to feedback
            
        Returns:
            int: Score between 0 and 100
        """
        if not feedback:
            return 0
        
        total_score = 0
        answered_questions = 0
        
        # Iterate through feedback items
        for idx, item in feedback.items():
            if isinstance(item, dict) and "data" in item:
                # New format with detailed scoring
                total_score += item["data"].get("total_score", 0)
                answered_questions += 1
            else:
                # Try to extract score from old format or use default
                try:
                    if isinstance(item, str) and "Total Score:" in item:
                        score_part = item.split("Total Score:")[1].strip()
                        score = int(score_part.split("/")[0].strip())
                        total_score += score
                    else:
                        # Default score if can't extract
                        total_score += 5  # Middle score (5 out of 10)
                except:
                    total_score += 5
                
                answered_questions += 1
        
        # Calculate average score
        if answered_questions > 0:
            avg_score = total_score / answered_questions
            return int(avg_score * 10)  # Convert to 0-100 scale
        
        return 0
    
    def close(self):
        """Close the database connection"""
        self.client.close()