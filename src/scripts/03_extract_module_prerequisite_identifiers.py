# Goal is to extract module ids as well as titles out of the unstructured prerequisite texts.
import sqlite3
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from ratelimit import limits, sleep_and_retry

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os
import re

load_dotenv()
# Change to the appropriate directory
os.chdir("../../")
resources_path = "resources"


class ModuleIdentifiers(BaseModel):
    """Module identifiers (IDs or Titles) that were found in the provided text"""

    module_ids: List[str] = Field(
        description="Unique identifiers of modules that can be found in the text.Extract only if you are very sure. ID has to appear in the provided text. DO NOT make up IDs",
        examples=["WZ6407", "MA2504", "PH9101", "CH102012"],
    )
    module_titles: List[str] = Field(
        description="Module Names that can be found in the text. Sometimes the text states only knowledge is needed in a specific field. Please differentiate between module TITLES and KNOWLEDGE needed and ONLY extract titles. ",
        examples=[
            "Analysis 1",
            "Grundlagen der Informatik",
            "Mechanische und Thermische Verfahrenstechnik",
            "Lineare Algebra",
        ],
    )


@sleep_and_retry
@limits(calls=450, period=60)
def extract_module_ids_titles_llm(module_prerequisites: str) -> ModuleIdentifiers:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert extraction algorithm. "
                "You will receive excerpts from university module descriptions focusing on prerequisites for those courses. "
                "Your task is to extract identifiers (titles or IDs) of the modules that are mentioned in the text."
                "Only extract the relevant information as specified. "
                "If an attribute's value cannot be determined, return null for that attribute.",
            ),
            ("human", "{text}"),
        ]
    )

    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    runnable = prompt | llm.with_structured_output(schema=ModuleIdentifiers)

    return runnable.invoke(module_prerequisites)


def remove_all_whitespace(extracted_id):
    pattern = re.compile(r"\s+")
    return re.sub(pattern, "", extracted_id)


def extract_module_ids_regex(prereq):
    MODULE_ID_UNI_REGEX = r"(?:\W|^)([A-Z]{2,4}[0-9]{3,7}|BGU[0-9A-Z]{5,8}|MW[0-9A-Z]{5}|CH-C[0-9]{2}|BV[0-9]{6}T[0-9]|CS[0-9]{4}BOK|WZ[0-9]{4}BOK|CITHN[0-9]{4,5}|MGTHN[0-9]{4,5}|SG[0-9]{6}(?:e|a|BNB|BBB|VHB|v2)?)(?:\W|$)"
    prereq_ids = re.findall(MODULE_ID_UNI_REGEX, prereq)
    return prereq_ids


def check_module_id_format(extracted_module_id):
    MODULE_ID_UNI_REGEX = r"([A-Z]{2,4}[0-9]{3,7}|BGU[0-9A-Z]{5,8}|MW[0-9A-Z]{5}|CH-C[0-9]{2}|BV[0-9]{6}T[0-9]|CS[0-9]{4}BOK|WZ[0-9]{4}BOK|CITHN[0-9]{4,5}|MGTHN[0-9]{4,5}|SG[0-9]{6}(?:e|a|BNB|BBB|VHB|v2)?)"
    prereq_id = re.match(MODULE_ID_UNI_REGEX, extracted_module_id)
    return prereq_id is not None


def process_module(row):
    module_id_uni, prereq_unstructured = row[0], row[1]
    emi_rows = set()
    # Extract module IDs and titles using LLM
    module_identifiers_llm = extract_module_ids_titles_llm(
        module_prerequisites=prereq_unstructured
    )
    print(f"Raw LLM output for module {module_id_uni}: {module_identifiers_llm}")

    # Extracted IDs and titles from LLM
    extracted_ids_llm = module_identifiers_llm.module_ids
    extracted_titles_llm = module_identifiers_llm.module_titles

    # Update the set with extracted IDs
    emi_rows.update(
        [
            (module_id_uni, remove_all_whitespace(extracted_id), "ID")
            for extracted_id in extracted_ids_llm
            if check_module_id_format(extracted_id)
        ]
    )

    # Update the set with extracted titles
    emi_rows.update([(module_id_uni, title, "TITLE") for title in extracted_titles_llm])
    # Extracted IDs using regex
    extracted_ids_regex = extract_module_ids_regex(prereq_unstructured)

    # Update the set with regex extracted IDs
    emi_rows.update(
        [(module_id_uni, extracted_id, "ID") for extracted_id in extracted_ids_regex]
    )

    return emi_rows


def main():
    # Create a new database and execute the DDL script
    modules_con = sqlite3.connect(os.path.join(resources_path, "modules.db"))

    topic_rows = modules_con.execute(
        "SELECT module_id_uni, prereq from modules where prereq is not null and prereq != ''"
    ).fetchall()

    total_rows = len(topic_rows)
    print(f"Amount of rows to process: {total_rows}")

    processed_rows = 0

    # Use ThreadPoolExecutor to process modules in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_row = {
            executor.submit(process_module, row): row for row in topic_rows
        }

        for future in as_completed(future_to_row):
            row = future_to_row[future]
            try:
                emi_rows = future.result()
                print(f"{emi_rows=}")
                modules_con.executemany(
                    "INSERT OR IGNORE INTO extracted_module_identifiers (module_id_uni, identifier, identifier_type) VALUES (?, ?, ?)",
                    emi_rows,
                )

                modules_con.commit()

                processed_rows += 1
                print(f"Processed {processed_rows}/{total_rows} rows...")

            except Exception as e:
                print(f"Error processing module {row[0]}: {e}")

    print(f"All rows processed. Total: {processed_rows}/{total_rows}")
    modules_con.close()


if __name__ == "__main__":
    main()
