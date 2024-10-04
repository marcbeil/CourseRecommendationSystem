import json

import os
import sqlite3

from dotenv import load_dotenv

from backend.student_input_extraction import extract_student_preferences

load_dotenv()
# Change to the appropriate directory
resources_path = "../../../resources"

modules_con = sqlite3.connect(os.path.join(resources_path, "modules.db"))

user_inputs = modules_con.execute(
    "Select user_input_id ,text From user_input where label like 'user-study-%' or label = 'artificial'"
).fetchall()

with open("test_set.json") as file:
    test_set = json.load(file)

for entry in test_set:
    try:
        prefs_actual = extract_student_preferences(student_input=entry["text"])
        entry["prefs_actual"] = prefs_actual
    except Exception as e:
        entry["error"] = e
        entry["prefs_actual"] = None
        print(e)

with open("evaluation_set.json", 'w') as file:
    file.write(json.dumps(test_set))
