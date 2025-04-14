"""
Language model utilities for the English learning app
"""
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

def generate_questions(passage, num_questions=3):
    """
    Generate reading comprehension questions based on the given passage
    
    Args:
        passage (str): The English passage to generate questions from
        num_questions (int): Number of questions to generate
        
    Returns:
        list: A list of generated questions
    """
    try:
        # Initialize the language model
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",  # You can use "gpt-4" if you have access
            temperature=0.7
        )
        
        # Create a prompt template for question generation
        prompt_template = PromptTemplate(
            input_variables=["passage", "num_questions"],
            template="""
            Based on the following English passage, generate {num_questions} reading comprehension questions.
            The questions should test the reader's understanding of the main ideas, details, and implications in the text.
            Only return the questions as a numbered list, with no additional text.
            
            Passage:
            {passage}
            """,
        )
        
        # Create and run the chain
        chain = LLMChain(llm=llm, prompt=prompt_template)
        result = chain.run(passage=passage, num_questions=num_questions)
        
        # Process the result into a list of questions
        questions = []
        for line in result.strip().split("\n"):
            # Remove numbering and clean the question
            cleaned_line = line.strip()
            # Check for common number formats (1., 1-, 1), etc.
            if cleaned_line and (cleaned_line[0].isdigit() or cleaned_line[0] == "#"):
                # Find the position after the number and any separators
                for i, char in enumerate(cleaned_line):
                    if i > 0 and (char.isalpha() or char == '"'):
                        cleaned_line = cleaned_line[i:].strip()
                        break
            
            if cleaned_line:
                questions.append(cleaned_line)
        
        # Ensure we only return the requested number of questions
        return questions[:num_questions]
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error generating questions: {str(e)}")
        raise e

