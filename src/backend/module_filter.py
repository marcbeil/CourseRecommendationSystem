import itertools
from functools import lru_cache
from sqlalchemy import (
    func,
    distinct,
    or_,
)
from sqlalchemy.orm import aliased
from sqlalchemy.sql import and_


import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

from backend.db_models import (
    Session,
    Module,
    Organisation,
    ModuleTopicMapping,
    Topic,
    ModulePrerequisiteMapping,
)


language_mapper = {
    "English": ("English", "German/English", "Unknown"),
    "German": ("German", "German/English", "Unknown"),
    "Other": ("Other", "Unknown"),
}

study_level_mapper = {
    "Bachelor": ("Bachelor", "Bachelor/Master", "Unknown"),
    "Master": ("Bachelor/Master", "Unknown", "Master"),
    "Other": ("Bachelor/Master", "Unknown", "Master", "Bachelor"),
}

school_mapper = {
    "Computation, Information and Technology": "TUS1000",
    "Engineering and Design": "TUS2000",
    "Life Sciences": "TUS4000",
    "Management": "TUS6000",
    "Medicine and Health": "TUS5000",
    "Natural Sciences": "TUS3000",
    "Social Sciences and Technology": "TUS7000",
}

department_mapper = {
    "Department Mathematics": "TUS1DP1",
    "Department Computer Science": "TUS1DP2",
    "Department Computer Engineering": "TUS1DP3",
    "Department Electrical Engineering": "TUS1DP4",
    "Department Aerospace and Geodesy": "TUS2DP1",
    "Department Architecture": "TUS2DP2",
    "Department Civil and Environmental Engineering": "TUS2DP3",
    "Department Energy and Process Engineering": "TUS2DP8",
    "Department Engineering Physics and Computation": "TUS2DP4",
    "Department Materials Engineering": "TUS2DP7",
    "Department Mechanical Engineering": "TUS2DP6",
    "Department Mobility Systems Engineering": "TUS2DP5",
    "Department Molecular Life Sciences": "TUS4DP1",
    "Department Life Science Engineering": "TUS4DP2",
    "Department Life Science Systems": "TUS4DP3",
    "Department Economics and Policy": "TUS6DP1",
    "Department Finance and Accounting": "TUS6DP2",
    "Department Innovation and Entrepreneurship": "TUS6DP3",
    "Department Marketing, Strategy and Leadership": "TUS6DP4",
    "Department Operations and Technology": "TUS6DP5",
    "Department Health and Sport Sciences": "TUS5DP1",
    "Department Preclinical Medicine": "TUS5DP2",
    "Department Clinical Medicine": "TUS5DP3",
    "Department Physics": "TUS3DP1",
    "Department Bioscience": "TUS3DP2",
    "Department Chemistry": "TUS3DP3",
    "Department Educational Sciences": "TUS7DP1",
    "Department Governance": "TUS7DP2",
    "Department Science, Technology and Society": "TUS7DP3",
}


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


from sqlalchemy import func, case


@lru_cache
def apply_filters(
    schools,
    study_level,
    ects_min,
    ects_max,
    digital_score_min,
    digital_score_max,
    module_languages,
    departments,
    previous_modules,
    topics_of_interest,
    topics_to_exclude,
):
    session = Session()
    department = aliased(Organisation)
    school = aliased(Organisation)

    # Base query with added custom ordering fields
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

    filters_and = []
    filters_or = []

    if module_languages:
        languages_mapped = set(
            itertools.chain.from_iterable(
                [language_mapper[lang] for lang in module_languages]
            )
        )
        filters_and.append(Module.lang.in_(languages_mapped))

    if study_level:
        study_levels = study_level_mapper[study_level]
        filters_and.append(Module.level.in_(study_levels))

    if ects_min is not None:
        filters_and.append(Module.ects >= ects_min)

    if ects_max is not None:
        filters_and.append(Module.ects <= ects_max)

    if digital_score_min is not None:
        filters_and.append(Module.digital_score >= digital_score_min)

    if digital_score_max is not None:
        filters_and.append(Module.digital_score <= digital_score_max)

    if schools:
        school_ids = [school_mapper[school] for school in schools]
        filters_and.append(Organisation.school_id.in_(school_ids))

    if departments:
        department_ids = [department_mapper[department] for department in departments]
        filters_and.append(department.org_id.in_(department_ids))

    if previous_modules:
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
        filters_or.append(previous_module_exists)
    if topics_of_interest:
        filters_and.append(
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

    if topics_to_exclude:
        filters_and.append(~Topic.topic.in_(topics_to_exclude))

    # Apply filters only if they exist
    if filters_and:
        query = query.filter(or_(and_(*filters_and), *filters_or))

    # Order by the number of matching topics of interest and whether it has previous modules as prerequisites
    query = query.order_by(
        func.sum(
            case((Topic.topic.in_(topics_of_interest), 1), else_=0)
        ).desc(),  # Modules with more matching topics of interest first
        func.sum(
            ModulePrerequisiteMapping.prereq_module_id_uni.in_(previous_modules)
        ).desc(),  # Modules with previous modules as prerequisites on top
    )
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
