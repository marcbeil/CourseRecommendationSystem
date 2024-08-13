import faiss  # make faiss available
import json
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import func
from backend.db_models import Session, Topic

load_dotenv()


def get_all_topics(max_size=None):
    with Session() as session:
        topic_query = session.query(Topic)
        if max_size:
            topic_query = topic_query.order_by(func.random()).limit(max_size)
        topics = topic_query.all()
    return topics


class VectorStore:
    def __init__(self, topics=None, max_size=None):
        if not topics:
            topics = get_all_topics(max_size=max_size)
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

    def vector_similarity_search(self, topic_str, k, threshold=None):
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

        if threshold is not None:
            # Filter out results based on the threshold
            indices = indices[0][distances[0] <= threshold]
            distances = distances[0][distances[0] <= threshold]
        else:
            indices = indices[0]
            distances = distances[0]

        print(distances)
        return [self.topics[index] for index in indices]

    def map_topic(self, topic, k, threshold=None):
        return self.vector_similarity_search(topic_str=topic, k=k, threshold=threshold)

    def map_topics(self, topics, k, threshold=None):
        topic_mappings = {}
        for topic in topics:
            topic_mappings[topic] = self.map_topic(topic, k, threshold=threshold)
        return topic_mappings
