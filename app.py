# app.py
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
import os
import json
import tempfile
from openai import OpenAI
from datetime import datetime
import time

from utils.language_model import generate_questions, analyze_answer, get_word_definition
from utils.auth import init_auth_state, login_page, register_page, logout
from utils.database import Database

# Load environment variables
load_dotenv()

# Sample passage
DEFAULT_PASSAGE = """
Technology has revolutionized education in numerous ways over the past few decades. From the introduction of computers in classrooms to the widespread use of the internet, educational tools have evolved significantly. Today, students can access vast amounts of information instantly, collaborate with peers across the globe, and utilize interactive learning platforms.
"""

def speech_recognition_component():
    """Custom speech recognition component using browser's Web Speech API"""
    
    # Create a unique key for each invocation
    component_key = f"speech_recognition_{id(st.session_state)}"
    
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Speech Recognition</title>
        <style>
            .container {
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                box-sizing: border-box;
                font-family: Arial, sans-serif;
            }
            .button {
                padding: 10px 20px;
                margin: 5px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            .start-button {
                background-color: #4CAF50;
                color: white;
            }
            .stop-button {
                background-color: #f44336;
                color: white;
                display: none;
            }
            .use-button {
                background-color: #2196F3;
                color: white;
            }
            .status {
                margin: 10px 0;
                padding: 10px;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
            .result {
                margin: 10px 0;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-height: 60px;
                max-height: 150px;
                overflow-y: auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="controls">
                <button id="startButton" class="button start-button">Start Recording</button>
                <button id="stopButton" class="button stop-button">Stop Recording</button>
            </div>
            <div id="status" class="status">Click "Start Recording" to begin.</div>
            <div id="result" class="result"></div>
            <div>
                <form id="transcriptForm">
                    <input type="hidden" id="transcriptInput" name="transcript" value="">
                </form>
            </div>
        </div>

        <script>
            const startButton = document.getElementById('startButton');
            const stopButton = document.getElementById('stopButton');
            const statusElement = document.getElementById('status');
            const resultElement = document.getElementById('result');
            const transcriptInput = document.getElementById('transcriptInput');
            
            let recognition;
            let finalTranscript = '';
            
            // Check if browser supports speech recognition
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.lang = 'en-US';  // English language
                
                recognition.onstart = function() {
                    statusElement.textContent = 'Listening... Speak now.';
                    startButton.style.display = 'none';
                    stopButton.style.display = 'inline-block';
                };
                
                recognition.onresult = function(event) {
                    let interimTranscript = '';
                    
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) {
                            finalTranscript += event.results[i][0].transcript + ' ';
                        } else {
                            interimTranscript += event.results[i][0].transcript;
                        }
                    }
                    
                    resultElement.innerHTML = finalTranscript + '<i style="color: #999;">' + interimTranscript + '</i>';
                    
                    // Store the transcript
                    transcriptInput.value = finalTranscript.trim();
                    
                    // Send message to parent (Streamlit) with the transcript
                    if (finalTranscript) {
                        window.parent.postMessage({
                            type: "speech-recognition",
                            transcript: finalTranscript.trim()
                        }, "*");
                    }
                };
                
                recognition.onerror = function(event) {
                    statusElement.textContent = 'Error occurred: ' + event.error;
                    startButton.style.display = 'inline-block';
                    stopButton.style.display = 'none';
                };
                
                recognition.onend = function() {
                    statusElement.textContent = 'Recording stopped. Click "Start Recording" to try again.';
                    startButton.style.display = 'inline-block';
                    stopButton.style.display = 'none';
                };
                
                startButton.onclick = function() {
                    finalTranscript = '';
                    resultElement.innerHTML = '';
                    transcriptInput.value = '';
                    recognition.start();
                };
                
                stopButton.onclick = function() {
                    recognition.stop();
                };
            } else {
                statusElement.textContent = 'Speech recognition is not supported in this browser. Please try Chrome, Edge, or Safari.';
                startButton.disabled = true;
            }
            
            // Function to send transcript to Streamlit
            function sendTranscriptToStreamlit() {
                const transcript = transcriptInput.value;
                if (transcript) {
                    window.parent.postMessage({
                        type: "speech-recognition",
                        transcript: transcript
                    }, "*");
                }
            }
            
            // Send transcript when the page is about to unload
            window.addEventListener('beforeunload', sendTranscriptToStreamlit);
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=250)
    
    # Return any transcript that was stored in session state
    return st.session_state.get("speech_transcript", "")

