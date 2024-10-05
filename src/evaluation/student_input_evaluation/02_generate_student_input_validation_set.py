import json

import os
import sqlite3

from dotenv import load_dotenv

from backend.student_input_extraction import extract_student_preferences

load_dotenv()
with open("test_set.json") as file:
    test_set = json.load(file)

for index, entry in enumerate(test_set):
    print(f"{index}|{len(test_set)}: {entry}")
    try:
        prefs_actual = extract_student_preferences(student_input=entry["text"])
        entry["prefs_actual"] = prefs_actual
    except Exception as e:
        entry["error"] = str(e)
        entry["prefs_actual"] = None
        print(e)

with open("evaluation_set.json", "w") as file:
    file.write(json.dumps(test_set))
