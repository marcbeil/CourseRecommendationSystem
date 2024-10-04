import json
import os
import sqlite3

from dotenv import load_dotenv

from backend.student_input_extraction import extract_student_preferences

load_dotenv()
# Change to the appropriate directory
resources_path = "../../../resources"

modules_con = sqlite3.connect(os.path.join(resources_path, "modules.db"))


if "test_set.json" in os.listdir("."):
    with open("./test_set.json", "r") as file:
        test_set = json.load(file)
else:
    test_set = []
user_input_ids = list(map(lambda entry: entry["user_input_id"], test_set))

# Check if there are any user_input_ids to exclude
if user_input_ids:
    placeholders = ", ".join(
        "?" for _ in user_input_ids
    )  # Create the right number of placeholders
    query = f"""
        SELECT user_input_id, text, label 
        FROM user_input 
        WHERE (label LIKE 'user-study-%' or label = 'artificial')
        AND user_input_id NOT IN ({placeholders})
    """
    user_inputs = modules_con.execute(query, tuple(user_input_ids)).fetchall()
else:
    query = """
        SELECT user_input_id, text, label 
        FROM user_input 
        WHERE label LIKE 'user-study-%' or label = 'artificial'
    """
    user_inputs = modules_con.execute(query).fetchall()

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
