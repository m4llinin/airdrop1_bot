import json


def load_texts(language: str = 'ru'):
    with open('texts.json', 'r', encoding='utf-8') as f:
        texts = json.load(f)
    return texts.get(language, texts['en'])