def transcribe_with_whisper(audio_file):
    """
    Transcribe audio using OpenAI's Whisper API
    
    Args:
        audio_file: Audio file uploaded by the user
        
    Returns:
        str: Transcribed text
    """
    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
            temp_audio_file.write(audio_file.getvalue())
            temp_audio_file_path = temp_audio_file.name
        
        # Use OpenAI's Whisper API to transcribe the audio
        client = OpenAI()
        
        with open(temp_audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # Clean up the temporary file
        os.unlink(temp_audio_file_path)
        
        return transcription.text
    
    except Exception as e:
        st.error(f"Error during transcription: {str(e)}")
        return None

def save_session(db, user_id):
    """Save the current learning session to the database"""
    if 'questions' in st.session_state and st.session_state.questions:
        # Only save if there are questions and answers
        if st.session_state.answers:
            # Calculate session score
            total_score = 0
            answered_questions = 0
            
            # Iterate through all feedback
            for idx in range(len(st.session_state.questions)):
                idx_str = str(idx)
                if idx_str in st.session_state.feedback:
                    feedback = st.session_state.feedback[idx_str]
                    if isinstance(feedback, dict) and "data" in feedback:
                        # New format
                        total_score += feedback["data"].get("total_score", 0)
                    else:
                        # Try to extract score from old format
                        try:
                            # Look for "Total Score: X/10" pattern
                            if isinstance(feedback, str) and "Total Score:" in feedback:
                                score_part = feedback.split("Total Score:")[1].strip()
                                score = int(score_part.split("/")[0].strip())
                                total_score += score
                            else:
                                # Default score if can't extract
                                total_score += 5
                        except:
                            total_score += 5
                    
                    answered_questions += 1
            
            # Calculate average score (out of 100)
            session_score = 0
            if answered_questions > 0:
                avg_score = total_score / answered_questions
                session_score = int(avg_score * 10)  # Convert to 0-100 scale
            
            # Save the session with score
            db.save_learning_session(
                user_id=user_id,
                passage=st.session_state.current_passage,
                questions=st.session_state.questions,
                answers=st.session_state.answers,
                feedback=st.session_state.feedback,
                score=session_score
            )
            return True
    return False

def show_history(db, user_id):
    """Show user's learning history"""
    st.header("Your Learning History")
    
    # Get user's learning sessions
    sessions = db.get_user_learning_sessions(user_id)
    
    if not sessions:
        st.info("You haven't completed any learning sessions yet.")
        return
    
    # Display sessions in reverse chronological order
    for idx, session in enumerate(sorted(sessions, key=lambda x: x.get('created_at', ''), reverse=True)):
        created_at = session.get('created_at', datetime.now())
        formatted_date = created_at.strftime("%B %d, %Y at %I:%M %p")
        
        with st.expander(f"Session {idx+1} - {formatted_date}"):
            # Calculate statistics
            num_questions = len(session.get('questions', []))
            num_answered = len(session.get('answers', {}))
            score = session.get('score', 0)
            
            # Show session stats
            st.write(f"**Questions:** {num_questions}")
            st.write(f"**Questions Answered:** {num_answered}")
            st.write(f"**Score:** {score}/100")
            
            # Add a button to show details
            if st.button(f"View Details", key=f"view_details_{idx}"):
                st.subheader("Reading Passage")
                st.write(session.get('passage', 'No passage available'))
                
                st.subheader("Questions and Answers")
                questions = session.get('questions', [])
                answers = session.get('answers', {})
                feedback = session.get('feedback', {})
                
                for q_idx, question in enumerate(questions):
                    st.markdown(f"**Question {q_idx+1}:** {question}")
                    
                    # Show answer if available
                    if str(q_idx) in answers:
                        st.markdown(f"**Your Answer:** {answers[str(q_idx)]}")
                    else:
                        st.write("You did not answer this question.")
                    
                    # Show feedback if available
                    if str(q_idx) in feedback:
                        feedback_item = feedback[str(q_idx)]
                        st.subheader("Feedback:")
                        
                        # Check if feedback is in the new format or old format
                        if isinstance(feedback_item, dict) and "formatted_feedback" in feedback_item:
                            # Display the formatted feedback
                            st.markdown(feedback_item["formatted_feedback"])
                        else:
                            # Display legacy format feedback
                            st.markdown(f"**Feedback:** {feedback_item}")
                    
                    st.markdown("---")

def vocabulary_notebook(db, user_id):
    """Show and manage vocabulary notebook"""
    st.header("Vocabulary Notebook")
    
    # Tabs for different vocabulary functions
    tab1, tab2 = st.tabs(["My Vocabulary", "Add New Word"])
    
    with tab1:
        # Get user's vocabulary
        vocab_items = db.get_user_vocabulary(user_id)
        
        if not vocab_items:
            st.info("Your vocabulary notebook is empty. Add words to start learning!")
        else:
            # Display vocabulary items without using nested expanders
            for idx, item in enumerate(vocab_items):
                with st.container():
                    st.markdown(f"### {idx+1}. {item['word']}")
                    st.write(f"**Definition:** {item['definition']}")
                    
                    st.write("**Examples:**")
                    for example in item['examples']:
                        st.write(f"- {example}")
                    
                    # Show source if available in a simple collapsible section (not an expander)
                    if item.get('source_passage'):
                        if st.checkbox(f"Show Source Passage for '{item['word']}'", key=f"source_{idx}"):
                            st.text_area("Source Passage", item['source_passage'], height=100, key=f"source_text_{idx}", disabled=True)
                    
                    # Add review button
                    if st.button(f"Mark as Reviewed", key=f"review_{idx}"):
                        # Update review count and dates in database
                        # (This functionality would need to be added to the database class)
                        st.success(f"'{item['word']}' marked as reviewed!")
                    
                    # Add a divider between words
                    st.markdown("---")
    
    with tab2:
        # Form to add new vocabulary
        with st.form("add_vocab_form"):
            word = st.text_input("Word")
            definition = st.text_area("Definition (optional)")
            examples = st.text_area("Example sentences (one per line, optional)")
            source = st.text_area("Source (optional)")
            
            submit = st.form_submit_button("Add to Notebook")
            
            if submit and word:
                # Process examples
                example_list = [ex.strip() for ex in examples.split('\n') if ex.strip()]
                
                # If definition is empty, try to get it from OpenAI
                if not definition or not example_list:
                    with st.spinner("Getting word definition..."):
                        try:
                            word_info = get_word_definition(word)
                            if word_info:
                                if not definition:
                                    definition = word_info.get('definition', '')
                                if not example_list:
                                    example_list = word_info.get('examples', [])
                        except Exception as e:
                            st.error(f"Error getting definition: {str(e)}")
                
                # Save to database
                try:
                    result = db.save_vocabulary_item(
                        user_id=user_id,
                        word=word,
                        definition=definition,
                        examples=example_list,
                        source_passage=source
                    )
                    
                    if result:
                        st.success(f"'{word}' added to your vocabulary notebook!")
                        # Clear form
                        st.experimental_rerun()
                    else:
                        st.error("Failed to add word to notebook.")
                except Exception as e:
                    st.error(f"Error saving to database: {str(e)}")

def show_qa_interface(db):
    """Show the Q&A interface for answering and getting feedback"""
    # Get current question
    questions = st.session_state.questions
    current_idx = st.session_state.current_question_idx
    
    # Display passage for reference
    with st.expander("Show Reading Passage", expanded=False):
        st.write(st.session_state.current_passage)
    
    # Display all questions with the current one highlighted
    st.subheader("Reading Comprehension Questions:")
    for i, q in enumerate(questions):
        if i == current_idx:
            st.markdown(f"**{i+1}. {q}** (Current Question)")
        else:
            st.markdown(f"{i+1}. {q}")
    
    st.markdown("---")
    
    # Current question and answer area
    st.subheader(f"Question {current_idx + 1}:")
    st.write(questions[current_idx])
    
    # Get saved answer if any
    saved_answer = st.session_state.answers.get(str(current_idx), "")
    
    # Answer text area
    user_answer = st.text_area(
        "Your Answer:", 
        value=saved_answer,
        height=150,
        key=f"answer_{current_idx}"
    )
    
    # Add "Save to Vocabulary" feature for text selection
    if st.session_state.user:
        selected_word = st.text_input("Add word to vocabulary (select text from passage or question):", 
                                      key="selected_word")
        if selected_word and st.button("Add to Vocabulary"):
            with st.spinner("Adding to vocabulary..."):
                # Get definition
                word_info = get_word_definition(selected_word)
                if word_info:
                    # Save to database
                    db.save_vocabulary_item(
                        user_id=st.session_state.user["_id"],
                        word=selected_word,
                        definition=word_info.get('definition', ''),
                        examples=word_info.get('examples', []),
                        source_passage=st.session_state.current_passage,
                        source_question=questions[current_idx]
                    )
                    st.success(f"'{selected_word}' added to your vocabulary notebook!")
    
    # Speech recognition section
    st.write("Or record your answer:")
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["Microphone", "Upload Audio"])
    
    with tab1:
        st.write("Use your browser's microphone to record your answer:")
        
        # Add the speech recognition component
        speech_recognition_component()
        
        # Check if we have a transcript
        if st.session_state.speech_transcript:
            st.success("Speech transcription successful!")
            st.info(f"Transcribed text: {st.session_state.speech_transcript}")
            
            if st.button("Use this transcription as my answer"):
                # Update the answer with the transcription
                st.session_state[f"answer_{current_idx}"] = st.session_state.speech_transcript
                # Clear the transcript
                st.session_state.speech_transcript = ""
                st.rerun()
    
    with tab2:
        st.write("Upload an audio recording:")
        uploaded_file = st.file_uploader("Upload audio (.wav, .mp3)", type=["wav", "mp3"], key=f"upload_{current_idx}")
        
        if uploaded_file:
            st.audio(uploaded_file)
            if st.button("Transcribe Audio"):
                with st.spinner("Transcribing..."):
                    transcribed_text = transcribe_with_whisper(uploaded_file)
                    if transcribed_text:
                        st.success("Transcription successful!")
                        st.info(f"Transcribed text: {transcribed_text}")
                        
                        if st.button("Use this transcription as my answer"):
                            st.session_state[f"answer_{current_idx}"] = transcribed_text
                            st.rerun()
    
    # Submit button for the answer
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Submit Answer"):
            if not user_answer.strip():
                st.warning("Please enter an answer before submitting")
                return
                
            # Save the answer
            st.session_state.answers[str(current_idx)] = user_answer
            
            with st.spinner("Analyzing your answer..."):
                try:
                    # Analyze the answer
                    feedback = analyze_answer(
                        questions[current_idx],
                        user_answer,
                        st.session_state.current_passage
                    )
                    
                    # Save the feedback
                    st.session_state.feedback[str(current_idx)] = feedback
                    
                    # Auto-save if user is logged in
                    if st.session_state.authenticated and st.session_state.user:
                        save_session(db, st.session_state.user["_id"])
                    
                    # Force a rerun to update the UI
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error analyzing answer: {str(e)}")
    
    # Display feedback if available
    if str(current_idx) in st.session_state.feedback:
        st.subheader("Feedback:")
        
        feedback = st.session_state.feedback[str(current_idx)]
        
        # Check if feedback is in the new format or old format
        if isinstance(feedback, dict) and "formatted_feedback" in feedback:
            # Display the formatted feedback
            st.markdown(feedback["formatted_feedback"])
            
            # Show scoring rubric in an expander
            with st.expander("View Scoring Rubric"):
                st.markdown("""
                ### Reading Comprehension Scoring System
                
                Total per question: **10 points** across the following dimensions:
                
                | Scoring Dimension | Max Points | Description |
                | --- | --- | --- |
                | **1. Accuracy** | 4 points | How accurately the answer reflects the content of the passage. |
                | **2. Completeness** | 2 points | How thoroughly the answer covers all aspects of the question. |
                | **3. Clarity** | 1 point | How clear and understandable the answer is. |
                | **4. Language Quality** | 3 points | Grammar, spelling, and appropriate word choice. |
                
                ### 📏 Scoring Scale Reference
                
                | Score | Description |
                | --- | --- |
                | **10 points** | Answer is accurate, complete, clear, and has excellent grammar. |
                | **8-9 points** | Answer is mostly accurate with minor omissions or occasional language errors. |
                | **6-7 points** | Answer is partially correct but lacks thoroughness or has noticeable language issues. |
                | **4-5 points** | Answer significantly diverges from passage content or has numerous language errors. |
                | **1-3 points** | Answer is mostly irrelevant or difficult to understand. |
                | **0 points** | No answer provided or completely incorrect. |
                """)
        else:
            # Display legacy format feedback
            st.markdown(feedback)
    
    # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if current_idx > 0:
            if st.button("Previous Question"):
                st.session_state.current_question_idx -= 1
                st.rerun()
    
    with col2:
        if current_idx < len(questions) - 1:
            if st.button("Next Question"):
                st.session_state.current_question_idx += 1
                st.rerun()

