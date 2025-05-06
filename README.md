# Interactive English Learning

A comprehensive AI-powered platform for English language learners to improve reading comprehension and speaking skills through personalized feedback, intelligent vocabulary management, and data-driven insights.

## Overview

The Interactive English Learning application leverages cutting-edge AI technologies to create an adaptive learning environment that simulates real-world language usage scenarios. By combining large language models, speech recognition, and cognitive science principles, the system provides personalized guidance, detailed feedback, and systematic vocabulary development.

### Core Features

- **AI-Generated Comprehension Questions**: Practice with dynamically created questions based on any text passage
- **Multi-dimensional Feedback**: Receive detailed assessment on accuracy, completeness, clarity, and language quality
- **Speech-to-Text Capabilities**: Practice verbal responses with advanced transcription technology
- **Intelligent Vocabulary Management**: Build vocabulary with AI-generated definitions and examples
- **Spaced Repetition System**: Optimize vocabulary retention through scientifically-proven review scheduling
- **Personalized Learning Analytics**: Get data-driven insights and tailored recommendations for improvement

## Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB (local or cloud instance)
- OpenAI API key

### Setup

1. Clone the repository:
git clone https://github.com/SiyuSun341/English_Learning_Project.git
cd interactive-english-learning

2. Create and activate a virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:
pip install -r requirements.txt

4. Create a `.env` file in the project root with the following variables:
OPENAI_API_KEY=your_openai_api_key
MONGODB_URI=your_mongodb_connection_string

5. Run the application:
streamlit run app.py

## Project Structure
interactive-english-learning/
├── app.py                  # Main application entry point

├── requirements.txt        # Project dependencies

├── README.md               # Project documentation

├── .env                    # Environment variables (create this file)

├── static/                 # Static assets

│   └── audio/              # Audio resources

├── utils/                  # Utility modules

│   ├── init.py

│   ├── auth.py             # Authentication functionality

│   ├── database.py         # Database operations

│   ├── language_model.py   # AI language model interactions

│   ├── speech_input.py     # Speech recording functionality

│   └── speech_to_text.py   # Speech transcription

└── venv/                   # Virtual environment (create this directory)

## Usage Guide

### Registration and Login

1. On first visit, click "Register" to create a new account
2. Provide a username, email, and secure password
3. After registration, you'll be automatically logged in
4. For subsequent visits, use the login form with your credentials

### Reading Comprehension Practice

1. Navigate to the "Practice Reading" section
2. Use the default passage or paste your own English text
3. Select the number of questions to generate (1-5)
4. Click "Generate Questions" to create AI-powered comprehension questions
5. Answer each question in the text area or using voice input
6. Submit your answer to receive detailed feedback
7. Navigate between questions using the "Previous" and "Next" buttons

### Voice Recording Options

1. When answering questions, you have two voice input options:
   - Use the microphone tab to record directly in your browser
   - Use the upload tab to submit a pre-recorded audio file (.wav or .mp3)
2. After recording or uploading, the system will transcribe your speech
3. Review the transcription and click "Use this transcription" to set it as your answer

### Vocabulary Notebook

1. Navigate to the "Vocabulary Notebook" section
2. Use the "Add New Word" tab to manually add vocabulary
3. When practicing reading, select text and click "Add to Vocabulary" to add words directly from passages
4. Review your vocabulary list in the "My Vocabulary" tab
5. Use the "Words Due for Review" tab to practice words scheduled for review
6. Filter words by review count to focus on specific learning stages
7. Mark words as reviewed individually or in batches

### Learning Analytics

1. Navigate to the "Learning History" section
2. View your past learning sessions in the "Session History" tab
3. Explore detailed statistics in the "Learning Analytics" tab:
   - Score progress over time
   - Performance by learning dimension
   - Vocabulary growth
   - Activity patterns
4. Review personalized insights and recommendations tailored to your learning patterns
5. Follow the suggested study plan and metacognitive strategies

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: MongoDB
- **AI Services**:
  - OpenAI GPT models for question generation and answer analysis
  - OpenAI Whisper for speech recognition
- **Data Visualization**: Plotly
- **Data Processing**: Pandas
- **Authentication**: Bcrypt

## Development Roadmap

### Completed
- ✅ Core reading comprehension functionality
- ✅ Speech-to-text integration
- ✅ User authentication and data persistence
- ✅ Enhanced feedback system
- ✅ Vocabulary notebook feature
- ✅ Spaced repetition review system
- ✅ Comprehensive learning analytics

### Future Enhancements
- Mobile application development
- Community and social learning features
- Content recommendation system
- Support for additional languages
- Integration with external language resources

## Contributors

- Siyu (Suzy) Sun
- Yuling (Winnie) Wang

## License

This project is licensed under the MIT License - see the LICENSE file for details.
