import os
import sys
import json
import requests
import pandas as pd
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
        
        Please analyze the candidate's answer and provide:
        1. A score from 1-10 based on how well it matches the quality of the good answer
        2. Key strengths in their response
        3. Areas for improvement
        4. Specific suggestions for how they could improve their answer
        5. Whether their answer demonstrates the key competencies expected for this question
        
        Format your response as a JSON object with these keys:
        - score (number)
        - strengths (array of strings)
        - improvements (array of strings)
        - suggestions (array of strings)
        - competencies (array of strings)
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
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            analysis = json.loads(result['choices'][0]['message']['content'])
            
            return {
                "score": analysis.get("score", 0),
                "strengths": analysis.get("strengths", []),
                "improvements": analysis.get("improvements", []),
                "suggestions": analysis.get("suggestions", []),
                "competencies": analysis.get("competencies", []),
                "reference_positive": reference_answers['positive'],
                "reference_negative": reference_answers['negative']
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {str(e)}")
            return {
                "error": "Failed to analyze answer",
                "details": str(e)
            }
        except json.JSONDecodeError as e:
            print(f"Error parsing API response: {str(e)}")
            return {
                "error": "Invalid response format",
                "details": str(e)
            }
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
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