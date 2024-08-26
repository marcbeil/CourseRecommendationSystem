# Map the extracted module ids / titles to already existing titles / ids in the db
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from functools import lru_cache
from rapidfuzz import fuzz
from dotenv import load_dotenv

load_dotenv()
# Change to the appropriate directory
os.chdir("../../")
resources_path = "resources"

modules_con = sqlite3.connect(os.path.join(resources_path, "modules.db"))


@lru_cache()
def fuzzy_similarity(a, b):
    return fuzz.ratio(a, b)


def levenshtein_distance(a, b):
    return SequenceMatcher(None, a, b).ratio() * 100


def map_extracted_ids():
    emi_rows = modules_con.execute(
        "SELECT extracted_module_identifier_id, module_id_uni, identifier FROM extracted_module_identifiers WHERE identifier_type = 'ID'"
    ).fetchall()

    # Use set for O(1) average time complexity for lookups
    all_module_ids = set(
        row[0]
        for row in modules_con.execute("SELECT module_id_uni FROM modules").fetchall()
    )
    pm_rows = [
        (module_id_uni, extracted_module_id, extracted_module_identifier_id)
        for extracted_module_identifier_id, module_id_uni, extracted_module_id in emi_rows
        if extracted_module_id in all_module_ids
    ]
    return pm_rows


# Pre-fetch school mapping to avoid repeated database hits
school_rows = modules_con.execute(
    """
    SELECT m.module_id_uni, o.dep_id, o.school_id
    FROM modules m
    JOIN organisations o ON m.org_id = o.org_id
    """
).fetchall()

school_mapping = {
    module_id: {"dep_id": dep_id, "school_id": school_id}
    for module_id, dep_id, school_id in school_rows
}


@lru_cache()
def compute_similarity_score(title_a, title_b):
    score = fuzz.ratio(title_a, title_b)
    suffixes = [("I", "II", "III"), ("1", "2", "3")]
    for suffix_group in suffixes:
        for i in range(len(suffix_group) - 1):
            if title_b.endswith(suffix_group[i]):
                if any(title_a.endswith(suffix) for suffix in suffix_group[i + 1 :]):
                    score -= 5
                break
    return score


# Prereq modules constraints
def process_emi_row(emi_row, all_module_ids_and_titles):
    extracted_module_identifier_id, module_id_uni, extracted_module_title = emi_row
    modules_filtered = all_module_ids_and_titles
    target_module = max(
        map(
            lambda module_id_title: (
                module_id_title[0],
                module_id_title[1],
                compute_similarity_score(module_id_title[1], extracted_module_title),
            ),
            modules_filtered,
        ),
        key=lambda module_id_title_score: module_id_title_score[2],
    )

    if target_module[2] > 70:
        return (
            module_id_uni,
            target_module[0],
            extracted_module_identifier_id,
            target_module[2],
        )
    return None


def map_extracted_titles():
    emi_rows = modules_con.execute(
        "SELECT extracted_module_identifier_id, module_id_uni, identifier FROM extracted_module_identifiers WHERE identifier_type = 'TITLE'"
    ).fetchall()
    all_module_ids_and_titles = modules_con.execute(
        "SELECT m.module_id_uni, m.name FROM modules m"
    ).fetchall()

    mpm_rows = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_emi_row = {
            executor.submit(
                process_emi_row, emi_row, all_module_ids_and_titles
            ): emi_row
            for emi_row in emi_rows
        }
        total_rows = len(emi_rows)
        completed_count = 0
        for future in as_completed(future_to_emi_row):
            result = future.result()
            if result:
                mpm_rows.append(result)
            completed_count += 1
            if completed_count % 25 == 0:
                print(f"{completed_count} | {total_rows}")
    return mpm_rows


def main():
    mpm_rows_ids = map_extracted_ids()
    mpm_rows_titles = map_extracted_titles()
    modules_con.executemany(
        "INSERT INTO module_prerequisite_mappings (module_id_uni, prereq_module_id_uni, extracted_module_identifier_id) VALUES (?,?,?)",
        mpm_rows_ids,
    )
    modules_con.executemany(
        "INSERT INTO module_prerequisite_mappings (module_id_uni, prereq_module_id_uni, extracted_module_identifier_id, score) VALUES (?,?,?, ?)",
        mpm_rows_titles,
    )
    modules_con.commit()


if __name__ == "__main__":
    main()
