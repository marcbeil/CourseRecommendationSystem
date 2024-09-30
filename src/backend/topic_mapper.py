import csv
from functools import lru_cache

import faiss  # make faiss available
import json
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import func
from backend.db_models import Session, Topic
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

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

    @lru_cache
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

        if threshold:
            # Filter out results based on the threshold
            mask = distances[0] <= threshold
            indices = indices[0][mask]
            distances = distances[0][mask]
        else:
            indices = indices[0]
            distances = distances[0]

        return [self.topics[index] for index in indices]

    def map_topic(self, topic, k, threshold=None):
        return self.vector_similarity_search(topic_str=topic, k=k, threshold=threshold)

    def map_topics(self, topics, k, threshold=None):
        topic_mappings = {}
        for topic in topics:
            topic_mappings[topic] = self.map_topic(topic, k, threshold=threshold)
        return topic_mappings

    def save_2d_projection(
        self, filename="projection.png", transparent=True, x_offset=0.003, y_offset=0.003
    ):
        # Convert embeddings to numpy array if not already done
        embeddings = np.array(
            [np.array(json.loads(topic.embedding)) for topic in self.topics]
        )

        # Use PCA to reduce dimensions to 2
        pca = PCA(n_components=2)
        embeddings_2d = pca.fit_transform(embeddings)

        # Plotting the 2D projection
        plt.figure(figsize=(10, 8))
        plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], s=50, alpha=0.7)

        # Add topic names with a slight offset to avoid overlap
        for i, topic in enumerate(self.topics):
            plt.text(
                embeddings_2d[i, 0],
                embeddings_2d[i, 1],
                topic.topic,
                fontsize=9,
            )

        # Customize the plot to keep axes but remove labels and ticks
        plt.xticks([])  # Remove x-axis ticks
        plt.yticks([])  # Remove y-axis ticks
        plt.gca().set_xticklabels([])  # Remove x-axis labels
        plt.gca().set_yticklabels([])  # Remove y-axis labels

        # Save the plot as an image
        plt.savefig(filename, bbox_inches="tight", transparent=transparent)

        # Close the plot to free up memory
        plt.close()

    def save_2d_projection_csv(self, filename="projection.csv"):
        # Convert embeddings to numpy array if not already done
        embeddings = np.array(
            [np.array(json.loads(topic.embedding)) for topic in self.topics]
        )

        # Use PCA to reduce dimensions to 2
        pca = PCA(n_components=2)
        embeddings_2d = pca.fit_transform(embeddings)

        # Save 2D projections to a CSV file
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Topic", "PCA1", "PCA2"])  # Header row
            for i, topic in enumerate(self.topics):
                writer.writerow([topic.topic, embeddings_2d[i, 0], embeddings_2d[i, 1]])
