import pickle

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences


class Tokenizer:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.word_to_id = pickle.load(f)
        self.id_to_word = {v: k for k, v in self.word_to_id.items()}
        self.vocab_size = len(self.word_to_id)

    def encode(self, text):
        return [self.word_to_id.get(w, 1) for w in text.split()]

    def encode_batch(self, text_list):
        return [self.encode(text) for text in text_list]

    def decode(self, ids):
        return "".join([self.id_to_word[i] for i in ids])

    def decode_batch(self, ids_list):
        return [self.decode(ids) for ids in ids_list]

    def __call__(
        self,
        text_list,
        max_length=None,
        padding=None,
        truncate="pre",
        dtype="int32",
        return_type=None,
    ):
        if len(text_list[0]) == 1:
            text_list = [text_list]
        encoded = self.encode_batch(text_list)
        attention_mask = [
            [1 for _ in range(len(encoded[i]))] for i in range(len(encoded))
        ]

        if padding is not None:
            encoded = pad_sequences(
                encoded,
                maxlen=max_length,
                dtype=dtype,
                padding=padding,
                truncating=truncate,
            )
            attention_mask = pad_sequences(
                attention_mask,
                maxlen=max_length,
                dtype=dtype,
                padding=padding,
                truncating=truncate,
            )

        if return_type is None:
            encoded = encoded if isinstance(encoded, list) else encoded.tolist()
            attention_mask = (
                attention_mask
                if isinstance(attention_mask, list)
                else attention_mask.tolist()
            )
        elif return_type == "np":
            encoded = encoded if isinstance(encoded, np.ndarray) else np.array(encoded)
            attention_mask = (
                attention_mask
                if isinstance(attention_mask, np.ndarray)
                else np.array(attention_mask)
            )
        elif return_type == "tf":
            encoded = tf.constant(encoded)
            attention_mask = tf.constant(attention_mask)

        return {"input_ids": encoded, "attention_mask": attention_mask}
