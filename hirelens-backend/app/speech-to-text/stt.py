from RealtimeSTT import AudioToTextRecorder
from sheets_api import get_static_sheet_data
from ..answer_analysis.analyzer import AnswerAnalyzer
import random

class speech_to_text:
    def __init__(self):
        self.recorder = AudioToTextRecorder()
        self.qa_pairs = {}  # dictionary to store question-answer pairs
        self.questions = []  # list to store available questions
        self.analyzer = AnswerAnalyzer()
        
    def load_questions_from_sheet(self):
        """Load questions from Google Sheets"""
        response, status_code = get_static_sheet_data()
        if status_code == 200 and "data" in response:
            # assuming questions are in the first column of the sheet
            self.questions = [row[0] for row in response["data"]]
            return True
        return False
    
    def get_random_questions(self, num_questions=4):
        """Get random questions from the question bank"""
        if not self.questions:
            if not self.load_questions_from_sheet():
                raise ValueError("Failed to load questions from sheet")
        
        if num_questions > len(self.questions):
            num_questions = len(self.questions)
            
        return random.sample(self.questions, num_questions)
        
    def record_question(self, question_id):
        # records and stores a question
        print("Recording question...")
        self.recorder.start()
        input("Press Enter when done speaking the question...")
        self.recorder.stop()
        question_text = self.recorder.text()
        self.qa_pairs[question_id] = {"question": question_text, "answer": None}
        return question_text
    
    def record_answer(self, question_id):
        # record and store an answer for a given question
        if question_id not in self.qa_pairs:
            raise ValueError("Question ID not found. Please record the question first.")
            
        print("Recording answer...")
        self.recorder.start()
        input("Press Enter when done speaking the answer...")
        self.recorder.stop()
        answer_text = self.recorder.text()
        self.qa_pairs[question_id]["answer"] = answer_text
        return answer_text
    
    def get_qa_pairs(self):
        # return all recorded Q&A pairs
        return self.qa_pairs
    
    def get_qa_pair(self, question_id):
        # return a specific Q&A pair by question ID
        if question_id not in self.qa_pairs:
            raise ValueError("Question ID not found")
        return self.qa_pairs[question_id]
    
    def analyze_answers(self):
        """ analyze all recorded answers w/ respective questions using DeepSeek V3 """
        if not self.qa_pairs:
            raise ValueError("No Q&A pairs to analyze")
        return self.analyzer.analyze_qa_pairs(self.qa_pairs)

if __name__ == '__main__':
    # sample
    stt = speech_to_text()
    
    # get random questions from the sheet
    try:
        random_questions = stt.get_random_questions(4)
        print("Selected questions:", random_questions)
        
        # record Q&A for each question
        for question in random_questions:
            print(f"\nRecording response for: {question}")
            question_id = question
            answer = stt.record_answer(question_id)
            print(f"Answer recorded: {answer}")
        
        # get all Q&A pairs
        all_pairs = stt.get_qa_pairs()
        print("\nAll Q&A pairs:", all_pairs)
        
        # analyze the answers
        print("\nAnalyzing answers...")
        analyses = stt.analyze_answers()
        for analysis in analyses:
            print(f"\nAnalysis for: {analysis['question']}")
            print(analysis['analysis'])
        
    except Exception as e:
        print(f"Error: {e}")