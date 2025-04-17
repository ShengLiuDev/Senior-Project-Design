import os
import sys
import json
import requests
import pandas as pd
import random
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL, OPENROUTER_MODEL
from typing import Dict, List, Any

class AnswerAnalyzer:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.api_url = OPENROUTER_API_URL
        self.model = OPENROUTER_MODEL
        self.answer_sheet = self._load_answer_sheet()

    def _load_answer_sheet(self) -> pd.DataFrame:
        """Load the HireVue answer sheet from CSV"""
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
        # Get all questions from the answer sheet
        all_questions = self.answer_sheet['BEHAVIORAL_QUESTIONS'].tolist()
        
        # Create a dictionary to track first words
        first_words = {}
        selected_questions = []
        
        # Shuffle the questions to ensure randomness
        random.shuffle(all_questions)
        
        for question in all_questions:
            # Get the first word of the question
            first_word = question.split()[0].lower()
            
            # If we haven't seen this first word before and we haven't selected enough questions
            if first_word not in first_words and len(selected_questions) < num_questions:
                selected_questions.append(question)
                first_words[first_word] = True
                
            # If we've selected enough questions, break the loop
            if len(selected_questions) >= num_questions:
                break
        
        # If we couldn't find enough unique questions, add remaining questions
        if len(selected_questions) < num_questions:
            remaining_questions = [q for q in all_questions if q not in selected_questions]
            selected_questions.extend(remaining_questions[:num_questions - len(selected_questions)])
        
        return selected_questions

    def _get_reference_answers(self, question: str) -> Dict[str, str]:
        """Get reference positive and negative answers for a given question"""
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
        # Get reference answers
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
            "score": <number between 1.0-10.0>,\n
            "strengths": ["strength1", "strength2", ...],\n
            "improvements": ["improvement1", "improvement2", ...],\n
            "suggestions": ["suggestion1", "suggestion2", ...],\n
            "competencies": ["competency1", "competency2", ...]\n
        }}
        
        Focus on:
        1. How well the answer matches the quality of the good answer
        2. Key strengths in their response
        3. Areas for improvement
        4. Specific suggestions for improvement
        5. Key competencies demonstrated
        
        NOTE: if a users answer encompasses a majority of a good answer they should
        be scoring higher than a 6.0 to 7.0, hovering around 8.0 to 9.0. However, if the user
        provides a response that is not very relevant to the question, they should
        score lower than a 4.0.
        
        Additional Note: If a user's answer is in STAR format, give additional points for the STAR format. 
        Else deduct points for not using the STAR format.
        """
        
        # Make the API request
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
            print("\nMaking API request...")
            print(f"API URL: {self.api_url}")
            print(f"Model: {self.model}")
            print(f"Headers: {headers}")
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            print(f"\nResponse status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            
            # Check for error responses
            if response.status_code != 200:
                error_response = response.json()
                print(f"\nError response: {error_response}")
                return {
                    "error": "API request failed",
                    "status_code": response.status_code,
                    "details": error_response.get("error", {}).get("message", "Unknown error")
                }
            
            # Parse the response
            result = response.json()
            print("\nAPI Response received")
            print(f"Response content: {result}")
            
            if 'choices' not in result or not result['choices']:
                raise ValueError("Invalid API response format: missing choices")
                
            content = result['choices'][0]['message']['content']
            print("\nParsing content...")
            print(f"Raw content: {content}")
            
            # Try to find JSON in the content
            try:
                # Find the first { and last } to extract JSON
                start = content.find('{')
                end = content.rfind('}') + 1
                if start == -1 or end == 0:
                    raise ValueError("No JSON object found in response")
                    
                json_str = content[start:end]
                print(f"\nExtracted JSON string: {json_str}")
                analysis = json.loads(json_str)
                
                # User feedback will be given here
                return {
                    "score": analysis.get("score", 0),
                    "strengths": analysis.get("strengths", []),
                    "improvements": analysis.get("improvements", []),
                    "suggestions": analysis.get("suggestions", []),
                    "competencies": analysis.get("competencies", []),
                    "reference_positive": reference_answers['positive'],
                    "reference_negative": reference_answers['negative']
                }
                
            except json.JSONDecodeError as e:
                print(f"\nError parsing JSON: {str(e)}")
                print(f"Content received: {content}")
                return {
                    "error": "Failed to parse analysis",
                    "details": str(e),
                    "raw_content": content
                }
            
        except requests.exceptions.RequestException as e:
            print(f"\nError making API request: {str(e)}")
            return {
                "error": "Failed to analyze answer",
                "details": str(e)
            }
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            return {
                "error": "Unexpected error occurred",
                "details": str(e)
            }

    def analyze_qa_pairs(self, qa_pairs: Dict) -> List[Dict]:
        """
        Analyze multiple Q&A pairs
        """
        analyses = []
        for question_id, pair in qa_pairs.items():
            analysis = self.analyze_answer(pair["question"], pair["answer"])
            analyses.append(analysis)
        return analyses 