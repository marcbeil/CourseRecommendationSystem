import logging
from functools import lru_cache
from typing import Dict
from rapidfuzz import fuzz
import re

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import or_, text

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
vectorstore = VectorStore()
MODULE_ID_UNI_PATTERN = re.compile(
    r"(?:\W|^)([A-Z]{2,4}[0-9]{3,7}|BGU[0-9A-Z]{5,8}|MW[0-9A-Z]{5}|CH-C[0-9]{2}|BV[0-9]{6}T[0-9]|CS[0-9]{4}BOK|WZ[0-9]{4}BOK|CITHN[0-9]{4,5}|MGTHN[0-9]{4,5}|SG[0-9]{6}(?:e|a|BNB|BBB|VHB|v2)?)(?:\W|$)"
)


def add_reasoning(module_ranks, modules):
    # Step 1: Create a mapping of module_id to reasoning
    reasoning_map = {module.module_id: module.reasoning for module in module_ranks}

    order_map = {module.module_id: index for index, module in enumerate(module_ranks)}

    modules.sort(key=lambda m: order_map.get(m["id"], float("inf")))

    # Step 2: Update paginated modules with the reasoning field
    for module in modules:
        module_id = module.get("id")
        if module_id in reasoning_map.keys():
            module["reasoning"] = reasoning_map[module_id]
        else:
            module["reasoning"] = None


def store_user_input(input):
    session = Session()
    session.execute(
        text("INSERT OR IGNORE INTO user_input(text) VALUES(:input)"),
        {"input": input},
    )
    session.commit()
    session.close()


@app.get("/modules")
def get_modules():
    """Fetch unranked modules based on filter parameters."""
    # Extract query parameters
    query_params = extract_query_params()

    # Fetch unranked modules
    paginated_modules, total_pages, total_modules = fetch_unranked_modules(query_params)
    return jsonify(
        {
            "modules": paginated_modules,
            "modulesRankedByLLM": None,  # Not used in this route
            "totalPages": total_pages,
            "currentPage": query_params["page"],
            "pageSize": query_params["size"],
            "totalModules": total_modules,
        }
    )


@app.get("/modules-ranked")
def get_modules_ranked():
    """Fetch ranked modules based on filter parameters and student text."""
    # Extract query parameters
    query_params = extract_query_params()

    # Fetch ranked modules
    paginated_modules, modules_ranked_by_llm, total_pages, total_modules = (
        fetch_ranked_modules(query_params)
    )

    return jsonify(
        {
            "modules": paginated_modules,
            "modulesRankedByLLM": modules_ranked_by_llm,
            "totalPages": total_pages,
            "currentPage": query_params["page"],
            "pageSize": query_params["size"],
            "totalModules": total_modules,
        }
    )


def fetch_unranked_modules(query_params):
    """Fetch and paginate unranked modules based on filter parameters."""
    # Separate filter parameters from others
    filter_params = {
        key: query_params[key]
        for key in [
            "schools",
            "study_level",
            "ects_min",
            "ects_max",
            "digital_score_min",
            "digital_score_max",
            "module_languages",
            "departments",
            "previous_modules",
            "topics_of_interest",
            "excluded_topics",
        ]
    }

    # Apply filters to fetch modules
    filtered_modules = apply_filters(**filter_params)

    # Paginate the filtered modules
    paginated_modules, total_pages, total_modules = paginate(
        filtered_modules, query_params["page"], query_params["size"]
    )

    return paginated_modules, total_pages, total_modules


def fetch_ranked_modules(query_params):
    """Fetch, rank, and paginate modules based on filter parameters and student text."""
    # Fetch a larger set of unranked modules first to ensure there are enough for ranking
    original_page_size = query_params["size"]
    larger_page_size = max(
        query_params["size"], 20
    )  # Ensure at least 40 modules are fetched
    query_params["size"] = larger_page_size

    # Fetch unranked modules with a larger page size
    all_modules, _, total_modules = fetch_unranked_modules(query_params)
    print(len(all_modules))
    # If student text is provided, rank the modules using LLM
    modules_ranked_by_llm = None
    if all_modules and query_params["student_text"]:
        store_user_input(query_params["student_text"])

        modules_filtererd_fields = [
            {
                key: module[key]
                for key in [
                    "id",
                    "title",
                    "description",
                    "prereq",
                    "ects",
                    "language",
                    "studyLevel",
                    "chair",
                    "department",
                    "school",
                ]
            }
            for module in all_modules
        ]

        # Use all fetched modules for ranking to optimize performance
        module_ranks = rank_modules(
            student_input=query_params["student_text"],
            modules=tuple(
                frozenset(
                    (k, tuple(v) if isinstance(v, list) else v)
                    for k, v in module.items()
                )
                for module in modules_filtererd_fields
            ),
        )
        if module_ranks:
            # Add reasoning to the ranked modules
            add_reasoning(module_ranks, all_modules)
            print(f"{module_ranks=}")
            # Paginate the ranked modules after adding reasoning
            paginated_modules, total_pages, _ = paginate(
                all_modules, query_params["page"], original_page_size
            )
            modules_ranked_by_llm = paginated_modules
        else:
            paginated_modules, total_pages, _ = paginate(
                all_modules, query_params["page"], original_page_size
            )
    else:
        # No ranking needed, paginate the unranked modules
        paginated_modules, total_pages, _ = paginate(
            all_modules, query_params["page"], original_page_size
        )

    return paginated_modules, modules_ranked_by_llm, total_pages, total_modules


