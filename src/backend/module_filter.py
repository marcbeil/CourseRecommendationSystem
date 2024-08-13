from functools import lru_cache
from sqlalchemy import (
    func,
    distinct,
)
from sqlalchemy.orm import aliased
from sqlalchemy.sql import and_


import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

from backend.models import (
    Session,
    Module,
    Organisation,
    ModuleTopicMapping,
    Topic,
    ModulePrerequisiteMapping,
)


@lru_cache
def modules_by_id(module_ids):
    if not module_ids:
        return []
    logging.info(f"{module_ids=}")
    session = Session()
    modules = (
        session.query(Module.module_id_uni, Module.name)
        .filter(Module.module_id_uni.in_(module_ids))
        .all()
    )
    modules_dict = [
        {
            "id": r[0],
            "title": r[1],
        }
        for r in modules
    ]
    session.close()
    return modules_dict


@lru_cache
def apply_filters(
    school_name=None,
    study_level=None,
    ects_min=None,
    ects_max=None,
    module_languages=None,
    departments=None,
    previous_modules=None,
    topics_of_interest=None,
    topics_to_exclude=None,
):
    session = Session()
    department = aliased(Organisation)
    school = aliased(Organisation)

    # Base query
    query = (
        session.query(
            Module.module_id_uni,
            Module.name,
            Module.description,
            Module.prereq,
            Module.digital_score,
            Module.ects,
            Module.lang,
            Module.level,
            Module.org_id,
            Organisation.name.label("organisation"),
            department.name.label("department"),
            school.name.label("school"),
            func.group_concat(distinct(Topic.topic)).label("topics"),
            func.group_concat(
                distinct(ModulePrerequisiteMapping.prereq_module_id_uni)
            ).label("prereqModules"),
        )
        .outerjoin(Organisation, Module.org_id == Organisation.org_id)
        .outerjoin(department, Organisation.dep_id == department.org_id)
        .outerjoin(school, Organisation.school_id == school.org_id)
        .join(ModuleTopicMapping, Module.module_id == ModuleTopicMapping.module_id)
        .join(Topic, ModuleTopicMapping.topic_id == Topic.topic_id)
        .outerjoin(
            ModulePrerequisiteMapping,
            ModulePrerequisiteMapping.module_id_uni == Module.module_id_uni,
        )
    )

    filters = []

    if module_languages:
        filters.append(Module.lang.in_(module_languages))

    if study_level:
        filters.append(Module.level == study_level)

    if ects_min is not None:
        filters.append(Module.ects >= ects_min)

    if ects_max is not None:
        filters.append(Module.ects <= ects_max)

    if school_name:
        school_id = (
            session.query(Organisation.org_id)
            .filter(Organisation.name == school_name)
            .scalar()
        )
        if school_id:
            filters.append(Organisation.school_id == school_id)

    if departments:
        filters.append(department.org_id.in_(departments))
    if previous_modules:
        logging.info(f"{previous_modules=}")
        previous_module_exists = (
            session.query(ModulePrerequisiteMapping)
            .filter(
                and_(
                    ModulePrerequisiteMapping.module_id_uni == Module.module_id_uni,
                    ModulePrerequisiteMapping.prereq_module_id_uni.in_(
                        previous_modules
                    ),
                )
            )
            .correlate(Module)
            .exists()
        )
        filters.append(previous_module_exists)

    if topics_of_interest:
        topic_exists = (
            session.query(Topic.topic_id)
            .filter(
                and_(
                    Module.module_id == ModuleTopicMapping.module_id,
                    ModuleTopicMapping.topic_id == Topic.topic_id,
                    Topic.topic.in_(topics_of_interest),
                )
            )
            .correlate(Module)
            .exists()
        )
        filters.append(topic_exists)

    if topics_to_exclude:
        filters.append(~Topic.topic.in_(topics_to_exclude))

    # Apply filters only if they exist
    if filters:
        query = query.filter(and_(*filters))

    # Execute the query
    filtered_modules = query.group_by(
        Module.module_id, Organisation.name, department.name, school.name
    ).all()

    module_dicts = [
        {
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "prereq": r[3],
            "digitalScore": r[4],
            "ects": r[5],
            "language": r[6],
            "studyLevel": r[7],
            "OrgId": r[8],
            "chair": r[9],
            "department": r[10],
            "school": r[11],
            "topics": r[12].split(",") if r[12] else [],
            "prereqModules": r[13].split(",") if r[13] else [],
        }
        for r in filtered_modules
    ]
    session.close()
    return module_dicts
