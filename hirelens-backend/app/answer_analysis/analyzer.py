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
            # "HTTP-Referer": "https://github.com/ShengLiuDev/Senior-Project-Design",
        """
        The HTTP-Referer header is used to specify the referrer URL of the page that linked to the resource.
        This is used to track the source of the request and to prevent abuse. When we go to production, 
        we can remove this header. For now, we are using localhost for development.
        """
            "HTTP-Referer": "http://localhost:3000",  # Using localhost for development
            "X-Title": "HireLens"
        }

        prompt = f"""
        Question: {question}
        Answer: {answer}

        Please analyze this answer and provide:
        1. Content Quality (1.0-10.0)
        2. Clarity (1.0-10.0)
        3. Relevance (1.0-10.0)
        4. Specific Examples (Yes/No)
        5. Overall Score (1.0-10.0)
        6. Key Strengths
        7. Areas for Improvement
        8. Suggested Follow-up Questions
        """

        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        try:
            print("\nDebugging API Request:")
            print(f"API URL: {self.api_url}")
            print(f"Model: {self.model}")
            print(f"Headers: {headers}")
            print(f"Request data: {json.dumps(data, indent=2)}")
            print("Sending request to OpenRouter API...")
            
            # Add timeout to prevent infinite waiting
            response = requests.post(
                self.api_url, 
                headers=headers, 
                json=data,
                timeout=30  # 30 second timeout
            )
            
            # Print response status and content for debugging
            print(f"\nResponse status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response content type: {response.headers.get('content-type', 'unknown')}")
            print(f"Response content preview: {response.text[:500]}...")
            
            if response.status_code != 200:
                return f"API Error: {response.status_code} - {response.text}"
            
            # Check if response is HTML
            if 'text/html' in response.headers.get('content-type', '').lower():
                return "Error: Received HTML response instead of JSON. This usually means the API key is invalid or the endpoint is incorrect."
                
            # Try to parse the response
            try:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    return "Error: Unexpected API response format"
            except json.JSONDecodeError as e:
                return f"Error parsing API response: {str(e)}"
                
        except requests.exceptions.Timeout:
            return "Error: Request timed out after 30 seconds"
        except requests.exceptions.RequestException as e:
            return f"Request Error: {str(e)}"
        except Exception as e:
            return f"Unexpected Error: {str(e)}"
    
    def analyze_qa_pairs(self, qa_pairs: Dict) -> List[Dict]:
        """
        Analyze multiple Q&A pairs
        """
        analyses = []
        for question_id, pair in qa_pairs.items():
            analysis = self.analyze_answer(pair["question"], pair["answer"])
            analyses.append(analysis)
        return analyses 