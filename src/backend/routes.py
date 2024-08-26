import logging
from functools import lru_cache
from typing import Dict
from rapidfuzz import fuzz

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import or_

from backend.db_models import Session, Module
from backend.module_filter import (
    apply_filters,
    modules_by_id,
)
from backend.module_ranker import rank_modules
from backend.student_input_extraction import extract_student_preferences
from backend.topic_mapper import VectorStore

load_dotenv()

app = Flask(__name__)
CORS(app)


vectorstore = VectorStore(max_size=100)


def add_reasoning(ranked_modules, paginated_modules):
    # Step 1: Create a mapping of module_id to reasoning
    reasoning_map = {module.module_id: module.reasoning for module in ranked_modules}

    # Step 2: Update paginated modules with the reasoning field
    for module in paginated_modules:
        module_id = module.get("id")
        if module_id in reasoning_map.keys():
            module["reasoning"] = reasoning_map[module_id]
        else:
            module["reasoning"] = (
                "No reasoning available"  # Optional: handle case where no reasoning is found
            )


@app.get("/modules")
def get_modules():
    # Extract query parameters for filtering and pagination
    study_level = request.args.get("studyLevel", "")
    ects_min = request.args.get("ectsRange[0]", type=int, default=1)
    ects_max = request.args.get("ectsRange[1]", type=int, default=30)
    languages = request.args.getlist("languages[]")
    departments = request.args.getlist("departments[]")
    topics_of_interest = request.args.getlist("topicsOfInterest[]")
    topics_to_exclude = request.args.getlist("topicsToExclude[]")
    previous_modules = request.args.getlist("previousModules[]")
    schools = request.args.getlist("schools[]")
    student_text = request.args.get("studentText", "")
    page = request.args.get("page", type=int, default=1)
    size = request.args.get("size", type=int, default=10)
    languages = tuple(languages) if languages else None
    departments = tuple(departments) if departments else None
    previous_modules = tuple(previous_modules) if previous_modules else None
    logging.info(f"TEST {previous_modules=}")
    topics_of_interest = tuple(topics_of_interest) if topics_of_interest else None
    topics_to_exclude = tuple(topics_to_exclude) if topics_to_exclude else None
    schools = tuple(schools) if schools else None
    # Call apply_filters with individual arguments
    filtered_modules = apply_filters(
        schools=schools,
        study_level=study_level,
        ects_min=ects_min,
        ects_max=ects_max,
        module_languages=languages,
        departments=departments,
        previous_modules=previous_modules,
        topics_of_interest=topics_of_interest,
        topics_to_exclude=topics_to_exclude,
    )
    # Implement pagination
    total_modules = len(filtered_modules)
    start = (page - 1) * size
    end = start + size
    paginated_modules = filtered_modules[start:end]
    # Calculate total pages
    total_pages = (total_modules + size - 1) // size
    logging.info(f"{student_text=}")
    if paginated_modules and student_text:
        ranked_modules = rank_modules(
            student_input=student_text,
            modules=str(paginated_modules),
        )
        add_reasoning(ranked_modules, paginated_modules)
    return jsonify(
        {
            "modules": paginated_modules,
            "totalPages": total_pages,
            "currentPage": page,
            "pageSize": size,
            "totalModules": total_modules,
        }
    )


@app.get("/modules-by-id")
def get_modules_by_id():
    module_ids = tuple(request.args.getlist("moduleIds[]"))
    modules = modules_by_id(module_ids=module_ids)
    return (
        jsonify(
            {
                "success": True,
                "modules": modules,
            }
        ),
        200,
    )


def get_topic_mappings(topic, k=1, threshold=0.1):
    topic_mappings = vectorstore.map_topic(topic, k=k, threshold=threshold)
    topic_mappings = [mapping.topic for mapping in topic_mappings]
    return topic_mappings


@app.route("/map-topic", methods=["GET"])
def map_topic():
    topic = request.args.get("topic")
    if not topic:
        return jsonify({"message": "Topic is required"}), 400

    threshold = request.args.get("threshold", default=0.5, type=float)
    max_mappings = request.args.get("maxMappings", default=3, type=int)

    topic_mappings = get_topic_mappings(topic, k=max_mappings, threshold=threshold)
    return jsonify({"topicMappings": topic_mappings}), 200


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


def post_process_prefs(prefs: Dict):
    new_topics_of_interest = {
        topic: get_topic_mappings(topic, k=3, threshold=0.5)
        for topic in prefs["topicsOfInterest"]
    }
    new_topics_to_exclude = {
        topic: get_topic_mappings(topic, k=3, threshold=0.5)
        for topic in prefs["topicsToExclude"]
    }
    prefs["topicsOfInterest"] = new_topics_of_interest
    prefs["topicsToExclude"] = new_topics_to_exclude
    session = Session()
    previous_module_ids_and_titles = (
        session.query(Module.module_id_uni, Module.name)
        .filter(Module.module_id_uni.in_(prefs["previousModuleIds"]))
        .all()
    )
    all_module_ids_and_titles = session.query(Module.module_id_uni, Module.name).all()
    session.close()
    previous_modules_matched = [
        {"id": module[0], "title": module[1]}
        for module in previous_module_ids_and_titles
    ]

    # map prefs["previousModuleIds"] to Module names in the database using the fuzzy method
    # Assume prefs["previousModules"] contains a list of module names extracted by LLM

    for extracted_module_name in prefs.get("previousModules", []):
        best_match = None
        highest_score = 0
        for module_id, module_name in all_module_ids_and_titles:
            score = compute_similarity_score(extracted_module_name, module_name)
            if score > highest_score and score > 70:
                highest_score = score
                best_match = {"id": module_id, "title": module_name}

        if best_match:
            previous_modules_matched.append(best_match)

    prefs["previousModules"] = previous_modules_matched
    return prefs


@app.get("/search-modules")
def search_modules():
    query = request.args.get("query", "")
    limit = request.args.get("limit", type=int, default=10)

    if not query:
        return jsonify({"modules": []})
    session = Session()
    # Assuming you are using a full-text search or similar fuzzy search capability
    search_results = (
        session.query(Module.module_id_uni, Module.name)
        .filter(
            or_(
                Module.module_id_uni.ilike(f"%{query}%"),
                Module.name.ilike(f"%{query}%"),
            )
        )
        .limit(limit)
        .all()
    )

    modules = [{"id": r[0], "title": r[1]} for r in search_results]
    return jsonify({"modules": modules})


@app.post("/start-extraction")
def start_extraction():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"success": False, "message": "Invalid input"}), 400

    student_input = data["text"]
    logging.info(f"Received input for extraction: {student_input}")

    try:
        prefs = extract_student_preferences(student_input=student_input)
        prefs_processed = post_process_prefs(prefs)
        logging.info(prefs_processed)
        return jsonify({"success": True, "filters": prefs_processed}), 200
    except Exception as e:
        logging.error(f"Error during extraction: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
