import math
import sqlite3
import pandas as pd
from rapidfuzz import process, fuzz
import re
import roman
from prodigy.components.db import connect
import matplotlib.pyplot as plt


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


def get_extracted_data(modules_con, test_set_module_ids, score_threshold):
    placeholders = ",".join("?" for _ in test_set_module_ids)
    extracted_rows = modules_con.execute(
        f"SELECT module_id_uni, identifier, identifier_type FROM extracted_module_identifiers emi WHERE module_id_uni IN ({placeholders}) and exists(SELECT * FROM module_prerequisite_mappings mpm where emi.extracted_module_identifier_id = mpm.extracted_module_identifier_id and (score is null or score > {score_threshold}))",
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


def prepare_dataframe(test_set, extracted_data, module_school_df=None):
    if module_school_df is not None:
        module_school_dict = module_school_df.set_index("module_id_uni")[
            "school_name"
        ].to_dict()
        schools = [
            module_school_dict.get(entry["meta"]["module_id_uni"], "Unknown")
            for entry in test_set
        ]
    else:
        schools = [None] * len(test_set)

    data = {
        "module_id": [entry["meta"]["module_id_uni"] for entry in test_set],
        "school": schools,
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
        "ID": {
            "Precision": precision_ID,
            "Recall": recall_ID,
            "Accuracy": accuracy_ID,
        },
        "TITLE": {
            "Precision": precision_TITLE,
            "Recall": recall_TITLE,
            "Accuracy": accuracy_TITLE,
        },
        "COMBINED": {
            "Precision": (precision_TITLE + precision_ID) * 0.5,
            "Recall": (recall_TITLE + recall_ID) * 0.5,
            "Accuracy": (accuracy_TITLE + accuracy_ID) * 0.5,
        },
    }


def calculate_metrics_by_school(df):
    if "school" not in df.columns or df["school"].isnull().all():
        raise ValueError("School information is missing in the DataFrame.")

    school_metrics = {}
    grouped = df.groupby("school")

    for school_name, group_df in grouped:
        # Calculate TP, FP, FN for each group
        metrics = calculate_metrics(group_df)
        school_metrics[school_name] = metrics
    return school_metrics


def metrics_for_score_threshold(score_threshold=0):
    db = connect()
    test_set = get_test_set(db)
    test_set_module_ids = set(
        map(lambda prereq: prereq["meta"]["module_id_uni"], test_set)
    )
    modules_con = sqlite3.connect("../../resources/modules.db")

    extracted_data = get_extracted_data(
        modules_con, test_set_module_ids, score_threshold=score_threshold
    )
    df = prepare_dataframe(test_set, extracted_data)

    # Calculate TP, FP, FN for each row
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
    metrics = calculate_metrics(df)
    return metrics


def metrics_for_score_threshold_by_school(score_threshold=0):
    db = connect()
    test_set = get_test_set(db)
    test_set_module_ids = set(
        map(lambda prereq: prereq["meta"]["module_id_uni"], test_set)
    )
    modules_con = sqlite3.connect("../../resources/modules.db")

    # Get module-school mapping
    module_school_df = get_module_school_mapping(modules_con)

    extracted_data = get_extracted_data(
        modules_con, test_set_module_ids, score_threshold=score_threshold
    )
    df = prepare_dataframe(test_set, extracted_data, module_school_df)

    # Calculate TP, FP, FN for each row
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

    # Calculate metrics by school
    school_metrics = calculate_metrics_by_school(df)
    return school_metrics


def plot_metrics_over_thresholds(thresholds, group_by=None):
    metrics_dict = {}  # {threshold: metrics}

    for threshold in thresholds:
        if group_by == "school":
            # Use the new function
            metrics = metrics_for_score_threshold_by_school(score_threshold=threshold)
        else:
            # Use the existing function
            metrics = metrics_for_score_threshold(score_threshold=threshold)
        metrics_dict[threshold] = metrics

    if group_by == "school":
        # Extract list of schools
        schools = set()
        for metrics in metrics_dict.values():
            schools.update(metrics.keys())
        schools = list(schools)

        for school in schools:
            precision_ids = []
            recall_ids = []
            accuracy_ids = []

            precision_titles = []
            recall_titles = []
            accuracy_titles = []

            combined_precisions = []
            combined_recalls = []
            combined_accuracies = []

            for threshold in thresholds:
                metrics = metrics_dict[threshold]
                school_metrics = metrics.get(school)
                if school_metrics:
                    id_metrics = school_metrics["ID"]
                    title_metrics = school_metrics["TITLE"]
                    combined_metrics = school_metrics["COMBINED"]

                    precision_ids.append(id_metrics["Precision"])
                    recall_ids.append(id_metrics["Recall"])
                    accuracy_ids.append(id_metrics["Accuracy"])

                    precision_titles.append(title_metrics["Precision"])
                    recall_titles.append(title_metrics["Recall"])
                    accuracy_titles.append(title_metrics["Accuracy"])

                    combined_precisions.append(combined_metrics["Precision"])
                    combined_recalls.append(combined_metrics["Recall"])
                    combined_accuracies.append(combined_metrics["Accuracy"])
                else:
                    # If metrics are missing for this school at this threshold, append zeros
                    precision_ids.append(0)
                    recall_ids.append(0)
                    accuracy_ids.append(0)

                    precision_titles.append(0)
                    recall_titles.append(0)
                    accuracy_titles.append(0)

                    combined_precisions.append(0)
                    combined_recalls.append(0)
                    combined_accuracies.append(0)

            # Plot metrics for this school
            plt.figure(figsize=(15, 5))

            # Plot for IDs
            plt.subplot(1, 3, 1)
            plt.plot(thresholds, precision_ids, label="Precision", marker="o")
            plt.plot(thresholds, recall_ids, label="Recall", marker="x")
            plt.plot(thresholds, accuracy_ids, label="Accuracy", marker="s")
            plt.title(f"Metrics for IDs - {school}")
            plt.xlabel("Threshold")
            plt.ylabel("Metric Value")
            plt.legend()
            plt.grid(True)

            # Plot for Titles
            plt.subplot(1, 3, 2)
            plt.plot(thresholds, precision_titles, label="Precision", marker="o")
            plt.plot(thresholds, recall_titles, label="Recall", marker="x")
            plt.plot(thresholds, accuracy_titles, label="Accuracy", marker="s")
            plt.title(f"Metrics for Titles - {school}")
            plt.xlabel("Threshold")
            plt.ylabel("Metric Value")
            plt.legend()
            plt.grid(True)

            # Plot for Combined Metrics
            plt.subplot(1, 3, 3)
            plt.plot(thresholds, combined_precisions, label="Precision", marker="o")
            plt.plot(thresholds, combined_recalls, label="Recall", marker="x")
            plt.plot(thresholds, combined_accuracies, label="Accuracy", marker="s")
            plt.title(f"Combined Metrics - {school}")
            plt.xlabel("Threshold")
            plt.ylabel("Metric Value")
            plt.legend()
            plt.grid(True)

            plt.tight_layout()
            plt.show()
    else:
        # Existing plotting code
        precision_ids = []
        recall_ids = []
        accuracy_ids = []

        precision_titles = []
        recall_titles = []
        accuracy_titles = []

        combined_precisions = []
        combined_recalls = []
        combined_accuracies = []

        for threshold in thresholds:
            metrics = metrics_dict[threshold]
            id_metrics = metrics["ID"]
            title_metrics = metrics["TITLE"]
            combined_metrics = metrics["COMBINED"]

            precision_ids.append(id_metrics["Precision"])
            recall_ids.append(id_metrics["Recall"])
            accuracy_ids.append(id_metrics["Accuracy"])

            precision_titles.append(title_metrics["Precision"])
            recall_titles.append(title_metrics["Recall"])
            accuracy_titles.append(title_metrics["Accuracy"])

            combined_precisions.append(combined_metrics["Precision"])
            combined_recalls.append(combined_metrics["Recall"])
            combined_accuracies.append(combined_metrics["Accuracy"])

        plt.figure(figsize=(15, 5))

        # Plot for IDs
        plt.subplot(1, 3, 1)
        plt.plot(thresholds, precision_ids, label="Precision", marker="o")
        plt.plot(thresholds, recall_ids, label="Recall", marker="x")
        plt.plot(thresholds, accuracy_ids, label="Accuracy", marker="s")
        plt.title("Metrics for IDs")
        plt.xlabel("Threshold")
        plt.ylabel("Metric Value")
        plt.legend()
        plt.grid(True)

        # Plot for Titles
        plt.subplot(1, 3, 2)
        plt.plot(thresholds, precision_titles, label="Precision", marker="o")
        plt.plot(thresholds, recall_titles, label="Recall", marker="x")
        plt.plot(thresholds, accuracy_titles, label="Accuracy", marker="s")
        plt.title("Metrics for Titles")
        plt.xlabel("Threshold")
        plt.ylabel("Metric Value")
        plt.legend()
        plt.grid(True)

        # Plot for Combined Metrics
        plt.subplot(1, 3, 3)
        plt.plot(thresholds, combined_precisions, label="Precision", marker="o")
        plt.plot(thresholds, combined_recalls, label="Recall", marker="x")
        plt.plot(thresholds, combined_accuracies, label="Accuracy", marker="s")
        plt.title("Combined Metrics")
        plt.xlabel("Threshold")
        plt.ylabel("Metric Value")
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
        plt.show()


def get_module_school_mapping(modules_con):
    query = """
    SELECT
        m.module_id_uni,
        COALESCE(o_school.name, 'Unknown') AS school_name
    FROM
        modules m
    INNER JOIN
        organisations o ON m.org_id = o.org_id
    LEFT JOIN
        organisations o_school ON o.school_id = o_school.org_id
    """
    module_school_df = pd.read_sql_query(query, modules_con)
    return module_school_df


def save_metrics_to_csv(thresholds, group_by=None, output_dir="metrics_data"):
    import os

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    metrics_dict = {}  # {threshold: metrics}

    for threshold in thresholds:
        if group_by == "school":
            metrics = metrics_for_score_threshold_by_school(score_threshold=threshold)
        else:
            metrics = metrics_for_score_threshold(score_threshold=threshold)
        metrics_dict[threshold] = metrics

    if group_by == "school":
        # Extract list of schools
        schools = set()
        for metrics in metrics_dict.values():
            schools.update(metrics.keys())
        schools = list(schools)

        for school in schools:
            data_rows = []
            for threshold in thresholds:
                metrics = metrics_dict[threshold]
                school_metrics = metrics.get(school)
                if school_metrics:
                    id_metrics = school_metrics["ID"]
                    title_metrics = school_metrics["TITLE"]
                    combined_metrics = school_metrics["COMBINED"]
                else:
                    # If metrics are missing for this school at this threshold, set metrics to zero
                    id_metrics = {"Precision": 0, "Recall": 0, "Accuracy": 0}
                    title_metrics = {"Precision": 0, "Recall": 0, "Accuracy": 0}
                    combined_metrics = {"Precision": 0, "Recall": 0, "Accuracy": 0}

                data_row = {
                    "Threshold": threshold,
                    "ID_Precision": id_metrics["Precision"],
                    "ID_Recall": id_metrics["Recall"],
                    "ID_Accuracy": id_metrics["Accuracy"],
                    "Title_Precision": title_metrics["Precision"],
                    "Title_Recall": title_metrics["Recall"],
                    "Title_Accuracy": title_metrics["Accuracy"],
                    "Combined_Precision": combined_metrics["Precision"],
                    "Combined_Recall": combined_metrics["Recall"],
                    "Combined_Accuracy": combined_metrics["Accuracy"],
                }
                data_rows.append(data_row)
            # Save data_rows to CSV file
            df = pd.DataFrame(data_rows)
            # Replace spaces or special characters in school name for file name
            school_file_name = "".join(
                e for e in school if e.isalnum() or e == "_"
            ).rstrip()
            csv_file_path = os.path.join(output_dir, f"metrics_{school_file_name}.csv")
            df.to_csv(csv_file_path, index=False)
            print(f"Saved metrics for {school} to {csv_file_path}")
    else:
        data_rows = []
        for threshold in thresholds:
            metrics = metrics_dict[threshold]
            id_metrics = metrics["ID"]
            title_metrics = metrics["TITLE"]
            combined_metrics = metrics["COMBINED"]

            data_row = {
                "Threshold": threshold,
                "ID_Precision": id_metrics["Precision"],
                "ID_Recall": id_metrics["Recall"],
                "ID_Accuracy": id_metrics["Accuracy"],
                "Title_Precision": title_metrics["Precision"],
                "Title_Recall": title_metrics["Recall"],
                "Title_Accuracy": title_metrics["Accuracy"],
                "Combined_Precision": combined_metrics["Precision"],
                "Combined_Recall": combined_metrics["Recall"],
                "Combined_Accuracy": combined_metrics["Accuracy"],
            }
            data_rows.append(data_row)
        # Save data_rows to CSV file
        df = pd.DataFrame(data_rows)
        csv_file_path = os.path.join(output_dir, "prerequisite_mappings.csv")
        df.to_csv(csv_file_path, index=False)
        print(f"Saved overall metrics to {csv_file_path}")
