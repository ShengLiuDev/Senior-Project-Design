# %pip install pandas
# # upgrades accelerate to at least 0.26.0
# %pip install "accelerate>=0.26.0"
# # installs huggingface_hub as needed 
# %pip install huggingface_hub
# # installs pytorch as needed

# ensure dependencies are installed properly
from transformers import Trainer, TrainingArguments
from torch.utils.data import Dataset
import torch
import accelerate
import pandas as pd

# %load_ext autoreload
# %autoreload 2
# %reload_ext autoreload
# # should reload kernel as needed
# # stackoverflow article: https://stackoverflow.com/questions/63595912/how-to-restart-kernel-in-vscode-to-completely-reload-imports

# get the CSV reader and grab the data from LatinCsvReadInFunctions class
csv_reader = csv_read_in_functions("../dataset/hirevue-answer-sheet.csv")
sentence_data = csv_reader.grab_sentences_and_sentiment()

class sentiment_analysis:
    def __init__(self, sentences_data = sentence_data, model_name="distilbert/distilbert-base-uncased-finetuned-sst-2-english"):
        from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
        csv_reader = csv_read_in_functions("../dataset/hirevue-answer-sheet.csv")
        sentences_data = csv_reader.grab_sentences_and_sentiment()
        
        tokenizer = DistilBertTokenizer.from_pretrained(model_name)
        model = DistilBertForSequenceClassification.from_pretrained(model_name)
        # use_fast here since the tokenizer.json file doesn't exist in the bert model and we need to rely on vocab.json and merges.txt
        
        self.sentences_data = sentences_data
        self.tokenizer = tokenizer
        self.model = model
        
        # initializes MPS and ensures the model is set to the correct device before any training starts
        device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        self.model.to(device)

        
        # mapping sentiment to numeric values (may need to adjust as needed later depending on results)
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

# testing
lsa = sentiment_analysis(sentences_data)
dataset = lsa.prepare_dataset()
lsa.train(dataset)
