from sqlalchemy import create_engine, Table, Column, String, MetaData, select, cte, text
from sqlalchemy.orm import aliased
from sqlalchemy.sql import and_, not_
import logging

from course_recommender.topic_mapper_new import (
    _get_topics_with_embeddings,
    build_index,
    vector_similarity_search,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

from course_recommender.extraction_schema import StudentPreferences, StudyLevel

from db.models import Session, Module, Organisation, ModuleTopicMapping, Topic


def filter_modules(pref: StudentPreferences):
    session = Session()
    query = session.query(Module)
    filters = []

    log_template = "filter ({type}): {content}"

    if pref.module_languages:
        logging.info(
            log_template.format(type="language", content=pref.module_languages)
        )
        included_languages = [lang.value for lang in pref.module_languages]
        filters.append(Module.lang.in_(included_languages))

    if pref.study_level:
        logging.info(
            log_template.format(
                type="level", content=pref.study_level.get_level_filter()
            )
        )
        included_study_levels = pref.study_level.get_level_filter()
        filters.append(Module.level.in_(included_study_levels))

    if pref.school:
        logging.info(log_template.format(type="school", content=pref.school.value))
        filters.append(_filter_for_school(session, school_name=pref.school.value))

    if pref.previous_courses:
        logging.info(
            log_template.format(type="previous courses", content=pref.previous_courses)
        )
        filters.append(~Module.name.in_(pref.previous_courses))

    if filters:
        query = query.filter(and_(*filters))

    filtered_modules = query.all()
    session.close()
    return filtered_modules


def _get_all_organisations_for_school(session, school_name: str):
    school_id = (
        session.query(Organisation.org_id)
        .filter(Organisation.name == school_name)
        .filter(Organisation.org_type == "school")
        .scalar()
    )
    # Using a recursive CTE to filter modules based on school hierarchy
    org_hierarchy = aliased(Organisation, name="org_hierarchy")
    # anchor
    subquery = (
        session.query(org_hierarchy.org_id)
        .filter(org_hierarchy.org_id == school_id)
        .cte(recursive=True)
    )
    # recursive member
    filtered_organisations = subquery.union_all(
        session.query(org_hierarchy.org_id).join(
            subquery, org_hierarchy.parent_org_id == subquery.c.org_id
        )
    )

    return filtered_organisations


def _filter_for_school(session, school_name: str):
    school_organisation_ids = _get_all_organisations_for_school(
        session, school_name=school_name
    )
    school_filter = Module.org_id.in_(select(school_organisation_ids))
    return school_filter


# Example usage
pref = StudentPreferences(
    # module_languages={"English"},
    # study_level="Bachelor",
    school="Engineering and Design",
    # previous_courses={"Math 101", "CS 201"},
    topics_of_interest=["machine learning"],
)
filtered_modules = filter_modules(pref)

print(len(filtered_modules))

# print([m for m in filtered_modules])
