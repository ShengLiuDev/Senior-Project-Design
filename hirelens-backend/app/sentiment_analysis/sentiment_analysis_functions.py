from transformers import Trainer, TrainingArguments
from torch.utils.data import Dataset
import torch
import accelerate
import pandas as pd
import os
import sys
import requests
from app.sentiment_analysis.csv_readin_functions import csv_read_in_functions

# Add the project root to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

class sentiment_analysis:
    def __init__(self, model_name="distilbert/distilbert-base-uncased-finetuned-sst-2-english"):
        from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
        
        # Initialize CSV reader and get data
        dataset_path = os.path.join(PROJECT_ROOT, 'app', 'dataset', 'hirevue-answer-sheet.csv')
        csv_reader = csv_read_in_functions(dataset_path)
        self.sentences_data = csv_reader.grab_sentences_and_sentiment()
        
        # Initialize tokenizer and model
        tokenizer = DistilBertTokenizer.from_pretrained(model_name)
        model = DistilBertForSequenceClassification.from_pretrained(model_name)
        
        self.tokenizer = tokenizer
        self.model = model
        
        # Initialize device and move model to appropriate device
        device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        self.model.to(device)
        
        # Mapping sentiment to numeric values
        self.label2id = {"positive": 0, "negative": 1}
        self.model = DistilBertForSequenceClassification.from_pretrained(
            model_name,
            num_labels=len(self.label2id)
        )
        
    def prepare_dataset(self, max_length=128):
        """
        convert the sentences_data into a format suitable for training
        we're using a custom pytorch format here
        """
        class sentiment_dataset(Dataset):
            def __init__(self, data, tokenizer, max_length):
                self.data = data
                self.tokenizer = tokenizer
                self.max_length = max_length   # ensures max length of sentiment doesn't exceed this
            
            def __len__(self):
                return len(self.data)
            
            def __getitem__(self, idx):
                sentence, sentiment = self.data[idx]
                # vonvert sentiment to label; 
                # assuming self.label2id is available in the outer scope
                
                if sentiment.lower() == "positive":
                    label = 0 
                else:
                    label = 1  
                
                encoding = self.tokenizer(
                    sentence,
                    truncation=True,
                    padding="max_length",
                    max_length=max_length,
                    return_tensors="pt"
                )
                # got from hugging face documentation
                encoding = {key: value.squeeze(0) for key, value in encoding.items()}
                encoding["labels"] = torch.tensor(label)
                return encoding
        
        return sentiment_dataset(self.sentences_data, self.tokenizer, max_length)
    
    # training, evaluation, and prediction methods here.
    def train(self, dataset, output_dir="./results", num_train_epochs=3, per_device_train_batch_size=16):
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            logging_steps=10,
            save_steps=500,
            evaluation_strategy="no",
            # Note: don't use evaluation_strategy will be deprecated in version 4.46 transformers 
            # use eval_strategy 
            no_cuda=True 
            # this applies for macbook use only, if you're on windows or a linux system, comment no_cuda out 
            # this avoids the "RuntimeError: Placeholder storage has not been allocated on MPS device!" error
        )
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
        )
        trainer.train()

    def predict(self, text):
        """
        Predict the sentiment of a given text
        Returns 'positive' or 'negative'
        """
        # Tokenize the input text
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        
        # Move inputs to the same device as the model
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        # Get model predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=-1)
            
        # Convert prediction to sentiment label
        sentiment = "positive" if predictions.item() == 0 else "negative"
        return sentiment

    def reformulate_positive(self, text):
        """
        Generate a more positive version of the given text
        """
        prompt = f"""
        You are an expert interviewer helping a candidate improve their answer.
        The candidate's answer is: "{text}"
        
        Please provide a more positive and constructive version of this answer,
        maintaining the same key points but with a more optimistic and confident tone.
        Focus on:
        1. Using positive language
        2. Emphasizing strengths and achievements
        3. Maintaining professionalism
        4. Keeping the same core message
        """
        
        # Make the API request
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "HTTP-Referer": "http://localhost:3000",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek/deepseek-r1:free",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            content = response.json()["choices"][0]["message"]["content"]
            return content.strip()
            
        except Exception as e:
            print(f"Error generating positive reformulation: {str(e)}")
            return "Unable to generate positive reformulation at this time."

# testing
# lsa = sentiment_analysis(sentences_data)
# dataset = lsa.prepare_dataset()
# lsa.train(dataset)
