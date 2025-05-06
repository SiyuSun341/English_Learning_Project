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
    """Show user's learning history with enhanced statistics and visualizations"""
    st.header("Your Learning History")
    
    # Create tabs for history view and statistics
    history_tab, stats_tab = st.tabs(["Session History", "Learning Analytics"])
    
    # Get user's learning sessions
    sessions = db.get_user_learning_sessions(user_id)
    
    # Also get vocabulary data for some analytics
    vocab_items = db.get_user_vocabulary(user_id)
    
    with history_tab:
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
    
    with stats_tab:
        if not sessions:
            st.info("You need to complete some learning sessions to see analytics.")
            return
        
        st.subheader("Learning Performance Analytics")
        
        # Process session data for analysis
        session_dates = []
        session_scores = []
        dimension_scores = {
            "accuracy": [],
            "completeness": [],
            "clarity": [],
            "language": []
        }
        
        # Process all sessions for time-based data
        for session in sorted(sessions, key=lambda x: x.get('created_at', datetime.now())):
            session_date = session.get('created_at', datetime.now())
            session_dates.append(session_date)
            session_scores.append(session.get('score', 0))
            
            # Process feedback for dimension scores
            feedback = session.get('feedback', {})
            session_accuracy = []
            session_completeness = []
            session_clarity = []
            session_language = []
            
            for idx, item in feedback.items():
                if isinstance(item, dict) and "data" in item:
                    data = item.get("data", {})
                    if "accuracy_score" in data:
                        session_accuracy.append(data["accuracy_score"])
                    if "completeness_score" in data:
                        session_completeness.append(data["completeness_score"])
                    if "clarity_score" in data:
                        session_clarity.append(data["clarity_score"])
                    if "language_score" in data:
                        session_language.append(data["language_score"])
            
            # Calculate averages for this session and add to overall lists
            if session_accuracy:
                dimension_scores["accuracy"].append(sum(session_accuracy) / len(session_accuracy))
            if session_completeness:
                dimension_scores["completeness"].append(sum(session_completeness) / len(session_completeness))
            if session_clarity:
                dimension_scores["clarity"].append(sum(session_clarity) / len(session_clarity))
            if session_language:
                dimension_scores["language"].append(sum(session_language) / len(session_language))
        
        # Process vocabulary data
        vocab_dates = []
        vocab_counts = []
        vocab_review_counts = []
        
        if vocab_items:
            # Sort vocab items by creation date
            sorted_vocab = sorted(vocab_items, key=lambda x: x.get('created_at', datetime.now()))
            cumulative_count = 0
            
            for item in sorted_vocab:
                created_at = item.get('created_at', datetime.now())
                vocab_dates.append(created_at)
                cumulative_count += 1
                vocab_counts.append(cumulative_count)
                vocab_review_counts.append(item.get('review_count', 0))
        
        # Create a dictionary to track activity by date
        activity_by_date = {}
        
        # Process sessions for activity heatmap
        for session in sessions:
            session_date = session.get('created_at', datetime.now())
            date_str = session_date.strftime('%Y-%m-%d')
            activity_by_date[date_str] = activity_by_date.get(date_str, 0) + 1
        
        # Process vocabulary additions for activity heatmap
        for item in vocab_items:
            created_at = item.get('created_at', datetime.now())
            date_str = created_at.strftime('%Y-%m-%d')
            activity_by_date[date_str] = activity_by_date.get(date_str, 0) + 0.5  # Count vocab additions as 0.5 activity
            
            # Also count reviews
            if item.get('last_review'):
                review_date = item.get('last_review')
                date_str = review_date.strftime('%Y-%m-%d')
                activity_by_date[date_str] = activity_by_date.get(date_str, 0) + 0.3  # Count reviews as 0.3 activity
        
        # Now create the visualizations
        
        # 1. Time Series of Scores
        st.subheader("Score Progress Over Time")
        if len(session_dates) > 1:
            # Convert to format suitable for Streamlit charts
            score_chart_data = {
                "date": [d.strftime("%Y-%m-%d") for d in session_dates],
                "score": session_scores
            }
            
            # Create a DataFrame for the chart
            import pandas as pd
            score_df = pd.DataFrame(score_chart_data)
            
            # Create the chart
            st.line_chart(score_df.set_index("date"))
            
            # Add some insights
            avg_score = sum(session_scores) / len(session_scores)
            recent_avg = sum(session_scores[-3:]) / min(len(session_scores), 3) if session_scores else 0
            
            st.write(f"**Average Score:** {avg_score:.1f}/100")
            
            if recent_avg > avg_score:
                st.success(f"Your recent average of {recent_avg:.1f} is higher than your overall average. Great improvement!")
            elif recent_avg < avg_score:
                st.info(f"Your recent average of {recent_avg:.1f} is lower than your overall average. Consider reviewing earlier materials.")
        else:
            st.info("Complete more learning sessions to see your score progress over time.")
        
        # 2. Radar Chart for Dimension Scores
        st.subheader("Performance by Dimension")
        
        # Check if we have dimension data
        if (dimension_scores["accuracy"] and dimension_scores["completeness"] and 
            dimension_scores["clarity"] and dimension_scores["language"]):
            
            # Calculate averages for each dimension
            avg_accuracy = sum(dimension_scores["accuracy"]) / len(dimension_scores["accuracy"])
            avg_completeness = sum(dimension_scores["completeness"]) / len(dimension_scores["completeness"])
            avg_clarity = sum(dimension_scores["clarity"]) / len(dimension_scores["clarity"])
            avg_language = sum(dimension_scores["language"]) / len(dimension_scores["language"])
            
            # Create radar chart using Plotly
            import plotly.graph_objects as go
            import numpy as np
            
            # Normalize scores to percentages for the radar chart
            accuracy_pct = (avg_accuracy / 4) * 100
            completeness_pct = (avg_completeness / 2) * 100
            clarity_pct = (avg_clarity / 1) * 100
            language_pct = (avg_language / 3) * 100
            
            categories = ['Accuracy', 'Completeness', 'Clarity', 'Language Quality']
            values = [accuracy_pct, completeness_pct, clarity_pct, language_pct]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Average Performance'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                showlegend=False
            )
            
            st.plotly_chart(fig)
            
            # Display insights
            st.write("**Dimension Analysis:**")
            
            dimensions = [
                {"name": "Accuracy", "score": avg_accuracy, "max": 4, "color": "blue" if avg_accuracy >= 3 else "orange" if avg_accuracy >= 2 else "red"},
                {"name": "Completeness", "score": avg_completeness, "max": 2, "color": "blue" if avg_completeness >= 1.5 else "orange" if avg_completeness >= 1 else "red"},
                {"name": "Clarity", "score": avg_clarity, "max": 1, "color": "blue" if avg_clarity >= 0.75 else "orange" if avg_clarity >= 0.5 else "red"},
                {"name": "Language Quality", "score": avg_language, "max": 3, "color": "blue" if avg_language >= 2.25 else "orange" if avg_language >= 1.5 else "red"}
            ]
            
            # Sort dimensions by performance (worst to best)
            sorted_dimensions = sorted(dimensions, key=lambda x: x["score"] / x["max"])
            
            # Show strongest and weakest areas
            if sorted_dimensions:
                weakest = sorted_dimensions[0]
                strongest = sorted_dimensions[-1]
                
                st.markdown(f"🔥 **Strongest area:** {strongest['name']} ({strongest['score']:.2f}/{strongest['max']})")
                st.markdown(f"🔍 **Area for improvement:** {weakest['name']} ({weakest['score']:.2f}/{weakest['max']})")
                
                # Provide specific advice based on weakest area
                if weakest["name"] == "Accuracy":
                    st.info("**Tip:** Focus on carefully reading and understanding the passage before answering questions. Try highlighting key information while reading.")
                elif weakest["name"] == "Completeness":
                    st.info("**Tip:** Make sure to address all parts of the questions in your answers. Consider creating bullet points for complex questions before writing your full answer.")
                elif weakest["name"] == "Clarity":
                    st.info("**Tip:** Structure your answers with clear paragraphs and use transition words to connect ideas. Read your answers aloud to check if they sound clear.")
                elif weakest["name"] == "Language Quality":
                    st.info("**Tip:** Take time to proofread your answers before submitting. Pay attention to verb tenses and subject-verb agreement, which are common error areas.")
        else:
            st.info("Complete more detailed feedback sessions to see your performance by dimension.")
        
        # 3. Vocabulary Growth Chart
        st.subheader("Vocabulary Growth")
        if vocab_dates and vocab_counts:
            # Convert to format suitable for Streamlit charts
            vocab_chart_data = {
                "date": [d.strftime("%Y-%m-%d") for d in vocab_dates],
                "count": vocab_counts
            }
            
            # Create a DataFrame for the chart
            import pandas as pd
            vocab_df = pd.DataFrame(vocab_chart_data)
            
            # Create the chart
            st.line_chart(vocab_df.set_index("date"))
            
            # Add insights
            st.write(f"**Total vocabulary items:** {len(vocab_items)}")
            
            # Calculate words added in the last 7 days
            from datetime import timedelta
            one_week_ago = datetime.now() - timedelta(days=7)
            recent_vocab = sum(1 for item in vocab_items if item.get('created_at', datetime.now()) > one_week_ago)
            
            st.write(f"**Words added in the last 7 days:** {recent_vocab}")
            
            # Calculate review statistics
            total_reviews = sum(vocab_review_counts)
            reviewed_words = sum(1 for count in vocab_review_counts if count > 0)
            never_reviewed = len(vocab_items) - reviewed_words
            
            st.write(f"**Total reviews:** {total_reviews}")
            st.write(f"**Words never reviewed:** {never_reviewed} ({(never_reviewed/len(vocab_items))*100:.1f}% of your vocabulary)")
            
            if never_reviewed > 0:
                st.warning(f"You have {never_reviewed} words that haven't been reviewed yet. Regular review is key to vocabulary retention!")
        else:
            st.info("Add words to your vocabulary notebook to track vocabulary growth.")
        
        # 4. Activity Heatmap
        st.subheader("Learning Activity Calendar")
        if activity_by_date:
            # Create a date range for the heatmap
            import pandas as pd
            from datetime import timedelta
            
            # Get min and max dates from activity data
            dates = [datetime.strptime(date_str, '%Y-%m-%d') for date_str in activity_by_date.keys()]
            min_date = min(dates)
            max_date = max(dates)
            
            # Generate date range with zero activity
            all_dates = []
            current_date = min_date
            while current_date <= max_date:
                date_str = current_date.strftime('%Y-%m-%d')
                all_dates.append(date_str)
                current_date += timedelta(days=1)
            
            # Create complete dataset with activity levels
            complete_data = {
                "date": all_dates,
                "activity": [activity_by_date.get(date_str, 0) for date_str in all_dates]
            }
            
            # Create DataFrame
            activity_df = pd.DataFrame(complete_data)
            
            # Add year and day columns
            activity_df['dt'] = pd.to_datetime(activity_df['date'])
            activity_df['year'] = activity_df['dt'].dt.year
            activity_df['month'] = activity_df['dt'].dt.month
            activity_df['day'] = activity_df['dt'].dt.day
            activity_df['weekday'] = activity_df['dt'].dt.weekday
            
            # Create heatmap using Plotly
            import plotly.express as px
            
            # Create one heatmap per year
            years = activity_df['year'].unique()
            
            for year in years:
                year_data = activity_df[activity_df['year'] == year]
                
                # Create a pivot table for the heatmap
                pivot_data = year_data.pivot_table(
                    values='activity', 
                    index='weekday', 
                    columns='day', 
                    aggfunc='sum'
                )
                
                # Replace weekday numbers with names
                weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                pivot_data.index = [weekday_names[i] for i in pivot_data.index]
                
                # Create heatmap
                fig = px.imshow(
                    pivot_data,
                    labels=dict(x="Day of Month", y="Day of Week", color="Activity"),
                    title=f"Activity Calendar - {year}",
                    color_continuous_scale="Viridis"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Show activity insights
            active_days = sum(1 for level in activity_by_date.values() if level > 0)
            total_activity = sum(activity_by_date.values())
            
            st.write(f"**Active learning days:** {active_days}")
            st.write(f"**Average activity per active day:** {total_activity/active_days:.1f}")
            
            # Find most active day of week
            weekday_activity = [0] * 7  # Initialize counts for each day of the week
            for date_str, activity in activity_by_date.items():
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                weekday = date_obj.weekday()
                weekday_activity[weekday] += activity
            
            most_active_weekday = weekday_names[weekday_activity.index(max(weekday_activity))]
            st.write(f"**Most active day of the week:** {most_active_weekday}")
            
            # Identify current streak
            sorted_active_dates = sorted([datetime.strptime(date_str, '%Y-%m-%d') for date_str in activity_by_date.keys()])
            
            if sorted_active_dates:
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Check if today is active
                today_str = today.strftime('%Y-%m-%d')
                yesterday = today - timedelta(days=1)
                yesterday_str = yesterday.strftime('%Y-%m-%d')
                
                if today_str in activity_by_date:
                    # Start counting from today
                    streak_start = today
                    streak = 1
                elif yesterday_str in activity_by_date:
                    # Start counting from yesterday
                    streak_start = yesterday
                    streak = 1
                else:
                    streak = 0
                
                # Count backward from streak_start
                current_date = streak_start - timedelta(days=1)
                while streak > 0 and current_date.strftime('%Y-%m-%d') in activity_by_date:
                    streak += 1
                    current_date -= timedelta(days=1)
                
                if streak > 0:
                    st.success(f"🔥 **Current streak:** {streak} day{'s' if streak > 1 else ''} of learning activity!")
                else:
                    last_active = sorted_active_dates[-1]
                    days_since = (today - last_active).days
                    st.warning(f"Your last learning activity was {days_since} day{'s' if days_since > 1 else ''} ago. Log in to keep your streak going!")
        else:
            st.info("Complete more learning activities to see your activity calendar.")
        
        # Import the function at the top of your file if not already imported
        from utils.language_model import generate_personalized_insights
        
        # Add personalized insights section
        st.subheader("Personalized Learning Insights")
        
        insights_container = st.container()
        if sessions:
            # Collect data for insights
            total_questions = sum(len(session.get('questions', [])) for session in sessions)
            total_answers = sum(len(session.get('answers', {})) for session in sessions)
            completion_rate = (total_answers / total_questions) if total_questions > 0 else 0
            avg_score = sum(session_scores) / len(session_scores) if session_scores else 0
            
            # Prepare user data for insights generation
            user_data = {
                'session_count': len(sessions),
                'total_questions': total_questions,
                'total_answers': total_answers,
                'completion_rate': completion_rate,
                'avg_score': avg_score,
                'recent_trend': "improving" if recent_avg > avg_score else "declining" if recent_avg < avg_score else "stable",
            }
            
            # Add additional data if available
            if 'most_active_weekday' in locals():
                user_data['most_active_day'] = most_active_weekday
            
            if 'streak' in locals():
                user_data['current_streak'] = streak
            
            if vocab_items:
                user_data['vocab_count'] = len(vocab_items)
                
                # Add vocab stats if available
                if 'recent_vocab' in locals():
                    user_data['recent_vocab'] = recent_vocab
                
                if 'never_reviewed' in locals():
                    user_data['never_reviewed'] = never_reviewed
            
            # Add dimension scores if available
            if 'sorted_dimensions' in locals() and sorted_dimensions:
                user_data['accuracy_score'] = next((d["score"] for d in sorted_dimensions if d["name"] == "Accuracy"), 0)
                user_data['completeness_score'] = next((d["score"] for d in sorted_dimensions if d["name"] == "Completeness"), 0)
                user_data['clarity_score'] = next((d["score"] for d in sorted_dimensions if d["name"] == "Clarity"), 0)
                user_data['language_score'] = next((d["score"] for d in sorted_dimensions if d["name"] == "Language Quality"), 0)
                user_data['strongest_dimension'] = sorted_dimensions[-1]["name"] if sorted_dimensions else "unknown"
                user_data['weakest_dimension'] = sorted_dimensions[0]["name"] if sorted_dimensions else "unknown"
            
            # Generate insights using OpenAI
            with st.spinner("Generating personalized insights..."):
                insights = generate_personalized_insights(user_data)
            
            if insights:
                # Display the API-generated insights
                with insights_container:
                    st.write(f"**Assessment:** {insights['assessment']}")
                    
                    # Display strengths and areas for improvement
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success("**Strengths:**")
                        for strength in insights['strengths']:
                            st.markdown(f"- ✅ {strength}")
                    
                    with col2:
                        st.info("**Areas for Improvement:**")
                        for area in insights['areas_for_improvement']:
                            st.markdown(f"- 🔍 {area}")
                    
                    # Display personalized recommendations
                    st.write("**Recommended Learning Activities:**")
                    for i, rec in enumerate(insights['recommendations']):
                        with st.expander(f"{i+1}. {rec['title']} ({rec['difficulty'].capitalize()})"):
                            st.write(rec['description'])
                    
                    # Display study routine suggestion
                    st.write("**Suggested Study Routine:**")
                    st.info(insights['study_routine'])
            else:
                # Fallback if API generation fails
                with insights_container:
                    st.info("Complete more learning sessions to receive personalized insights and recommendations.")
        else:
            with insights_container:
                st.info("Complete some learning sessions to receive personalized insights and recommendations.")


def vocabulary_notebook(db, user_id):
    """Show and manage vocabulary notebook"""
    st.header("Vocabulary Notebook")
    
    # Tabs for different vocabulary functions
    tab1, tab2, tab3 = st.tabs(["My Vocabulary", "Add New Word", "Words Due for Review"])
    
    with tab1:
        # Get user's vocabulary
        vocab_items = db.get_user_vocabulary(user_id)
        
        if not vocab_items:
            st.info("Your vocabulary notebook is empty. Add words to start learning!")
        else:
            # Display vocabulary items without using nested expanders
            for idx, item in enumerate(vocab_items):
                with st.container():
                    # Word header with add count if more than 1
                    add_count = item.get('add_count', 1)
                    add_count_display = f" (Added {add_count} times)" if add_count > 1 else ""
                    
                    # Display review information
                    review_count = item.get('review_count', 0)
                    last_review = item.get('last_review')
                    next_review = item.get('next_review')
                    
                    # Format header with word information
                    st.markdown(f"### {idx+1}. {item['word']}{add_count_display}")
                    
                    # Display definition and examples
                    st.write(f"**Definition:** {item['definition']}")
                    
                    st.write("**Examples:**")
                    for example in item['examples']:
                        st.write(f"- {example}")
                    
                    # Display review information in a colored box
                    review_info_col1, review_info_col2 = st.columns(2)
                    
                    with review_info_col1:
                        if review_count > 0:
                            st.info(f"**Reviewed:** {review_count} time{'s' if review_count > 1 else ''}")
                            if last_review:
                                st.info(f"**Last reviewed:** {last_review.strftime('%B %d, %Y at %I:%M %p')}")
                        else:
                            st.warning("**Not yet reviewed**")
                    
                    with review_info_col2:
                        if next_review:
                            if next_review <= datetime.now():
                                st.error(f"**Review due!** Was due on {next_review.strftime('%B %d, %Y')}")
                            else:
                                st.success(f"**Next review:** {next_review.strftime('%B %d, %Y')}")
                    
                    # Show source if available in a simple collapsible section (not an expander)
                    if item.get('source_passage'):
                        if st.checkbox(f"Show Source Passage for '{item['word']}'", key=f"source_{idx}"):
                            st.text_area("Source Passage", item['source_passage'], height=100, key=f"source_text_{idx}", disabled=True)
                    
                    # Add review button
                    if st.button(f"Mark as Reviewed", key=f"review_{idx}"):
                        # Update review count and dates in database using the new method
                        updated_item = db.mark_word_reviewed(user_id, item["_id"])
                        if updated_item:
                            review_count = updated_item.get("review_count", 0)
                            next_review_date = updated_item.get("next_review")
                            next_review_str = next_review_date.strftime('%B %d, %Y') if next_review_date else "Not scheduled"
                            
                            st.success(f"'{item['word']}' marked as reviewed! This word has been reviewed {review_count} times. Next review: {next_review_str}")
                            # Rerun to refresh the page with updated data
                            st.rerun()
                        else:
                            st.error(f"Error updating review status for '{item['word']}'")
                    
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
                
                # Check if the word already exists
                existing_vocab = db.vocabulary.find_one({
                    "user_id": user_id,
                    "word": word
                })
                
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
                        if existing_vocab:
                            # Word was updated, show appropriate message
                            add_count = result.get("add_count", 2)  # Should be at least 2 if it existed before
                            st.success(f"'{word}' already exists in your vocabulary notebook and has been updated. Added {add_count} times in total.")
                        else:
                            # New word was added
                            st.success(f"'{word}' added to your vocabulary notebook!")
                        
                        # Clear form
                        st.experimental_rerun()
                    else:
                        st.error("Failed to add word to notebook.")
                except Exception as e:
                    st.error(f"Error saving to database: {str(e)}")
    
    with tab3:
        # Get all vocabulary items for filtering
        all_vocab_items = db.get_user_vocabulary(user_id)
        
        # Add filtering controls
        st.subheader("Filter Words by Review Count")
        col1, col2 = st.columns(2)
        
        with col1:
            # Minimum reviews filter input
            min_reviews = st.number_input("Minimum Reviews", 
                                          min_value=0, 
                                          max_value=10, 
                                          value=0,
                                          step=1)
        
        with col2:
            # Find the maximum review count to set as upper limit
            max_possible = max([item.get('review_count', 0) for item in all_vocab_items]) if all_vocab_items else 10
            # Maximum reviews filter input
            max_reviews = st.number_input("Maximum Reviews", 
                                          min_value=0, 
                                          max_value=max_possible, 
                                          value=max_possible,
                                          step=1)
        
        # Option to show all words or only those due for review
        show_only_due = st.checkbox("Show only words due for review", value=True)
        
        # Apply filters
        if show_only_due:
            # Get words due for review and apply review count filter
            due_words = db.get_words_due_for_review(user_id)
            filtered_words = [item for item in due_words 
                              if min_reviews <= item.get('review_count', 0) <= max_reviews]
        else:
            # Apply review count filter to all words
            filtered_words = [item for item in all_vocab_items 
                              if min_reviews <= item.get('review_count', 0) <= max_reviews]
        
        # Display filtered results
        if not filtered_words:
            if show_only_due:
                st.success(f"You have no words with {min_reviews}-{max_reviews} reviews that are due for review.")
            else:
                st.info(f"You have no words with {min_reviews}-{max_reviews} reviews in your vocabulary.")
        else:
            st.write(f"Found {len(filtered_words)} word{'s' if len(filtered_words) > 1 else ''} matching your criteria.")
            
            # Add "Mark All Reviewed" button for batch operations
            if st.button("Mark All Filtered Words as Reviewed"):
                updated_count = 0
                for item in filtered_words:
                    updated_item = db.mark_word_reviewed(user_id, item["_id"])
                    if updated_item:
                        updated_count += 1
                
                if updated_count > 0:
                    st.success(f"Successfully marked {updated_count} word{'s' if updated_count > 1 else ''} as reviewed!")
                    st.rerun()
            
            # Display word list
            for idx, item in enumerate(filtered_words):
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Display word and review information
                        st.markdown(f"**{idx+1}. {item['word']}**")
                        review_count = item.get('review_count', 0)
                        st.info(f"Reviewed: {review_count} time{'s' if review_count > 1 else ''}")
                        
                        # Show last review date if available
                        if item.get('last_review'):
                            last_review_date = item['last_review'].strftime('%B %d, %Y')
                            st.info(f"Last reviewed: {last_review_date}")
                        else:
                            st.info("Not yet reviewed")
                        
                        # Show next review date with appropriate status color
                        if item.get('next_review'):
                            if item['next_review'] <= datetime.now():
                                st.error(f"Review due! Was due on {item['next_review'].strftime('%B %d, %Y')}")
                            else:
                                st.success(f"Next review: {item['next_review'].strftime('%B %d, %Y')}")
                    
                    with col2:
                        # Individual review button for each word
                        if st.button(f"Mark Reviewed", key=f"quick_review_{idx}"):
                            updated_item = db.mark_word_reviewed(user_id, item["_id"])
                            if updated_item:
                                st.success(f"'{item['word']}' marked as reviewed!")
                                st.rerun()
                            else:
                                st.error(f"Error updating review status for '{item['word']}'")
                    
                    # Expandable details section
                    if st.checkbox(f"Show details for '{item['word']}'", key=f"details_{idx}"):
                        st.write(f"**Definition:** {item['definition']}")
                        
                        st.write("**Examples:**")
                        for example in item['examples']:
                            st.write(f"- {example}")
                    
                    # Add separator between words
                    st.markdown("---")

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