def extract_query_params():
    """Extracts and processes query parameters for filtering and pagination."""
    ects_range = request.args.getlist("ectsRange[]", type=int)
    digital_score_range = request.args.getlist("digitalScoreRange[]", type=int)
    return {
        "study_level": request.args.get("studyLevel", ""),
        "ects_min": ects_range[0] if len(ects_range) > 0 else 0,
        "ects_max": ects_range[1] if len(ects_range) > 1 else 30,
        "digital_score_min": (
            digital_score_range[0] if len(digital_score_range) > 0 else 0
        ),
        "digital_score_max": (
            digital_score_range[1] if len(digital_score_range) > 1 else 3
        ),
        "module_languages": tuple(request.args.getlist("languages[]")),
        "departments": tuple(request.args.getlist("departments[]")),
        "previous_modules": tuple(request.args.getlist("previousModules[]")),
        "topics_of_interest": tuple(request.args.getlist("topicsOfInterest[]")),
        "excluded_topics": tuple(request.args.getlist("excludedTopics[]")),
        "schools": tuple(request.args.getlist("schools[]")),
        "student_text": request.args.get("studentText", ""),
        "page": request.args.get("page", type=int, default=1),
        "size": request.args.get("size", type=int, default=5),
    }


def paginate(filtered_modules, page, size):
    """Paginates the filtered modules list."""
    total_modules = len(filtered_modules)
    start = (page - 1) * size
    end = start + size
    paginated_modules = filtered_modules[start:end]
    total_pages = (total_modules + size - 1) // size
    return paginated_modules, total_pages, total_modules


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


def get_topic_mappings(topic, k=30, threshold=0.23):
    topic_mappings = vectorstore.map_topic(topic, k=k, threshold=threshold)
    topic_mappings = [mapping.topic for mapping in topic_mappings]
    return topic_mappings


@app.route("/map-topic", methods=["GET"])
def map_topic():
    topic = request.args.get("topic")
    if not topic:
        return jsonify({"message": "Topic is required"}), 400

    # threshold = request.args.get("threshold", default=0.23, type=float)
    threshold = request.args.get("threshold", default=0.5, type=float)
    max_mappings = request.args.get("maxMappings", default=100, type=int)
    topic_mappings = get_topic_mappings(topic, k=max_mappings, threshold=threshold)
    print(topic_mappings)
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


@app.get("/search-modules")
def search_modules():
    query = request.args.get("query", "")
    limit = request.args.get("limit", type=int, default=10)

    if not query:
        return jsonify({"modules": []})

    session = Session()
    is_id = bool(MODULE_ID_UNI_PATTERN.search(query))

    if is_id:
        # Perform traditional LIKE search on the module_id_uni field if the query is an ID
        search_results = session.execute(
            text(
                f"SELECT module_id_uni, name FROM modules WHERE module_id_uni LIKE :query LIMIT :limit"
            ),
            {"query": f"%{query}%", "limit": limit},
        ).fetchall()
    else:
        # Perform FTS5 search on the name field if the query is not an ID
        search_results = session.execute(
            text(
                f"SELECT module_id_uni, name FROM module_fts WHERE name MATCH :query LIMIT :limit"
            ),
            {"query": query, "limit": limit},
        ).fetchall()

        # Format the results for JSON response
    modules = [{"id": r[0], "title": r[1]} for r in search_results]
    return jsonify({"modules": modules})


@app.post("/start-extraction")
def start_extraction():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"success": False, "message": "Invalid input"}), 400

    student_input = data["text"]
    logging.info(f"Received input for extraction: {student_input}")

    prefs_processed = extract_and_process_user_preferences(student_input=student_input)
    logging.info(prefs_processed)
    return jsonify({"success": True, "filters": prefs_processed}), 200
    # return jsonify({"success": False, "message": str(e)}), 500


@lru_cache
def extract_and_process_user_preferences(student_input):
    prefs = extract_student_preferences(student_input=student_input)
    logging.info("Parsing extracted prefs ...")
    prefs_processed = post_process_prefs(prefs)
    return prefs_processed


def post_process_prefs(prefs: Dict):
    new_topics_of_interest = {
        topic: get_topic_mappings(topic, k=30, threshold=0.23)
        for topic in prefs["topicsOfInterest"]
    }
    new_topics_to_exclude = {
        topic: get_topic_mappings(topic, k=10, threshold=0.15)
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

    if not prefs["languages"]:
        prefs["languages"] = ["English", "German", "Other"]
    return prefs


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
