import json
import pickle


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def save_pickle(data, path):
    with open(path, "wb") as f:
        pickle.dump(data, f)
