import csv
import json
from collections import Counter


def calculate_metrics(expected, actual):
    expected_set = set(expected)
    actual_set = set(actual)

    if len(expected_set) == 0 and len(actual_set) == 0:
        return 1, 1, 1
    # Precision: What fraction of the predicted items are correct
    if len(actual_set) > 0:
        precision = len(expected_set & actual_set) / len(actual_set)
    else:
        precision = 0

    # Recall: What fraction of the true items were found
    if len(expected_set) > 0:
        recall = len(expected_set & actual_set) / len(expected_set)
    else:
        recall = 0

    # Accuracy: What fraction of all possible predictions are correct
    accuracy = len(expected_set & actual_set) / len(expected_set | actual_set)

    return precision, recall, accuracy


def calculate_all_metrics(user_input):
    aggregated_metrics = {}
    total_fields = Counter()  # Track how many times each field was present

    total_precision = 0
    total_recall = 0
    total_accuracy = 0
    num_fields = 0  # Total number of evaluated fields

    for user_data in user_input:
        expected_prefs = user_data["prefs_expected"]
        actual_prefs = user_data["prefs_actual"]

        # Loop through fields in expected prefs
        for field in expected_prefs:
            expected_value = expected_prefs[field]
            actual_value = actual_prefs.get(field)

            # If field is a list (e.g., schools, departments, topicsOfInterest), calculate metrics using set logic
            if isinstance(expected_value, list):
                precision, recall, accuracy = calculate_metrics(
                    expected_value, actual_value
                )

            # If field is a dictionary (e.g., departments), calculate metrics for each sub-field
            elif isinstance(expected_value, dict):
                precision, recall, accuracy = 0, 0, 0
                if len(expected_value) > 0:  # Avoid zero division
                    for sub_key in expected_value:
                        sub_precision, sub_recall, sub_accuracy = calculate_metrics(
                            expected_value[sub_key], actual_value.get(sub_key, [])
                        )
                        precision += sub_precision
                        recall += sub_recall
                        accuracy += sub_accuracy
                    precision /= len(expected_value)
                    recall /= len(expected_value)
                    accuracy /= len(expected_value)
                else:
                    precision, recall, accuracy = (
                        1,
                        1,
                        1,
                    )  # If no sub-keys, perfect scores

            # If field is a scalar value (e.g., studyLevel, ectsMin), compare directly
            else:
                precision = 1 if expected_value == actual_value else 0
                recall = 1 if expected_value == actual_value else 0
                accuracy = 1 if expected_value == actual_value else 0

            # Accumulate the metrics for this field
            if field not in aggregated_metrics:
                aggregated_metrics[field] = {"precision": 0, "recall": 0, "accuracy": 0}

            aggregated_metrics[field]["precision"] += precision
            aggregated_metrics[field]["recall"] += recall
            aggregated_metrics[field]["accuracy"] += accuracy
            total_fields[field] += 1  # Track how many times we evaluate this field

            # Accumulate total precision, recall, accuracy for overall calculation
            total_precision += precision
            total_recall += recall
            total_accuracy += accuracy
            num_fields += 1  # Increase field count for averaging

    # Compute the averages for each field
    for field in aggregated_metrics:
        count = total_fields[field]
        aggregated_metrics[field]["precision"] /= count
        aggregated_metrics[field]["recall"] /= count
        aggregated_metrics[field]["accuracy"] /= count

    # Compute overall aggregated precision, recall, and accuracy
    if num_fields > 0:
        overall_precision = total_precision / num_fields
        overall_recall = total_recall / num_fields
        overall_accuracy = total_accuracy / num_fields
    else:
        overall_precision, overall_recall, overall_accuracy = 0, 0, 0

    # Add overall aggregated metrics to the result
    aggregated_metrics["aggregated"] = {
        "precision": overall_precision,
        "recall": overall_recall,
        "accuracy": overall_accuracy,
    }

    return aggregated_metrics


def write_metrics_to_csv(metrics, file_path):
    # Write metrics to a CSV file
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Field", "Precision", "Recall", "Accuracy"])

        for field, field_metrics in metrics.items():
            writer.writerow(
                [
                    field,
                    field_metrics["precision"],
                    field_metrics["recall"],
                    field_metrics["accuracy"],
                ]
            )


# Example usage with your JSON data
with open("evaluation_set.json", "r") as file:
    user_input_data = json.load(file)


aggregated_results = calculate_all_metrics(user_input_data)

# Write the aggregated results to CSV
csv_file_path = "student_input_evaluation.csv"
write_metrics_to_csv(aggregated_results, csv_file_path)

print(f"Metrics have been written to {csv_file_path}")
print(f"Aggregated Results:\n{aggregated_results}")

# aggregated,0.9248214285714285,0.9220982142857143,0.9142212301587301

# {'studyLevel': {'precision': 0.9166666666666666, 'recall': 0.9166666666666666, 'accuracy': 0.9166666666666666}, 'schools': {'precision': 0.9166666666666666, 'recall': 0.8958333333333334, 'accuracy': 0.8541666666666666}, 'departments': {'precision': 0.875, 'recall': 0.875, 'accuracy': 0.875}, 'ectsMin': {'precision': 0.9583333333333334, 'recall': 0.9583333333333334, 'accuracy': 0.9583333333333334}, 'ectsMax': {'precision': 1.0, 'recall': 1.0, 'accuracy': 1.0}, 'topicsOfInterest': {'precision': 0.8270833333333334, 'recall': 0.797371031746032, 'accuracy': 0.7512400793650794}, 'topicsToExclude': {'precision': 0.9583333333333334, 'recall': 0.9583333333333334, 'accuracy': 0.9583333333333334}, 'previousModules': {'precision': 1.0, 'recall': 1.0, 'accuracy': 1.0}, 'previousModuleIds': {'precision': 1.0, 'recall': 1.0, 'accuracy': 1.0}, 'languages': {'precision': 0.7916666666666666, 'recall': 0.7916666666666666, 'accuracy': 0.7916666666666666}, 'aggregated': {'precision': 0.924375, 'recall': 0.9193204365079366, 'accuracy': 0.9105406746031746}}
