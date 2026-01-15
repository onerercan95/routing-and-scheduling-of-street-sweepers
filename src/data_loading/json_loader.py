import json

def load_config(path="dat/input/input.json"):
    with open(path) as f:
        return json.load(f)