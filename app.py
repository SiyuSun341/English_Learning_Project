# app.py
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
import os
import json
from utils.language_model import generate_questions, analyze_answer
import tempfile
from openai import OpenAI

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

def main():
    st.title("Interactive English Learning")
    
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
    
    # Sidebar configuration
    st.sidebar.header("Settings")
    api_key = st.sidebar.text_input("OpenAI API Key", 
                                   value=os.getenv("OPENAI_API_KEY", ""), 
                                   type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
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
                    
                    # Force a rerun to update the UI
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error generating questions: {str(e)}")
                    st.error("Please make sure your OpenAI API key is valid and has sufficient credits.")
    
    # If we have questions, show the Q&A interface
    else:
        # Show Q&A interface
        show_qa_interface()
        
        # Add reset button at the bottom
        if st.button("Reset and Generate New Questions"):
            # Clear session state
            st.session_state.questions = []
            st.session_state.answers = {}
            st.session_state.feedback = {}
            st.session_state.current_question_idx = 0
            
            # Force a rerun to refresh the UI
            st.rerun()

def show_qa_interface():
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
    saved_answer = st.session_state.answers.get(current_idx, "")
    
    # Answer text area
    user_answer = st.text_area(
        "Your Answer:", 
        value=saved_answer,
        height=150,
        key=f"answer_{current_idx}"
    )
    
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
            st.session_state.answers[current_idx] = user_answer
            
            with st.spinner("Analyzing your answer..."):
                try:
                    # Analyze the answer
                    feedback = analyze_answer(
                        questions[current_idx],
                        user_answer,
                        st.session_state.current_passage
                    )
                    
                    # Save the feedback
                    st.session_state.feedback[current_idx] = feedback
                    
                    # Force a rerun to update the UI
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error analyzing answer: {str(e)}")
    
    # Display feedback if available
    if current_idx in st.session_state.feedback:
        st.subheader("Feedback:")
        st.markdown(st.session_state.feedback[current_idx])
    
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

if __name__ == "__main__":
    main()