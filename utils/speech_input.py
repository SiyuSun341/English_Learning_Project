import os
import streamlit as st
import streamlit.components.v1 as components

# Define the JavaScript for speech recognition
def speech_to_text():
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a simple HTML component with JavaScript for speech recognition
    speech_recognition_html = """
    <div>
        <button id="startButton" style="background-color: #4CAF50; color: white; padding: 10px 20px; 
                border: none; border-radius: 4px; cursor: pointer; margin-bottom: 10px;">
            Start Recording
        </button>
        <button id="stopButton" style="background-color: #f44336; color: white; padding: 10px 20px; 
                border: none; border-radius: 4px; cursor: pointer; margin-bottom: 10px; display: none;">
            Stop Recording
        </button>
        <p id="status">Click 'Start Recording' to begin speaking.</p>
        <p id="result" style="padding: 10px; border: 1px solid #ddd; min-height: 50px;"></p>
    </div>

    <script>
        const startButton = document.getElementById('startButton');
        const stopButton = document.getElementById('stopButton');
        const statusElement = document.getElementById('status');
        const resultElement = document.getElementById('result');
        
        let recognition;
        let finalTranscript = '';
        
        // Check if browser supports speech recognition
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';  // You can change language here
            
            recognition.onstart = function() {
                statusElement.textContent = 'Listening... Speak now.';
                startButton.style.display = 'none';
                stopButton.style.display = 'inline-block';
            };
            
            recognition.onresult = function(event) {
                let interimTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }
                
                resultElement.innerHTML = finalTranscript + '<i style="color: #999;">' + interimTranscript + '</i>';
                
                // Send data to Streamlit
                if (finalTranscript) {
                    parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: finalTranscript
                    }, '*');
                }
            };
            
            recognition.onerror = function(event) {
                statusElement.textContent = 'Error occurred in recognition: ' + event.error;
            };
            
            recognition.onend = function() {
                statusElement.textContent = 'Recording stopped. Click "Start Recording" to try again.';
                startButton.style.display = 'inline-block';
                stopButton.style.display = 'none';
            };
            
            startButton.onclick = function() {
                finalTranscript = '';
                resultElement.innerHTML = '';
                recognition.start();
            };
            
            stopButton.onclick = function() {
                recognition.stop();
            };
        } else {
            statusElement.textContent = 'Speech recognition is not supported in this browser.';
        }
    </script>
    """
    
    # Use st.components.v1.html to embed the HTML component
    return components.html(speech_recognition_html, height=200)

def main():
    st.title("Speech to Text Demo")
    
    # Use the custom speech-to-text component
    transcription = speech_to_text()
    
    if transcription:
        st.write("Transcription:", transcription)

if __name__ == "__main__":
    main()