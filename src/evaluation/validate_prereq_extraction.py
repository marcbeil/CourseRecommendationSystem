import sqlite3
import pandas as pd
from rapidfuzz import process, fuzz
import re
import roman
from prodigy.components.db import connect


def extract_numerals(text):
    arabic_numerals = re.findall(r"\d+", text)
    roman_numerals = re.findall(r"\b[I|V|X|L|C|D|M]+\b", text)
    roman_to_arabic = [str(roman.fromRoman(numeral)) for numeral in roman_numerals]
    return arabic_numerals + roman_to_arabic


def custom_scorer(a, b, score_cutoff=None):
    base_score = fuzz.token_sort_ratio(a, b)
    numbers_a = extract_numerals(a)
    numbers_b = extract_numerals(b)
    if numbers_a != numbers_b:
        base_score *= 0.5
    if score_cutoff is not None and base_score < score_cutoff:
        return 0
    return base_score


def calculate_tp_fp_fn(labeled, extracted, threshold=85):
    tp = 0
    fp = 0
    fn = 0
    labeled_set = set(labeled)
    extracted_set = set(extracted)
    for extracted_item in extracted_set:
        best_match = process.extractOne(
            extracted_item, labeled_set, scorer=custom_scorer, score_cutoff=threshold
        )
        if best_match and best_match[1] >= threshold:
            tp += 1
            labeled_set.remove(best_match[0])
        else:
            fp += 1
    fn = len(labeled_set)
    return tp, fp, fn


def extract_labels(prereq, label):
    text = prereq["text"]
    labels = []
    if prereq["spans"]:
        for span in prereq["spans"]:
            if span["label"] == label:
                identifier = text[span["start"] : span["end"]]
                labels.append(identifier)
    return labels


def get_test_set(db):
    test_set = db.get_dataset_examples("module_prerequisites_dataset")
    test_set = list(filter(lambda x: x["answer"] == "accept", test_set))
    return test_set


def get_extracted_data(modules_con, test_set_module_ids):
    placeholders = ",".join("?" for _ in test_set_module_ids)
    extracted_rows = modules_con.execute(
        f"SELECT module_id_uni, identifier, identifier_type FROM extracted_module_identifiers emi WHERE module_id_uni IN ({placeholders}) and exists(SELECT * FROM module_prerequisite_mappings mpm where emi.extracted_module_identifier_id = mpm.extracted_module_identifier_id and (score is null or score > 80))",
        tuple(test_set_module_ids),
    )
    extracted_data = {}
    for row in extracted_rows:
        module_id = row[0]
        identifier = row[1]
        identifier_type = row[2]
        if module_id not in extracted_data:
            extracted_data[module_id] = {"IDs": [], "TITLES": []}
        if identifier_type == "ID":
            extracted_data[module_id]["IDs"].append(identifier)
        elif identifier_type == "TITLE":
            extracted_data[module_id]["TITLES"].append(identifier)
    return extracted_data


def prepare_dataframe(test_set, extracted_data):
    data = {
        "module_id": [entry["meta"]["module_id_uni"] for entry in test_set],
        "text": [entry["text"] for entry in test_set],
        "labeled_ids": [extract_labels(entry, "ID") for entry in test_set],
        "labeled_titles": [extract_labels(entry, "TITLE") for entry in test_set],
        "extracted_ids": [
            extracted_data.get(entry["meta"]["module_id_uni"], {}).get("IDs", [])
            for entry in test_set
        ],
        "extracted_titles": [
            extracted_data.get(entry["meta"]["module_id_uni"], {}).get("TITLES", [])
            for entry in test_set
        ],
    }
    return pd.DataFrame(data)


def calculate_metrics(df):
    df["TP_ID"], df["FP_ID"], df["FN_ID"] = zip(
        *df.apply(
            lambda x: calculate_tp_fp_fn(x["labeled_ids"], x["extracted_ids"]), axis=1
        )
    )
    df["TP_TITLE"], df["FP_TITLE"], df["FN_TITLE"] = zip(
        *df.apply(
            lambda x: calculate_tp_fp_fn(x["labeled_titles"], x["extracted_titles"]),
            axis=1,
        )
    )
    TP_ID = df["TP_ID"].sum()
    FP_ID = df["FP_ID"].sum()
    FN_ID = df["FN_ID"].sum()
    TP_TITLE = df["TP_TITLE"].sum()
    FP_TITLE = df["FP_TITLE"].sum()
    FN_TITLE = df["FN_TITLE"].sum()
    precision_ID = TP_ID / (TP_ID + FP_ID) if (TP_ID + FP_ID) > 0 else 0
    recall_ID = TP_ID / (TP_ID + FN_ID) if (TP_ID + FN_ID) > 0 else 0
    accuracy_ID = TP_ID / (TP_ID + FP_ID + FN_ID) if (TP_ID + FP_ID + FN_ID) > 0 else 0
    precision_TITLE = (
        TP_TITLE / (TP_TITLE + FP_TITLE) if (TP_TITLE + FP_TITLE) > 0 else 0
    )
    recall_TITLE = TP_TITLE / (TP_TITLE + FN_TITLE) if (TP_TITLE + FN_TITLE) > 0 else 0
    accuracy_TITLE = (
        TP_TITLE / (TP_TITLE + FP_TITLE + FN_TITLE)
        if (TP_TITLE + FP_TITLE + FN_TITLE) > 0
        else 0
    )
    return {
        "ID": {"Precision": precision_ID, "Recall": recall_ID, "Accuracy": accuracy_ID},
        "TITLE": {
            "Precision": precision_TITLE,
            "Recall": recall_TITLE,
            "Accuracy": accuracy_TITLE,
        },
    }


def main():
    db = connect()
    test_set = get_test_set(db)
    test_set_module_ids = set(
        map(lambda prereq: prereq["meta"]["module_id_uni"], test_set)
    )
    modules_con = sqlite3.connect("../../resources/modules.db")
    extracted_data = get_extracted_data(modules_con, test_set_module_ids)
    df = prepare_dataframe(test_set, extracted_data)
    metrics = calculate_metrics(df)
    print(metrics)


if __name__ == "__main__":
    main()


# {'ID': {'Precision': 0.9727891156462585, 'Recall': 0.6941747572815534, 'Accuracy': 0.680952380952381}, 'TITLE': {'Precision': 0.6594360086767896, 'Recall': 0.6565874730021598, 'Accuracy': 0.49032258064516127}}
# {'ID': {'Precision': 0.9655172413793104, 'Recall': 0.9514563106796117, 'Accuracy': 0.92018779342723}, 'TITLE': {'Precision': 0.5341074020319303, 'Recall': 0.7948164146868251, 'Accuracy': 0.46938775510204084}}
# {'ID': {'Precision': 0.9727891156462585, 'Recall': 0.6941747572815534, 'Accuracy': 0.680952380952381}, 'TITLE': {'Precision': 0.6689655172413793, 'Recall': 0.6285097192224622, 'Accuracy': 0.4794069192751236}}
# {'ID': {'Precision': 0.9727891156462585, 'Recall': 0.6941747572815534, 'Accuracy': 0.680952380952381}, 'TITLE': {'Precision': 0.671875, 'Recall': 0.46436285097192226, 'Accuracy': 0.3785211267605634}}
