"""
Language model utilities for the English learning app
"""
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os

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
    Analyze a user's answer to a reading comprehension question
    
    Args:
        question (str): The question being answered
        user_answer (str): The user's answer to analyze
        reference_passage (str): The original passage for context
        
    Returns:
        str: Formatted feedback on the answer
    """
    try:
        # Initialize the language model
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.3  # Lower temperature for more consistent analysis
        )
        
        # Create a prompt template for answer analysis
        prompt_template = PromptTemplate(
            input_variables=["passage", "question", "answer"],
            template="""
            As an English language tutor, analyze the following answer to a reading comprehension question.
            
            Passage:
            {passage}
            
            Question:
            {question}
            
            Student's Answer:
            {answer}
            
            Please analyze the answer and provide feedback on:
            1. Content accuracy: Is the answer correct based on the passage?
            2. Grammar and expression: Identify any grammatical errors or awkward expressions.
            3. Improvement suggestions: How could the answer be improved?
            
            Format your response as follows:
            Content: [Your assessment of the content accuracy]
            Grammar: [Your assessment of grammar and expression]
            Suggestions: [Your suggestions for improvement]
            Improved Answer: [A model answer for reference]
            """,
        )
        
        # Create and run the chain
        chain = LLMChain(llm=llm, prompt=prompt_template)
        result = chain.run(
            passage=reference_passage,
            question=question,
            answer=user_answer
        )
        
        return result
        
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