def main():
    # Initialize session state
    init_auth_state()
    
    # Initialize session state variables if they don't exist
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'current_passage' not in st.session_state:
        st.session_state.current_passage = DEFAULT_PASSAGE
    if 'current_question_idx' not in st.session_state:
        st.session_state.current_question_idx = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'feedback' not in st.session_state:
        st.session_state.feedback = {}
    if 'speech_transcript' not in st.session_state:
        st.session_state.speech_transcript = ""
    
    # Handle speech recognition messages from JavaScript
    if 'speech_transcript' in st.query_params:
        transcript = st.query_params['speech_transcript']
        if transcript:
            st.session_state.speech_transcript = transcript
            # Clear the query param to avoid issues with refreshes
            del st.query_params['speech_transcript']
    
    # Create database instance
    db = Database()
    
    # Sidebar configuration
    st.sidebar.header("Settings")
    api_key = st.sidebar.text_input("OpenAI API Key", 
                                   value=os.getenv("OPENAI_API_KEY", ""), 
                                   type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    # Check if user is authenticated
    if not st.session_state.authenticated:
        # Show login/register pages
        if st.session_state.show_login:
            if login_page():
                st.rerun()
        elif st.session_state.show_register:
            if register_page():
                st.rerun()
        return
    
    # User is authenticated - show application
    st.title("Interactive English Learning")
    
    # Show user info in sidebar
    st.sidebar.success(f"Logged in as: {st.session_state.user['username']}")
    
    # Navigation menu in sidebar
    st.sidebar.header("Navigation")
    app_mode = st.sidebar.radio(
        "Choose a feature",
        ["Practice Reading", "Learning History", "Vocabulary Notebook"]
    )
    
    # Logout button
    if st.sidebar.button("Logout"):
        # Save current session before logout if needed
        if st.session_state.authenticated and st.session_state.user and 'questions' in st.session_state:
            save_session(db, st.session_state.user["_id"])
        logout()
        st.rerun()
    
    # Main content based on selected mode
    if app_mode == "Practice Reading":
        # If we don't have questions yet, show the passage input and question generation interface
        if not st.session_state.questions:
            # Article input
            st.header("Reading Material")
            passage = st.text_area("Enter or paste an English passage", value=DEFAULT_PASSAGE, height=200)
            
            num_questions = st.slider("Number of questions to generate", 1, 5, 3)
            
            if st.button("Generate Questions"):
                if not passage.strip():
                    st.warning("Please enter a passage")
                    return
                    
                with st.spinner("Generating questions..."):
                    try:
                        # Use the question generation function
                        questions = generate_questions(passage, num_questions)
                        
                        # Save to session state
                        st.session_state.questions = questions
                        st.session_state.current_passage = passage
                        st.session_state.current_question_idx = 0
                        st.session_state.answers = {}
                        st.session_state.feedback = {}
                        
                        # Force a rerun to update the UI
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error generating questions: {str(e)}")
                        st.error("Please make sure your OpenAI API key is valid and has sufficient credits.")
        
        # If we have questions, show the Q&A interface
        else:
            # Show Q&A interface
            show_qa_interface(db)
            
            # Add reset button at the bottom
            if st.button("Reset and Generate New Questions"):
                # Save current session before reset
                if st.session_state.authenticated and st.session_state.user:
                    save_session(db, st.session_state.user["_id"])
                
                # Clear session state for questions
                st.session_state.questions = []
                st.session_state.answers = {}
                st.session_state.feedback = {}
                st.session_state.current_question_idx = 0
                
                # Force a rerun to refresh the UI
                st.rerun()
    
    elif app_mode == "Learning History":
        # Show learning history
        if st.session_state.authenticated and st.session_state.user:
            show_history(db, st.session_state.user["_id"])
        else:
            st.warning("You need to be logged in to view your learning history.")
    
    elif app_mode == "Vocabulary Notebook":
        # Show vocabulary notebook
        if st.session_state.authenticated and st.session_state.user:
            vocabulary_notebook(db, st.session_state.user["_id"])
        else:
            st.warning("You need to be logged in to access your vocabulary notebook.")

    # Close database connection
    db.close()

if __name__ == "__main__":
    main()