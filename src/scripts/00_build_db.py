import os.path
import sqlite3
from dbml_sqlite import toSQLite

# Change to the appropriate directory
os.chdir("../../")
resources_path = "resources"

# Convert DBML to SQLite DDL
ddl = toSQLite(os.path.join(resources_path, "modules.dbml"))

# Create a new database and execute the DDL script
modules_con = sqlite3.connect(os.path.join(resources_path, "modules.db"))
with modules_con:
    modules_con.executescript(ddl)

# Connect to the old database
modules_old_con = sqlite3.connect(os.path.join(resources_path, "modules_old.db"))

# Fetch all rows from the old database
module_rows = modules_old_con.execute(
    "SELECT `INDEX`, ID, NAME, DEPT_ID, LEVEL_CLEANED, LANG_CLEANED, ECTS, PREREQ, ENGLISH_DESCRIPTION, VALID_FROM, VALID_TO, LINK, LINK_TYPE, DIGITAL_SCORE FROM SCORED_MODULES_NEW WHERE UNI = 'TUM'"
).fetchall()

# Insert the fetched rows into the new database
with modules_con:
    for row in module_rows:
        # Execute the insert statement
        modules_con.execute(
            "INSERT INTO modules (module_id, module_id_uni, name, org_id, level, lang, ects, prereq, description, valid_from, valid_to, link, link_type, digital_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            row,
        )


# topics
topic_rows = modules_old_con.execute(
    "SELECT distinct TOPIC_ID, TOPIC from NERD_MODULES_NEW nmw, SCORED_MODULES_NEW smw WHERE nmw.`INDEX` = smw.`INDEX` and smw.UNI = 'TUM' and TOPIC is not null"
).fetchall()

# topics where topic = null will be dropped
with modules_con:
    for row in topic_rows:
        # Execute the insert statement
        modules_con.execute(
            "INSERT INTO topics (topic_id, topic, embedding) VALUES (?, ?, null)", row
        )

module_topic_mapping_rows = modules_old_con.execute(
    "SELECT nmw.`INDEX`, TOPIC_ID from NERD_MODULES_NEW nmw, SCORED_MODULES_NEW smw WHERE nmw.`INDEX` = smw.`INDEX` and smw.UNI = 'TUM' and TOPIC is not null"
).fetchall()

with modules_con:
    for row in module_topic_mapping_rows:
        # Execute the insert statement
        modules_con.execute(
            "INSERT INTO module_topic_mappings (module_id, topic_id) VALUES (?, ?)", row
        )
