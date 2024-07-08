import os
import sqlite3

# Change to the appropriate directory
os.chdir("../../")
resources_path = "resources"

# Create a new database and execute the DDL script
modules_con = sqlite3.connect(os.path.join(resources_path, "modules.db"))

"""
--------------------------------------------------------------------------------------------------------------
-- Schools (7)
SELECT * FROM organisations WHERE hierarchy = 1 and org_id LIKE 'TUS%';
--------------------------------------------------------------------------------------------------------------
-- Departments (29)
SELECT * FROM organisations WHERE hierarchy = 2 and org_id LIKE 'TUS%DP%' and name LIKE 'Department%';
--------------------------------------------------------------------------------------------------------------
-- Administration
SELECT * FROM organisations WHERE hierarchy >=2 and (name like '%School Office%' or name like '%School Zentral%')

-- School Offices (7)
SELECT * FROM organisations WHERE hierarchy = 2 and name like '%School Office%';

-- School Zentral (7)
SELECT * FROM organisations WHERE hierarchy = 2 and name like '%School Zentral%';
--------------------------------------------------------------------------------------------------------------
-- Alle Ehemaligen Einrichtungen (47)
SELECT * FROM organisations where name like '%Ehem%';

-- Ehemalige Einrichtungen der TUM (1)
SELECT * FROM organisations where name like '%Ehemalige%' and hierarchy != 2 and hierarchy != 3;

-- Ehemalige EInrichtungen  der Schools + Munich Center for Technology in Society (8)
SELECT * FROM organisations where name like '%Ehemalige%' and hierarchy = 2;

--- Ehemalige Einrichtungen des Department of x (29)
SELECT * FROM organisations where hierarchy = 3 and name LIKE '%Department%';

-- Diverse ehemalige Einrichtungen (8)
SELECT * FROM organisations where hierarchy = 3 and name not LIKE '%Department%' and name LIKE '%Ehemalige%';
--------------------------------------------------------------------------------------------------------------
-- Chairs (929)
SELECT * FROM organisations where org_type is null and (name like '%Professur%' or name like '%Lehrstuhl%')
--------------------------------------------------------------------------------------------------------------
-- Clinic (29)
SELECT * FROM organisations where name like 'Klinik%'

-- Institute (9)
SELECT * FROM organisations WHERE hierarchy = 2 and name like '%Institut%';

-- Sonstige mit hierarchy = 2 (31)
SELECT * FROM organisations WHERE hierarchy = 2 and name not like '%School Office%' and name not like 'Department%' and name not like 'Ehemalige%' and name not like '%School Zentral%' and name not like '%Institut%';

"""

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
query = "UPDATE organisations SET org_type = 'former_facility' where name like '%Ehem%';"
modules_con.execute(query)
modules_con.commit()

# Chairs
query = "UPDATE organisations SET org_type = 'chair' where org_type is null and (name like '%Professur%' or name like '%Lehrstuhl%')"
modules_con.execute(query)
modules_con.commit()

query = "UPDATE organisations SET org_type = 'clinic' where name like 'Klinik%'"
modules_con.execute(query)
modules_con.commit()

