import os
import sqlite3

import faiss  # make faiss available
import json
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
modules_con = sqlite3.connect(os.getenv("DB_PATH"))
cursor = modules_con.cursor()


def filter_org_by_school(school_name="Computation, Information and Technology"):
    query = """
            WITH RECURSIVE OrgHierarchy AS (
            -- Anchor member: start with the input school
            SELECT org_id, parent_org_id, name
            FROM organisations
            WHERE name = ?  -- Replace with the actual school ID
        
            UNION ALL
        
            -- Recursive member: find all child organizations
            SELECT o.org_id, o.parent_org_id, o.name
            FROM organisations o
            INNER JOIN OrgHierarchy oh ON o.parent_org_id = oh.org_id
        )
        -- Select all child organizations
        SELECT org_id, name
        FROM OrgHierarchy;
    """
    return modules_con.execute(query, school_name).fetchall()


def get_topics_for_school(school_id):
    query = """
        WITH RECURSIVE OrgHierarchy AS (
    -- Anchor member: start with the input school
    SELECT org_id, parent_org_id, name
    FROM organisations
    WHERE org_id = ?  -- Replace with the actual school ID

    UNION ALL

    -- Recursive member: find all child organizations
    SELECT o.org_id, o.parent_org_id, o.name
    FROM organisations o
    INNER JOIN OrgHierarchy oh ON o.parent_org_id = oh.org_id
)
SELECT distinct t.topic_id, t.embedding, t.topic from topics t, modules m, module_topic_mappings mtm, OrgHierarchy oh WHERE m.module_id = mtm.module_id and oh.org_id = m.org_id and t.topic_id = mtm.topic_id
    """
    return modules_con.execute(query, (school_id,)).fetchall()


def build_index(school_id=None, dimension=1536):
    if school_id:
        topic_rows = get_topics_for_school(school_id=school_id)
    else:
        topic_rows = cursor.execute(
            "SELECT topic_id, embedding, topic FROM topics"
        ).fetchall()
    print(topic_rows)
    embeddings = [
        np.array(json.loads(embedding_str)) for _, embedding_str, _ in topic_rows
    ]
    _topics = [(topic_id, topic_str) for topic_id, _, topic_str in topic_rows]

    # Convert the list of arrays into a single NumPy array
    embeddings_np = np.array(embeddings)

    _index = faiss.IndexFlatL2(dimension)  # build the index
    _index.add(embeddings_np)
    return _index, _topics


def vector_similarity_search(index_with_topics, topic_str, k):
    index, topics = index_with_topics
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

    return [topic for i, topic in enumerate(topics) if i in indices[0]]
