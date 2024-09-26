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
    "Select user_input_id ,text, label From user_input where label like 'user-study-%'"
).fetchall()

test_set = []

for index, user_input in enumerate(user_inputs):
    user_input_id, text, label = user_input
    print("-" * 30)
    print(f"{index}|{len(user_inputs)}: {user_input_id=}, ")
    try:
        prefs = extract_student_preferences(student_input=text)
    except Exception as e:
        print(e)
    test_set.append(
        {
            "user_input_id": user_input_id,
            "text": text,
            "label": label,
            "prefs_expected": prefs,
        }
    )

test_set_json = json.dumps(test_set)
with open("test_set.json", "w") as file:
    file.write(test_set_json)

print(f"Generated test_set.json. Now check the test set and correct it")
