import logging
from typing import Dict

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import or_

from backend.db_models import Session, Module
from backend.module_filter import (
    apply_filters,
    modules_by_id,
)
from backend.student_input_extraction import extract_student_preferences
from backend.topic_mapper import VectorStore

load_dotenv()

app = Flask(__name__)
CORS(app)


vectorstore = VectorStore(max_size=2000)


@app.get("/modules")
def get_modules():
    # Extract query parameters for filtering and pagination
    school = request.args.get("school", "")
    study_level = request.args.get("studyLevel", "")
    ects_min = request.args.get("ectsRange[0]", type=int, default=1)
    ects_max = request.args.get("ectsRange[1]", type=int, default=30)
    languages = request.args.getlist("languages[]")
    departments = request.args.getlist("departments[]")
    topics_of_interest = request.args.getlist("topicsOfInterest[]")
    topics_to_exclude = request.args.getlist("topicsToExclude[]")
    previous_modules = request.args.getlist("previousModules[]")
    page = request.args.get("page", type=int, default=1)
    size = request.args.get("size", type=int, default=10)
    languages = tuple(languages) if languages else None
    departments = tuple(departments) if departments else None
    previous_modules = tuple(previous_modules) if previous_modules else None
    logging.info(f"{previous_modules=}")
    topics_of_interest = tuple(topics_of_interest) if topics_of_interest else None
    topics_to_exclude = tuple(topics_to_exclude) if topics_to_exclude else None
    # Call apply_filters with individual arguments
    filtered_modules = apply_filters(
        school_name=school,
        study_level=study_level,
        ects_min=ects_min,
        ects_max=ects_max,
        module_languages=languages,
        departments=departments,
        previous_modules=previous_modules,
        topics_of_interest=topics_of_interest,
        topics_to_exclude=topics_to_exclude,
    )
    logging.info(f"{page=}, {request.args.get("page")}")
    # Implement pagination
    total_modules = len(filtered_modules)
    start = (page - 1) * size
    end = start + size
    paginated_modules = filtered_modules[start:end]
    # Calculate total pages
    total_pages = (total_modules + size - 1) // size

    # Return the paginated and filtered modules with metadata
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
