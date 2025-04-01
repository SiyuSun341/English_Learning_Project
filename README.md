# Interactive English Learning

An AI-powered application for improving English reading comprehension and speaking skills through interactive exercises and feedback.

## Overview

This project combines several AI technologies to create an interactive English learning experience:

- **Reading Comprehension**: Upload or select English passages and generate comprehension questions using AI
- **Speech Recognition**: Record your answers using your microphone or upload audio files
- **Intelligent Feedback**: Receive detailed analysis of your answers, including content accuracy and grammar suggestions

## Features

- AI-generated comprehension questions based on any English text
- Text and voice input options for answering questions
- Detailed feedback on answers with grammar and content suggestions
- Navigation between questions with session state preservation
- Speech-to-text conversion using OpenAI's Whisper API

## Installation

1. Clone this repository:
git clone https://github.com/YourUsername/interactive-english-learning.git
cd interactive-english-learning
Copy
2. Create a virtual environment and activate it:
python -m venv venv
On Windows
venv\Scripts\activate
On macOS/Linux
source venv/bin/activate
Copy
3. Install the required packages:
pip install -r requirements.txt
Copy
4. Create a `.env` file in the project root and add your OpenAI API key:
OPENAI_API_KEY=your_openai_api_key_here
Copy
## Usage

1. Run the Streamlit application:
streamlit run app.py
Copy
2. Open your web browser and navigate to `http://localhost:8501`

3. Enter or select an English passage for reading comprehension

4. Generate questions by clicking the "Generate Questions" button

5. Answer questions by typing in the text area or using the voice recording feature

6. Submit your answers to receive AI-powered feedback

## Requirements

- Python 3.7+
- OpenAI API key
- Web browser with microphone access (for voice recording feature)
- Internet connection for API calls

## Project Structure
.
├── app.py                   # Main Streamlit application
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in repository)
├── static/                  # Static assets
│   └── audio/               # Audio recordings storage
└── utils/                   # Utility modules
    ├── __init__.py          # Package initialization
    ├── language_model.py    # Language model interactions
    └── speech_to_text.py    # Speech recognition functionality

## Upcoming Features

- User authentication and profile management
- Vocabulary notebook for saving and reviewing new words
- Personalized review schedule based on performance
- Progress tracking and analytics
- Enhanced user interface with customization options

## Technologies Used

- [Streamlit](https://streamlit.io/): Web application framework
- [LangChain](https://langchain.readthedocs.io/): Language model integration
- [OpenAI API](https://openai.com/): GPT models for question generation and answer analysis
- [OpenAI Whisper API](https://openai.com/research/whisper): Speech-to-text conversion

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
