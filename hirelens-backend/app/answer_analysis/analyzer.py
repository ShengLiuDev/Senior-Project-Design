import os
import sys
import json
import requests
import pandas as pd
import secrets  # Import secrets module for secure random operations
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL, OPENROUTER_MODEL
from typing import Dict, List, Any

class AnswerAnalyzer:
    # Main class for analyzing interview answers using AI
    def __init__(self):
        # Initialize with API credentials and load the interview dataset
        self.api_key = OPENROUTER_API_KEY
        self.api_url = OPENROUTER_API_URL
        self.model = OPENROUTER_MODEL
        self.answer_sheet = self._load_answer_sheet()

    def _load_answer_sheet(self) -> pd.DataFrame:
        """Load the HireVue answer sheet from CSV"""
        # Load interview questions and sample answers from CSV file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        answer_sheet_path = os.path.join(current_dir, '..', 'dataset', 'hirevue-answer-sheet.csv')
        return pd.read_csv(answer_sheet_path)

    def get_random_questions(self, num_questions: int = 3) -> List[str]:
        """
        Select random questions from the answer sheet, ensuring no two questions
        start with the same word.
        
        Args:
            num_questions: Number of questions to select (default: 3)
            
        Returns:
            List of randomly selected questions
        """
        # Select diverse interview questions using secure randomization
        all_questions = self.answer_sheet['BEHAVIORAL_QUESTIONS'].tolist()
        
        # Create a dictionary to track first words
        first_words = {}
        selected_questions = []
        
        # Using Fisher-Yates shuffle with secrets module for secure randomization
        questions = all_questions.copy()
        for i in range(len(questions) - 1, 0, -1):
            # Use secrets.randbelow for secure random index selection
            j = secrets.randbelow(i + 1)
            questions[i], questions[j] = questions[j], questions[i]
        
        # Select questions ensuring no two start with the same word
        for question in questions:
            if len(selected_questions) >= num_questions:
                break
                
            first_word = question.split()[0].lower()
            if first_word not in first_words:
                selected_questions.append(question)
                first_words[first_word] = True
        
        # If we couldn't find enough unique questions, add remaining questions
        if len(selected_questions) < num_questions:
            remaining_questions = [q for q in questions if q not in selected_questions]
            selected_questions.extend(remaining_questions[:num_questions - len(selected_questions)])
        
        return selected_questions

    def _get_reference_answers(self, question: str) -> Dict[str, str]:
        """Get reference positive and negative answers for a given question"""
        # Retrieve sample good/bad answers for a specific question
        matching_row = self.answer_sheet[self.answer_sheet['BEHAVIORAL_QUESTIONS'] == question]
        if matching_row.empty:
            return {"positive": "", "negative": ""}
        return {
            "positive": matching_row['SAMPLE_POSITIVE_ANSWERS'].iloc[0],
            "negative": matching_row['SAMPLE_NEGATIVE_ANSWERS'].iloc[0]
        }

    def analyze_answer(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Analyze the answer using the HireVue answer sheet as reference
        """
        # Core function: Analyzes candidate's answer using AI
        reference_answers = self._get_reference_answers(question)
        
        # Prepare the prompt for the model
        prompt = f"""
        You are an expert interviewer analyzing a candidate's response to a behavioral interview question.
        The question is: "{question}"
        
        Here are reference examples of good and poor answers:
        Good answer: "{reference_answers['positive']}"
        Poor answer: "{reference_answers['negative']}"
        
        The candidate's answer is: "{answer}"
        
        Please analyze the candidate's answer and provide a JSON response with the following structure:
        {{
            "score": <number between 1.0-100.0>,\n
            "strengths": ["specific strength1", "specific strength2", ...],\n
            "weaknesses": ["specific weakness1", "specific weakness2", ...],\n
            "improvements": ["improvement1", "improvement2", ...],\n
            "suggestions": ["suggestion1", "suggestion2", ...],\n
            "competencies": ["competency1", "competency2", ...]\n
        }}
        
        Focus on:
        1. How well the answer matches the quality of the good answer
        2. SPECIFIC strengths in their response (be detailed, not generic)
        3. SPECIFIC weaknesses in their response (be detailed, not generic)
        4. Areas for improvement
        5. Specific suggestions for improvement
        6. Key competencies demonstrated
        
        NOTE: if a users answer encompasses a majority of a good answer they should be scoring higher than 60.0 to 70.0, hovering around 80.0 to 90.0 it should be a very specific score users get. However, if the user provides a response that is not very relevant to the question, they should score lower than 40.0.
        
        The score must be on a scale of 1.0-100.0, not 1.0-10.0.
        
        Also when you give them a score, make sure you give them a percentage score that is like 87.4% for example. You can nitpick and say that the user could have done better and deduct say 1.4%, but the score should be a percentage score.
        
        Additional Note: If a user's answer is in STAR format, give additional points for the STAR format. Else deduct points as neededfor not using the STAR format.
        
        IMPORTANT: Be SUPER SPECIFIC in your analysis of strengths and weaknesses. Avoid generic statements like "Good communication skills" and instead provide detailed observations like "Effectively articulated how they resolved a conflict by using active listening and compromise." Also feedback can be longer if needed. 
        """
        
        # Setup API request parameters
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:3000",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            # Send request to OpenRouter API
            print("\nMaking API request...")
            print(f"API URL: {self.api_url}")
            print(f"Model: {self.model}")
            print(f"Headers: {headers}")
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            print(f"\nResponse status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            
            # Handle error responses
            if response.status_code != 200:
                error_response = response.json()
                print(f"\nError response: {error_response}")
                return {
                    "error": "API request failed",
                    "status_code": response.status_code,
                    "details": error_response.get("error", {}).get("message", "Unknown error")
                }
            
            # Process successful API response
            result = response.json()
            print("\nAPI Response received")
            print(f"Response content: {result}")
            
            if 'choices' not in result or not result['choices']:
                raise ValueError("Invalid API response format: missing choices")
                
            content = result['choices'][0]['message']['content']
            print("\nParsing content...")
            print(f"Raw content: {content}")
            
            # Extract and parse JSON from AI response
            try:
                # Find the first { and last } to extract JSON
                start = content.find('{')
                end = content.rfind('}') + 1
                if start == -1 or end == 0:
                    raise ValueError("No JSON object found in response")
                    
                json_str = content[start:end]
                print(f"\nExtracted JSON string: {json_str}")
                analysis = json.loads(json_str)
                
                # Format final response with analysis results
                return {
                    "score": analysis.get("score", 0),
                    "strengths": analysis.get("strengths", []),
                    "weaknesses": analysis.get("weaknesses", []),
                    "improvements": analysis.get("improvements", []),
                    "suggestions": analysis.get("suggestions", []),
                    "competencies": analysis.get("competencies", []),
                    "reference_positive": reference_answers['positive'],
                    "reference_negative": reference_answers['negative']
                }
                
            except json.JSONDecodeError as e:
                # Handle JSON parsing errors
                print(f"\nError parsing JSON: {str(e)}")
                print(f"Content received: {content}")
                return {
                    "error": "Failed to parse analysis",
                    "details": str(e),
                    "raw_content": content
                }
            
        except requests.exceptions.RequestException as e:
            # Handle network or API request errors
            print(f"\nError making API request: {str(e)}")
            return {
                "error": "Failed to analyze answer",
                "details": str(e)
            }
        except Exception as e:
            # Catch any other unexpected errors
            print(f"\nUnexpected error: {str(e)}")
            return {
                "error": "Unexpected error occurred",
                "details": str(e)
            }

    def analyze_qa_pairs(self, qa_pairs: Dict) -> List[Dict]:
        """
        Analyze multiple Q&A pairs
        """
        # Batch process multiple question-answer pairs at once
        analyses = []
        for question_id, pair in qa_pairs.items():
            analysis = self.analyze_answer(pair["question"], pair["answer"])
            analyses.append(analysis)
        return analyses 