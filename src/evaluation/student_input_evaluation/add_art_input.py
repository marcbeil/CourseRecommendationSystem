import os
import pandas as pd
import sqlite3

# Load the CSV file into a DataFrame
df = pd.read_csv("artificial_student_input.csv")

# Set up the database connection
resources_path = "../../../resources"
modules_con = sqlite3.connect(os.path.join(resources_path, "modules.db"))

# Iterate over the rows of the DataFrame
for _, row in df.iterrows():
    # Print the 'User Query' field for debugging
    print(row["User Query"])

    # Insert the row into the `student_input` table
    modules_con.execute(
        "INSERT INTO user_input(text, label) VALUES (?, 'artificial')",
        (row["User Query"],),
    )

# Commit the transaction
modules_con.commit()

# Close the connection
modules_con.close()
