# Interactive English Learning

An AI-powered application for improving English reading comprehension and speaking skills through interactive exercises, personalized feedback, and vocabulary management.

## Overview

This project combines several AI technologies to create a comprehensive English learning experience:

- **Reading Comprehension**: Generate AI-powered questions from any English passage
- **Speech Recognition**: Record answers using your microphone or upload audio files
- **Intelligent Feedback**: Receive detailed analysis with a robust scoring system
- **Vocabulary Management**: Build and organize your vocabulary with automatic definitions
- **Progress Tracking**: Review your learning history and performance over time

## Features

### Core Functionality
- AI-generated comprehension questions based on any English text
- Text and voice input options for answering questions
- Detailed feedback with multi-dimensional scoring (Accuracy, Completeness, Clarity, Language Quality)
- Specific grammar and spelling error identification with corrections
- Session state preservation to maintain progress

### User Management
- User registration and authentication system
- Secure password storage with bcrypt encryption
- Personalized learning history tracking
- MongoDB integration for data persistence

### Vocabulary System
- Smart vocabulary notebook with deduplication
- Automatic word definitions and example generation
- Tracking word frequency and usage
- Source passage reference for context
- Words prioritized by frequency of addition

### Speech Recognition
- Browser-based recording using Web Speech API
- Audio file upload support
- OpenAI Whisper API integration for accurate transcription

## Installation

1. Clone this repository:
```
git clone https://github.com/YourUsername/interactive-english-learning.git
cd interactive-english-learning
```

2. Create a virtual environment and activate it:
```
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install the required packages:
```
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
MONGODB_URI=your_mongodb_connection_string_here
```

## Usage

1. Run the Streamlit application:
```
streamlit run app.py
```

2. Open your web browser and navigate to http://localhost:8501

3. Register an account or log in

4. Choose a feature from the sidebar:
   - **Practice Reading**: Work on reading comprehension exercises
   - **Learning History**: Review past sessions and performance
   - **Vocabulary Notebook**: Manage your personal vocabulary collection

## Project Structure
```
.
├── app.py                   # Main Streamlit application
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in repository)
├── utils/                   # Utility modules
│   ├── __init__.py          # Package initialization
│   ├── auth.py              # Authentication functionality
│   ├── database.py          # MongoDB database operations
│   ├── language_model.py    # Language model interactions
│   ├── speech_input.py      # Speech input component
│   └── speech_to_text.py    # Speech recognition functionality
```

## Technologies Used

- **Streamlit**: Web application framework
- **MongoDB**: Database for user data and learning history
- **LangChain**: Language model integration and prompt engineering
- **OpenAI API**: 
  - GPT models for question generation and answer analysis
  - Whisper API for speech-to-text conversion
- **Web Speech API**: Browser-based speech recognition
- **bcrypt**: Secure password hashing

## Future Enhancements

- Spaced repetition system for vocabulary review
- Enhanced data visualization for learning analytics
- Mobile-responsive design improvements
- Customizable learning focus areas
- Social features for learning communities
- Offline mode for practice without internet

## License
[Add your license information here]

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.