def analyze_answer(question, user_answer, reference_passage):
    """
    Analyze a user's answer to a reading comprehension question with a scoring system
    
    Args:
        question (str): The question being answered
        user_answer (str): The user's answer to analyze
        reference_passage (str): The original passage for context
        
    Returns:
        dict: Structured feedback with scores and feedback text
    """
    try:
        # Special case for debugging or testing phrases
        if user_answer.strip().lower() in ["update scoring rubric", "test score system", "test", "testing"]:
            # Return a very low score for testing phrases
            feedback_data = {
                "accuracy_score": 0,
                "accuracy_feedback": "This appears to be a test phrase, not a genuine answer to the question. An actual answer should discuss how technology has impacted education based on the passage.",
                "completeness_score": 0,
                "completeness_feedback": "The answer does not address any aspects of the question.",
                "clarity_score": 0,
                "clarity_feedback": "This is not a proper answer to the question.",
                "language_score": 1,
                "language_feedback": "While grammatically correct, this is not an appropriate response to the question.",
                "suggestions": "Please provide a real answer that discusses how technology has revolutionized education as described in the passage.",
                "improved_answer": "Technology has revolutionized education through the introduction of computers in classrooms, the widespread use of the internet for accessing information, tools for global collaboration, and interactive learning platforms.",
                "total_score": 1
            }
            
            # Format the feedback text
            formatted_feedback = f"""**Accuracy ({feedback_data['accuracy_score']}/4)**: {feedback_data['accuracy_feedback']}

**Completeness ({feedback_data['completeness_score']}/2)**: {feedback_data['completeness_feedback']}

**Clarity ({feedback_data['clarity_score']}/1)**: {feedback_data['clarity_feedback']}

**Language Quality ({feedback_data['language_score']}/3)**: {feedback_data['language_feedback']}

**Suggestions**: {feedback_data['suggestions']}

**Improved Answer**: {feedback_data['improved_answer']}

**Total Score: {feedback_data['total_score']}/10**
"""
            return {
                "formatted_feedback": formatted_feedback,
                "data": feedback_data
            }
        
        # Check if answer is too short (less than 15 characters)
        if len(user_answer.strip()) < 15:
            # Return a low score for very short answers
            feedback_data = {
                "accuracy_score": 0,
                "accuracy_feedback": "The answer is too brief to accurately address the question.",
                "completeness_score": 0,
                "completeness_feedback": "The answer is too short to cover any aspects of the question.",
                "clarity_score": 0,
                "clarity_feedback": "The answer is too brief to evaluate clarity.",
                "language_score": 1 if user_answer.strip() else 0,
                "language_feedback": "The answer is too short to properly evaluate language quality.",
                "suggestions": "Please provide a complete answer that addresses the question about how technology has impacted education over the past few decades.",
                "improved_answer": "Technology has revolutionized education through the introduction of computers in classrooms, the widespread use of the internet for accessing information, tools for global collaboration, and interactive learning platforms.",
                "total_score": 1 if user_answer.strip() else 0
            }
            
            # Format the feedback text
            formatted_feedback = f"""**Accuracy ({feedback_data['accuracy_score']}/4)**: {feedback_data['accuracy_feedback']}

**Completeness ({feedback_data['completeness_score']}/2)**: {feedback_data['completeness_feedback']}

**Clarity ({feedback_data['clarity_score']}/1)**: {feedback_data['clarity_feedback']}

**Language Quality ({feedback_data['language_score']}/3)**: {feedback_data['language_feedback']}

**Suggestions**: {feedback_data['suggestions']}

**Improved Answer**: {feedback_data['improved_answer']}

**Total Score: {feedback_data['total_score']}/10**
"""
            return {
                "formatted_feedback": formatted_feedback,
                "data": feedback_data
            }
        
        # Initialize the language model with a higher temperature for more critical evaluation
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.2  # Lower temperature for more consistent analysis
        )
        
        # Create a prompt template for answer analysis with scoring
        prompt_template = PromptTemplate(
            input_variables=["passage", "question", "answer"],
            template="""
            You are a critical and strict English teacher grading a reading comprehension answer. 
            You should be highly critical and never give perfect or near-perfect scores unless the answer is truly exceptional.
            
            Passage:
            {passage}
            
            Question:
            {question}
            
            Student's Answer:
            {answer}
            
            Evaluate the answer strictly according to these criteria:
            
            1. Accuracy (0-4 points): 
               - Give 0 points if the answer shows no understanding of the passage or is completely wrong
               - Give 1 point if the answer has only minimal connection to the passage
               - Give 2 points if the answer has some correct elements but significant inaccuracies
               - Give 3 points if the answer is mostly accurate with minor errors
               - Only give 4 points if the answer is completely accurate and demonstrates thorough understanding
            
            2. Completeness (0-2 points):
               - Give 0 points if the answer fails to address the main aspects of the question
               - Give 1 point if the answer addresses some aspects but misses important elements
               - Only give 2 points if the answer comprehensively addresses all aspects of the question
            
            3. Clarity (0-1 point):
               - Give 0 points if the answer is confusing, poorly structured, or hard to follow
               - Only give 1 point if the answer is clear, well-organized, and easy to understand
            
            4. Language Quality (0-3 points):
               - Give 0 points if there are severe grammar/spelling errors making it difficult to understand
               - Give 1 point if there are multiple grammar/spelling errors but the meaning is still clear
               - Give 2 points if there are a few minor grammar/spelling errors
               - Only give 3 points if the grammar, spelling, and word choice are nearly perfect
            
            If the answer appears to be nonsensical, testing text, or completely unrelated to the question, give the lowest possible scores in most categories.
            
            For the Language Quality feedback, be extremely detailed and specific:
            1. Identify EACH spelling error with the incorrect word and the correct spelling
            2. Point out EACH grammar mistake with a brief explanation of the rule being broken
            3. Highlight any issues with word choice, suggesting better alternatives
            4. For run-on sentences or fragments, explain how to correct them
            5. Organize these corrections as a list if there are multiple issues
            
            Format your response as a JSON structure with the following format:
            {{
                "accuracy_score": score (integer between 0 and 4),
                "accuracy_feedback": "Your detailed feedback on accuracy",
                "completeness_score": score (integer between 0 and 2),
                "completeness_feedback": "Your detailed feedback on completeness",
                "clarity_score": score (integer between 0 and 1),
                "clarity_feedback": "Your detailed feedback on clarity",
                "language_score": score (integer between 0 and 3),
                "language_feedback": "Your detailed feedback on language quality, identifying each error specifically",
                "spelling_errors": ["Error 1: incorrect → correct", "Error 2: incorrect → correct"],
                "grammar_errors": ["Error 1: description and correction", "Error 2: description and correction"],
                "suggestions": "Specific suggestions for improvement",
                "improved_answer": "A model answer for reference",
                "total_score": sum of all scores (integer between 0 and 10)
            }}
            
            Be very strict with your scoring and do not inflate scores. Most answers should not receive perfect or near-perfect scores.
            Only return the JSON object, no other text.
            """,
        )
        
        # Create and run the chain
        chain = LLMChain(llm=llm, prompt=prompt_template)
        result = chain.run(
            passage=reference_passage,
            question=question,
            answer=user_answer
        )
        
        # Parse the result as JSON
        try:
            # Clean the result to ensure it's valid JSON
            cleaned_result = result.strip()
            if cleaned_result.startswith('```json'):
                cleaned_result = cleaned_result[7:]
            if cleaned_result.endswith('```'):
                cleaned_result = cleaned_result[:-3]
            cleaned_result = cleaned_result.strip()
            
            # Parse JSON
            feedback_data = json.loads(cleaned_result)
            
            # Verify that scores are within expected ranges
            feedback_data["accuracy_score"] = max(0, min(4, feedback_data.get("accuracy_score", 0)))
            feedback_data["completeness_score"] = max(0, min(2, feedback_data.get("completeness_score", 0)))
            feedback_data["clarity_score"] = max(0, min(1, feedback_data.get("clarity_score", 0)))
            feedback_data["language_score"] = max(0, min(3, feedback_data.get("language_score", 0)))
            
            # Calculate total score based on individual scores (don't trust provided total)
            feedback_data["total_score"] = (
                feedback_data["accuracy_score"] + 
                feedback_data["completeness_score"] + 
                feedback_data["clarity_score"] + 
                feedback_data["language_score"]
            )
            
            # Enhance language quality feedback with specific errors if they exist
            language_feedback = feedback_data["language_feedback"]
            
            # Add spelling errors if present
            if "spelling_errors" in feedback_data and feedback_data["spelling_errors"]:
                language_feedback += "\n\n**Spelling errors:**"
                for error in feedback_data["spelling_errors"]:
                    language_feedback += f"\n- {error}"
            
            # Add grammar errors if present
            if "grammar_errors" in feedback_data and feedback_data["grammar_errors"]:
                language_feedback += "\n\n**Grammar errors:**"
                for error in feedback_data["grammar_errors"]:
                    language_feedback += f"\n- {error}"
            
            # Update the language feedback in the data
            feedback_data["language_feedback"] = language_feedback
            
            # Format the feedback text
            formatted_feedback = f"""**Accuracy ({feedback_data['accuracy_score']}/4)**: {feedback_data['accuracy_feedback']}

**Completeness ({feedback_data['completeness_score']}/2)**: {feedback_data['completeness_feedback']}

**Clarity ({feedback_data['clarity_score']}/1)**: {feedback_data['clarity_feedback']}

**Language Quality ({feedback_data['language_score']}/3)**: {feedback_data['language_feedback']}

**Suggestions**: {feedback_data['suggestions']}

**Improved Answer**: {feedback_data['improved_answer']}

**Total Score: {feedback_data['total_score']}/10**
"""
            
            # Return both the formatted feedback text and the raw data
            return {
                "formatted_feedback": formatted_feedback,
                "data": feedback_data
            }
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return the raw text
            print(f"Error parsing feedback JSON: {e}")
            return {
                "formatted_feedback": result,
                "data": {
                    "total_score": 0,
                    "error": "Could not parse feedback"
                }
            }
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error analyzing answer: {str(e)}")
        raise e

