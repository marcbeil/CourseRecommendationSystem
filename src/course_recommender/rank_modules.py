import json

import faiss
import numpy as np
from openai import OpenAI

from course_recommender.db.models import Session, Topic, ModuleTopicMapping
from course_recommender.module_filter import filtered_modules, pref


def rank_modules(module_ids, pref):
    session = Session()
    if pref.topics_of_interest and len(pref.topics_of_interest) > 0:
        module_topics = (
            session.query(Topic)
            .join(ModuleTopicMapping)
            .filter(ModuleTopicMapping.module_id.in_(module_ids))
            .distinct()
            .all()
        )
        print(len(module_topics))
        rank_modules_by_topics(module_topics, pref.topics_of_interest)


from collections import defaultdict


def average_rank_aggregation(rankings, n):
    """
    Aggregates multiple rankings using average rank method.

    Parameters:
    rankings (list of lists): List of rankings, where each ranking is a list of indices ordered by relevance.
    n (int): Total number of items to rank.

    Returns:
    list: Aggregated ranking of indices.
    """
    rank_sums = defaultdict(int)
    rank_counts = defaultdict(int)

    for ranking in rankings:
        for rank, index in enumerate(ranking):
            rank_sums[index] += rank
            rank_counts[index] += 1

    average_ranks = {
        index: rank_sums[index] / rank_counts[index] for index in rank_sums.keys()
    }

    # Sort by average rank
    aggregated_ranking = sorted(average_ranks, key=average_ranks.get)

    return aggregated_ranking


# Example usage
rankings = [
    [0, 1, 2, 3, 4],  # First ranking
    [2, 0, 3, 4, 1],  # Second ranking
    [3, 0, 4, 2, 1],  # Third ranking
    # Add more rankings as needed
]

n = len(rankings[0])  # Assuming all rankings are of same length
aggregated_ranking = average_rank_aggregation(rankings, n)

print("Aggregated Ranking:", aggregated_ranking)


def rank_modules_by_topics(module_topics, topics_of_interest):
    def build_index(embeddings, dimension=1536):
        embeddings = [
            np.array(json.loads(embedding_str)) for embedding_str in embeddings
        ]
        # Convert the list of arrays into a single NumPy array
        embeddings_np = np.array(embeddings)
        _index = faiss.IndexFlatL2(dimension)  # build the index
        _index.add(embeddings_np)
        return _index

    def vector_similarity_search(index, topic_str, k):
        client = OpenAI()
        topic_embedding = (
            client.embeddings.create(input=topic_str, model="text-embedding-ada-002")
            .data[0]
            .embedding
        )
        embedding_np = np.array(topic_embedding).reshape(
            1, -1
        )  # Reshape to a 2D array (1, dimension)
        distances, indices = index.search(embedding_np, k)

        return distances, indices

    embeddings = [topic.embedding for topic in module_topics]
    index = build_index(embeddings)
    rankings = []
    for topic in topics_of_interest:
        print(topic)
        distances, indices = vector_similarity_search(
            index, topic, k=len(module_topics)
        )
        rankings.append(indices[0])
        print(indices[0])
        for i, index in enumerate(indices[0]):
            print(f"{topic}: {i}. {module_topics[index]}")
            if i > 25:
                break


rank_modules([m.module_id for m in filtered_modules], pref=pref)
