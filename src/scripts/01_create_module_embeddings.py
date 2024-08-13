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

module_rows = modules_con.execute("SELECT module_id, name FROM modules").fetchall()

names = [module_row[1] for module_row in module_rows]
batch_size = 2000
cursor = modules_con.cursor()
client = OpenAI()
# Loop through topics in batches
for i in range(0, len(names), batch_size):
    print(f"Processing batch {i // batch_size + 1}")
    batch_topics = names[i : i + batch_size]
    response = client.embeddings.create(
        model="text-embedding-ada-002", input=batch_topics
    )
    module_ids_with_name_embeddings = []
    for j, data in enumerate(response.data):
        module_id = module_rows[i + j][0]
        name = module_rows[i + j][1]
        embedding = json.dumps(data.embedding)
        module_ids_with_name_embeddings.append((embedding, module_id))

    # Insert data into the database in chunks to avoid memory issues
    cursor.executemany(
        """
        UPDATE modules SET name_embedding = ? WHERE module_id = ?
    """,
        module_ids_with_name_embeddings,
    )

    # Commit and clear the list to free memory
    modules_con.commit()
