from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
import os

model_path = "C:/Users/Issam/code/api/open_models/results/checkpoint-120"

model = AutoModelForSequenceClassification.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained('roberta-base')