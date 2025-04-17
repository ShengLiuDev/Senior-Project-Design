import pandas as pd

class csv_read_in_functions:
    csv_path = "../dataset/hirevue-answer-sheet.csv"
    
    def __init__(self, csv_path):
        # loads the csv when the class is instantiated 
        self.df = pd.read_csv(csv_path)
        
        # verify columns exist, behavioral does not matter just ensuring it exists 
        required_columns = {"BEHAVIORAL_QUESTIONS","SAMPLE_POSITIVE_ANSWERS","POSITIVE_SENTIMENT","SAMPLE_NEGATIVE_ANSWERS","NEGATIVE_SENTIMENT"}
        if not required_columns.issubset(self.df.columns):
            raise ValueError(f"CSV file must contain the columns: {required_columns}")
        self.positive_sentences = []  # store positive tuples: (positive_answer, positive_sentiment_expected)
        self.negative_sentences = []  # store negative tuples: (negative_answer, negative_sentiment_expected)

    def grab_sentences_and_sentiment(self):
        """
        gets each row of the CSV and extracts only the 'sentence' and 'expected_sentiment' columns.
        """
        # .iterrows() loops through the rows geeksforgeeks
        for _, row in self.df.iterrows():
            positive_sentence = row["SAMPLE_POSITIVE_ANSWERS"]
            positive_sentiment_expected = row["POSITIVE_SENTIMENT"]
            
            negative_sentence = row["SAMPLE_NEGATIVE_ANSWERS"]
            negative_sentiment_expected = row["NEGATIVE_SENTIMENT"]
            
            self.positive_sentences.append((positive_sentence, positive_sentiment_expected))
            self.negative_sentences.append((negative_sentence, negative_sentiment_expected))
           
        # temp will store both positive and negative sentiment sentences to return a singular array 
        # containing both 
        temp = []
        for entry in self.positive_sentences: 
            temp.append(entry)
            
        for entry in self.negative_sentences:
            temp.append(entry)
        return temp

    """
    might not be needed since we can already grab it using a single function
    we could process the sentiment values here (int values)
    or just return a list of expected_sentiments
    """
    # def grab_sentiment(self):
    #     return self.df["expected_sentiment"].tolist()
    
# sample main 
if __name__ == "__main__":
    # testing the csvReadInFunctions
    reader = csv_read_in_functions("../dataset/hirevue-answer-sheet.csv")
    sentence_pairs = reader.grab_sentences_and_sentiment()
    
    for sentence, sentiment in sentence_pairs:
        print(f"Sentence: {sentence}\nExpected Sentiment: {sentiment}\n")

    
