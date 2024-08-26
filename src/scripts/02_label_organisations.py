# Goal of this script is to assign a school and a department to applicable organisations as well as categorize the organisations

import os
import sqlite3

# Change to the appropriate directory
os.chdir("../../")
resources_path = "resources"

# Create a new database and execute the DDL script
modules_con = sqlite3.connect(os.path.join(resources_path, "modules.db"))


# ----------- Label organisations as school / department / ... -----------
# Schools
query = "UPDATE organisations SET org_type = 'school' WHERE hierarchy = 1 and org_id LIKE 'TUS%'"
modules_con.execute(query)
modules_con.commit()

# Departments
query = "UPDATE organisations SET org_type = 'department' WHERE hierarchy = 2 and org_id LIKE 'TUS%DP%' and name LIKE 'Department%'"
modules_con.execute(query)
modules_con.commit()

# administration
query = "UPDATE organisations SET org_type = 'administration' where name like '%School Office%' or name like '%School Zentral%'"
modules_con.execute(query)
modules_con.commit()

# Former Facilities
query = (
    "UPDATE organisations SET org_type = 'former_facility' where name like '%Ehem%';"
)
modules_con.execute(query)
modules_con.commit()

# Chairs
query = "UPDATE organisations SET org_type = 'chair' where org_type is null and (name like '%Professur%' or name like '%Lehrstuhl%')"
modules_con.execute(query)
modules_con.commit()

# Clinics
query = "UPDATE organisations SET org_type = 'clinic' where name like 'Klinik%'"
modules_con.execute(query)
modules_con.commit()

# -------------- assign a school and a department to applicable organisations -----------

mapping_query = """CREATE TEMP TABLE temp_parents AS
WITH RECURSIVE
    school_mapping AS (SELECT org_id, org_id as school_id
                       FROM organisations
                       WHERE hierarchy = 2
                         AND org_id LIKE 'TUS%'
                       UNION ALL
                       SELECT o2.org_id, p.school_id
                       FROM organisations o2,
                            school_mapping p
                       WHERE o2.parent_org_id = p.org_id),
    department_mapping AS (SELECT org_id, org_id as dep_id
                           FROM organisations
                           WHERE hierarchy = 3
                             AND org_id LIKE 'TUS%DP%'
                             AND name LIKE 'Department%'
                           UNION ALL
                           SELECT o2.org_id, p.dep_id
                           FROM organisations o2,
                                department_mapping p
                           WHERE o2.parent_org_id = p.org_id)
SELECT p.org_id, p.school_id, d.dep_id
FROM school_mapping p
         LEFT JOIN department_mapping d ON p.org_id = d.org_id;"""

update_orgs_query = """UPDATE organisations
SET school_id = (SELECT school_id
                 FROM temp_parents
                 WHERE organisations.org_id = temp_parents.org_id),
    dep_id    = (SELECT dep_id
                 FROM temp_parents
                 WHERE organisations.org_id = temp_parents.org_id);"""

drop_temp_table_query = """DROP TABLE temp_parents;"""

modules_con.execute(mapping_query)
modules_con.execute(update_orgs_query)
modules_con.execute(drop_temp_table_query)
modules_con.commit()