def get_word_definition(word):
    """
    Get definition and usage examples for a word using OpenAI
    
    Args:
        word (str): The word to define
        
    Returns:
        dict: Dictionary with definition and examples
    """
    try:
        # Initialize the language model
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.3
        )
        
        # Create a prompt template for word definition
        prompt_template = PromptTemplate(
            input_variables=["word"],
            template="""
            Please provide the definition and usage examples for the English word "{word}".
            Include the part of speech, a clear definition, and 3 example sentences.
            
            Format your response as a JSON with the following structure:
            {{
                "definition": "part_of_speech: the meaning of the word",
                "examples": ["example sentence 1", "example sentence 2", "example sentence 3"]
            }}
            
            Return only the JSON, no other text.
            """,
        )
        
        # Create and run the chain
        chain = LLMChain(llm=llm, prompt=prompt_template)
        result = chain.run(word=word)
        
        # Parse the result as a dictionary (it should be in JSON format)
        # This is a simple way to convert the string to a dict, assumes well-formed output
        import json
        try:
            # Clean the result to ensure it's valid JSON
            cleaned_result = result.strip()
            if cleaned_result.startswith('```json'):
                cleaned_result = cleaned_result[7:]
            if cleaned_result.endswith('```'):
                cleaned_result = cleaned_result[:-3]
            cleaned_result = cleaned_result.strip()
            
            return json.loads(cleaned_result)
        except json.JSONDecodeError:
            # Fallback to a simple parsing if JSON parsing fails
            lines = result.strip().split('\n')
            definition = ""
            examples = []
            
            for line in lines:
                if line.startswith('"definition"'):
                    definition = line.split(':', 1)[1].strip().strip('"').strip(',')
                elif '"examples"' in line:
                    continue
                elif line.strip().startswith('"') and line.strip().endswith('"'):
                    examples.append(line.strip().strip('"').strip(','))
            
            return {
                "definition": definition,
                "examples": examples
            }
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error getting word definition: {str(e)}")
        return None