import json
import sqlite3

import bs4
import requests
import os


# Create a new database and execute the DDL script
modules_con = sqlite3.connect("../../resources/modules.db")


def extract_orga_title_link(element):
    organisation = element.find("a", rel="Organisation")
    org_title = organisation.get_text()
    org_link = organisation["href"]
    return org_title, org_link


def extract_orga_ids_homepage(org_link):
    try:
        response = requests.get(org_link)
    except Exception as e:
        print(f"Error extracting orga ids for {org_link}: {e}")
    soup = bs4.BeautifulSoup(response.content, "html.parser")
    print(org_link)
    # Find the h3 tag with the subheader "technical description"
    subheader_tag = soup.find("h3", class_="subheader", string="technical description")

    org_id = None
    org_id_tumonline = None
    # Check if the subheader_tag was found
    if subheader_tag:
        # Find the following div with class 'profile_information_text'
        profile_info_div = subheader_tag.find_next_sibling(
            "div", class_="profile_information_text"
        )

        # Check if the profile_info_div was found
        if profile_info_div:
            # Find the small tag within that div and get its text
            small_tag = profile_info_div.find("small")
            profile_info_text = small_tag.get_text()
            org_id = profile_info_text.split("TUMonline:")[0]
            org_id_tumonline = profile_info_text.split("TUMonline:")[1].split(" ")[0]
    org_hp_tag = soup.find(class_="contact-wrapper")
    org_homepage = org_hp_tag.find("a")["href"] if org_hp_tag else None
    return org_id, org_id_tumonline, org_homepage


def depth_search(current, parent_org_id, hierarchy):
    if current is None:
        return

    org_title, org_link = extract_orga_title_link(current)
    org_id, org_id_tumonline, org_homepage = extract_orga_ids_homepage(org_link)
    print(f"{hierarchy}: {org_title}")

    try:
        modules_con.execute(
            "INSERT INTO organisations(org_id, name, link, homepage, org_id_tumonline, parent_org_id, hierarchy)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                org_id,
                org_title,
                org_link,
                org_homepage,
                org_id_tumonline,
                parent_org_id,
                hierarchy,
            ),
        )
        modules_con.commit()
    except Exception as e:
        print(e)

    child_elements = current.findAll(attrs={"data-level": f"{hierarchy+1}"})
    for element in child_elements:
        depth_search(current=element, parent_org_id=org_id, hierarchy=hierarchy + 1)


def add_missing_courses():
    with open("./manual_org_mapping.json", "r") as file:
        mapping = json.load(file)
    org_rows = []
    for org in mapping["orgs"]:
        org_row = (
            org["org_id"],
            org["name"],
            org["parent_org_id"] if org["parent_org_id"] != "" else None,
        )
        org_rows.append(org_row)
    modules_con.executemany(
        "INSERT OR IGNORE INTO organisations (org_id, name, parent_org_id) VALUES (?,?,?)",
        org_rows,
    )
    modules_con.commit()


def main():
    response = requests.get("https://portal.fis.tum.de/de/organisations/")

    soup = bs4.BeautifulSoup(response.content, "html.parser")

    level = 0
    element = soup.find(attrs={"data-level": f"{level}"})
    depth_search(element, None, hierarchy=0)
    add_missing_courses()


if __name__ == "__main__":
    main()
