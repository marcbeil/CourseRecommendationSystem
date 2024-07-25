import os
import sqlite3

import faiss  # make faiss available
import json
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import text
import logging
from course_recommender.db.models import Session, Topic


load_dotenv()
modules_con = sqlite3.connect(os.getenv("DB_PATH"))
cursor = modules_con.cursor()


class VectorStore:
    def __init__(self, topics):
        self.topics: [Topic] = topics
        self.index = self.build_index([topic.embedding for topic in topics])

    @staticmethod
    def build_index(embeddings, dimension=1536):
        embeddings = [
            np.array(json.loads(embedding_str)) for embedding_str in embeddings
        ]
        # Convert the list of arrays into a single NumPy array
        embeddings_np = np.array(embeddings)

        _index = faiss.IndexFlatL2(dimension)  # build the index
        _index.add(embeddings_np)
        return _index

    def vector_similarity_search(self, topic_str, k):
        client = OpenAI()
        topic_embedding = (
            client.embeddings.create(input=topic_str, model="text-embedding-ada-002")
            .data[0]
            .embedding
        )
        embedding_np = np.array(topic_embedding).reshape(
            1, -1
        )  # Reshape to a 2D array (1, dimension)
        distances, indices = self.index.search(embedding_np, k)
        return [topic for index, topic in enumerate(self.topics) if index in indices[0]]

    def map_topic(self, topic, k):
        return self.vector_similarity_search(topic_str=topic, k=k)

    def map_topics(self, topics, k):
        topic_mappings = {}
        for topic in topics:
            topic_mappings[topic] = self.map_topic(topic, k)
        return topic_mappings
