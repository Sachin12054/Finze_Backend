# ml_model/transformer_categorizer.py
import os, json, numpy as np, torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class TransformerCategorizer:
    def __init__(self, model_path='models/expense_distilbert', device=None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = model_path
        self._load()

    def _load(self):
        label_map_file = os.path.join(self.model_path, 'label_map.json')
        if not os.path.exists(self.model_path) or not os.path.exists(label_map_file):
            raise FileNotFoundError("Model or label_map.json missing in " + self.model_path)
        with open(label_map_file,'r') as f:
            label_map = json.load(f)
        # Ensure labels sorted by index
        self.labels = [label_map[str(i)] if str(i) in label_map else label_map[i] for i in sorted(map(int,label_map.keys()))]
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
        self.model.to(self.device)
        self.model.eval()

    @property
    def categories(self):
        return self.labels

    def _softmax(self, x):
        e = np.exp(x - np.max(x))
        return e / e.sum()

    def predict_category(self, merchant_name, description, amount=0.0, topk=3):
        text = (merchant_name or '') + ' - ' + (description or '')
        text_with_amount = text + ' [AMT] ' + str(amount)
        enc = self.tokenizer(text_with_amount, truncation=True, padding='max_length', max_length=128, return_tensors='pt')
        input_ids = enc['input_ids'].to(self.device)
        attention_mask = enc['attention_mask'].to(self.device)
        with torch.no_grad():
            logits = self.model(input_ids=input_ids, attention_mask=attention_mask).logits[0].cpu().numpy()
            probs = self._softmax(logits)
            order = list(np.argsort(probs)[::-1])
            topk_idxs = order[:topk]
            suggested = [(self.labels[i], float(probs[i])) for i in topk_idxs]
            pred = self.labels[order[0]]
            return {
                'category': pred,
                'confidence': float(probs[order[0]]),
                'suggested': suggested,
                'all_probabilities': {self.labels[i]: float(probs[i]) for i in range(len(probs))}
            }
