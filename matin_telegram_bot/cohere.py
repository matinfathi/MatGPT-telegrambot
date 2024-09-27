import numpy as np
import requests

from typing import List
import os
from constants import CohereConfig


class Cohere:
    def __init__(self, api_key: str = None):
        try:
            self.api_key = api_key if api_key else os.environ["CO_API_KEY"]
        except Exception as e:
            raise ValueError(f"The api key for cohere is required. {e}") from e

    def query(self, prompt: str, model: str = CohereConfig.CHAT_MODEL_COMMAND_R_PLUS) -> str:
        url = "https://api.cohere.com/v1/chat"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "message": prompt,
            "model": model,
        }
        response = requests.post(url, headers=headers, json=data)

        return response.json()["text"]

    def embedding(self, texts: List[str], model: str = CohereConfig.EMBEDDING_MODEL_3) -> np.array:
        url = "https://api.cohere.com/v1/embed"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        batch_size = 90
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            data = {
                "model": model,
                "texts": batch_texts,
                "input_type": "classification"
            }

            response = requests.post(url, headers=headers, json=data)

            all_embeddings.extend(response.json()["embeddings"])

        return np.array(all_embeddings)
