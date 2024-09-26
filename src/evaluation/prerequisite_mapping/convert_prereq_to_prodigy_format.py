import json

from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()
# Change to the appropriate directory
resources_path = "../../../resources"

modules_con = sqlite3.connect(os.path.join(resources_path, "modules.db"))


rows = modules_con.execute(
    "SELECT module_id_uni, prereq FROM modules where prereq != '' order by random()"
).fetchall()


def rows_to_dict(rows):
    prereq_dataset = []
    for row in rows:
        text_dict = {"text": row[1], "meta": {"module_id_uni": row[0]}}
        prereq_dataset.append(text_dict)
    return prereq_dataset


dataset = rows_to_dict(rows)
with open("module_prerequisites.jsonl", "w") as file:
    for entry in dataset:
        file.write(json.dumps(entry) + "\n")
