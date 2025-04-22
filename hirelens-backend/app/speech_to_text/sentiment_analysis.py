import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Global flag to indicate if the main sentiment analyzer failed
USE_FALLBACK = False

class SentimentAnalyzer:
    """
    Class to analyze sentiment of text and provide reformulations.
    This is a wrapper around the sentiment_analysis class.
    """
    def __init__(self):
        """Initialize the sentiment analyzer"""
        global USE_FALLBACK
        
        try:
            if not USE_FALLBACK:
                from app.sentiment_analysis.sentiment_analysis_functions import sentiment_analysis
                self.sentiment_analyzer = sentiment_analysis()
                print("SentimentAnalyzer initialized successfully")
            else:
                print("Using fallback sentiment analyzer due to previous errors")
                self.sentiment_analyzer = None
        except Exception as e:
            print(f"Error initializing sentiment analyzer, using fallback mode: {str(e)}")
            import traceback
            traceback.print_exc()
            USE_FALLBACK = True
            self.sentiment_analyzer = None
    
    def analyze_sentiment(self, text):
        """
        Analyze the sentiment of the given text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            str: 'positive', 'negative', or 'neutral'
        """
        global USE_FALLBACK
        
        if not text or len(text.strip()) < 5:
            print("Text too short for sentiment analysis")
            return "neutral"
        
        # If we're in fallback mode or the sentiment analyzer isn't available
        if USE_FALLBACK or self.sentiment_analyzer is None:
            print("Using simple rule-based fallback for sentiment analysis")
            return self._simple_sentiment_analysis(text)
            
        try:
            # Use the sentiment analyzer to predict sentiment
            result = self.sentiment_analyzer.predict(text)
            print(f"Sentiment analysis result: {result}")
            return result
        except Exception as e:
            print(f"Error in sentiment analysis, switching to fallback: {str(e)}")
            import traceback
            traceback.print_exc()
            USE_FALLBACK = True
            return self._simple_sentiment_analysis(text)
    
    def _simple_sentiment_analysis(self, text):
        """
        Very simple rule-based sentiment analysis as a fallback
        """
        text = text.lower()
        
        # Define positive and negative word lists
        positive_words = ['good', 'great', 'excellent', 'happy', 'positive', 
                         'wonderful', 'fantastic', 'amazing', 'love', 'best',
                         'awesome', 'enjoy', 'success', 'successful', 'well']
                         
        negative_words = ['bad', 'poor', 'terrible', 'horrible', 'negative',
                         'awful', 'worst', 'hate', 'fail', 'failure', 'wrong',
                         'problem', 'difficult', 'unfortunately', 'sorry']
        
        # Count occurrences
        positive_count = sum(1 for word in positive_words if word in text.split())
        negative_count = sum(1 for word in negative_words if word in text.split())
        
        # Determine sentiment
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def reformulate_positive(self, text):
        """
        Reformulate negative text to be more positive
        
        Args:
            text (str): Text to reformulate
            
        Returns:
            str: Reformulated text
        """
        global USE_FALLBACK
        
        if not text or len(text.strip()) < 5:
            return "Text too short for reformulation"
        
        # If we're in fallback mode or the sentiment analyzer isn't available
        if USE_FALLBACK or self.sentiment_analyzer is None:
            return "I would suggest rephrasing your answer to be more positive and confident."
            
        try:
            # Use the sentiment analyzer to reformulate
            reformulation = self.sentiment_analyzer.reformulate_positive(text)
            print(f"Successfully reformulated text")
            return reformulation
        except Exception as e:
            print(f"Error in reformulation: {str(e)}")
            import traceback
            traceback.print_exc()
            USE_FALLBACK = True
            return "I would suggest rephrasing your answer to be more positive and confident." 