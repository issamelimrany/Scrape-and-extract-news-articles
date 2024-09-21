import os
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Loading the trained model  from the checkpoint
model_path = "open_models/results/checkpoint-120"

tokenizer = AutoTokenizer.from_pretrained('roberta-base')
model = AutoModelForSequenceClassification.from_pretrained(model_path)

def classify_article(article_text):
    # Preprocessing the content 
    inputs = tokenizer(article_text, truncation=True, padding=True, return_tensors="pt")
    
    model.eval()
    
    # the inference
    with torch.no_grad():
        outputs = model(**inputs)
    
    # predicted label (0 = Funding Rounds, 1 = Exits)
    logits = outputs.logits
    predicted_class_id = torch.argmax(logits, dim=1).item()
    
    # Return the label based on the predicted class id
    if predicted_class_id == 0:
        return "Funding Rounds"
    elif predicted_class_id == 1:
        return "Exits"
    else:
        return "None"

# Note : as you may know in any ML model, garbage in == garbage out, so I've remarked a pattern upon testing the model
# so that the accurary remains as tested (97.5), the input article shall have those additional stuff present the given 
# data (other than the article, see the data for more details), I've concluded that the model picked up some patterns
# from there too, so for better results I would suggest to redo the training on a dataset that contains the pure content.