import requests
import json
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL, DEEPSEEK_MODEL
from typing import Dict, List

class AnswerAnalyzer:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.api_url = OPENROUTER_API_URL
        self.model = DEEPSEEK_MODEL

    def analyze_answer(self, question, answer):
        """
        Analyze an answer using the DeepSeek model
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ShengLiuDev/Senior-Project-Design",
            "X-Title": "HireLens"
        }

        prompt = f"""
        Question: {question}
        Answer: {answer}

        Please analyze this answer and provide:
        1. Content Quality (1-10)
        2. Clarity (1-10)
        3. Relevance (1-10)
        4. Specific Examples (Yes/No)
        5. Overall Score (1-10)
        6. Key Strengths
        7. Areas for Improvement
        8. Suggested Follow-up Questions
        """

        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            return f"Error analyzing answer: {str(e)}"
    
    def analyze_qa_pairs(self, qa_pairs: Dict) -> List[Dict]:
        """
        Analyze multiple Q&A pairs
        """
        analyses = []
        for question_id, pair in qa_pairs.items():
            analysis = self.analyze_answer(pair["question"], pair["answer"])
            analyses.append(analysis)
        return analyses 