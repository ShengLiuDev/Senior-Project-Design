from RealtimeSTT import AudioToTextRecorder

class speech_to_text:
    def __init__(self):
        self.recorder = AudioToTextRecorder()
        self.qa_pairs = {}  # cictionary to store question-answer pairs
        
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

if __name__ == '__main__':
    # Example usage
    stt = speech_to_text()
    
    # Record a question
    question_id = "q1"
    question = stt.record_question(question_id)
    print(f"Question recorded: {question}")
    
    # Record an answer
    answer = stt.record_answer(question_id)
    print(f"Answer recorded: {answer}")
    
    # Get all Q&A pairs
    all_pairs = stt.get_qa_pairs()
    print("All Q&A pairs:", all_pairs)