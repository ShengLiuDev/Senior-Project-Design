import requests
from typing import Dict, List
from ..config import OPENROUTER_API_KEY, OPENROUTER_API_URL, DEEPSEEK_MODEL

class AnswerAnalyzer:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ShengLiuDev/Senior-Project-Design", 
        }
    
    def analyze_answer(self, question: str, answer: str) -> Dict:
        """
        Analyze a single Q&A pair using DeepSeek model
        """
        prompt = f"""Analyze the following interview Q&A pair and provide feedback on:
        1. Relevance of the answer to the question
        2. Clarity and structure of the response
        3. Technical accuracy (if applicable)
        4. Areas for improvement

        Question: {question}
        Answer: {answer}

        Please provide a structured analysis.
        """

        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert interview analyst providing detailed feedback on interview responses. You are also an expert in the field of finance and investment banking. Additionally, you are to review the answers and rate them on a scale of 1-10. Do not by hyper critical, but provide meaningful feedback that will help the candidate improve their skills. Make sure to highlight the areas they are strong in and the areas they are weak in. Make sure to be very specific and detailed in your feedback."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        try:
            response = requests.post(OPENROUTER_API_URL, headers=self.headers, json=payload)
            response.raise_for_status()
            analysis = response.json()
            return {
                "question": question,
                "answer": answer,
                "analysis": analysis["choices"][0]["message"]["content"]
            }
        except requests.exceptions.RequestException as e:
            return {
                "question": question,
                "answer": answer,
                "error": f"Analysis failed: {str(e)}"
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