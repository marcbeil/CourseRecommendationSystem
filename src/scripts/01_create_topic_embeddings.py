import json
import sqlite3

from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()
# Change to the appropriate directory
os.chdir("../../")
resources_path = "resources"

# Create a new database and execute the DDL script
modules_con = sqlite3.connect(os.path.join(resources_path, "modules.db"))

topic_rows = modules_con.execute("SELECT topic_id, topic FROM topics WHERE topic is not null").fetchall()

topics = [topic_row[1] for topic_row in topic_rows]
batch_size = 2000
cursor = modules_con.cursor()
client = OpenAI()
# Loop through topics in batches
for i in range(0, len(topics), batch_size):
    print(f"Processing batch {i // batch_size + 1}")
    batch_topics = topics[i : i + batch_size]
    response = client.embeddings.create(
        model="text-embedding-ada-002", input=batch_topics
    )
    topics_with_embeddings = []
    for j, data in enumerate(response.data):
        topic_id = topic_rows[i + j][0]
        topic = topic_rows[i + j][1]
        embedding = json.dumps(data.embedding)
        topics_with_embeddings.append((embedding, topic_id))

    # Insert data into the database in chunks to avoid memory issues
    cursor.executemany(
        """
        UPDATE topics SET embedding = ? WHERE topic_id = ?
    """,
        topics_with_embeddings,
    )

    # Commit and clear the list to free memory
    modules_con.commit()
