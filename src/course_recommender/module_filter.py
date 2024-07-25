from itertools import chain

from sqlalchemy import (
    create_engine,
    Table,
    Column,
    String,
    MetaData,
    select,
    cte,
    text,
    exists,
)
from sqlalchemy.sql import and_


import logging

from course_recommender.topic_mapper import VectorStore

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

from course_recommender.extraction_schema import (
    StudentPreferences,
    StudyLevel,
    ModuleLanguage,
    Department,
    School,
)

from db.models import Session, Module, Organisation, ModuleTopicMapping, Topic


def filter_modules(pref: StudentPreferences):
    session = Session()
    query = session.query(Module)
    filters = []

    log_template = "filter ({type}): {content}"

    # TODO: fix language filter
    if pref.module_languages:
        logging.info(
            log_template.format(type="language", content=pref.module_languages)
        )
        included_languages = ModuleLanguage.get_filters(pref.module_languages)
        filters.append(Module.lang.in_(included_languages))

    if pref.study_level:
        logging.info(log_template.format(type="level", content=pref.study_level))
        included_study_levels = pref.study_level.get_level_filter()
        filters.append(Module.level.in_(included_study_levels))

    if pref.ects_min:
        logging.info(log_template.format(type="ects-min", content=pref.ects_min))
        filters.append(Module.ects >= pref.ects_min)

    if pref.ects_max:
        logging.info(log_template.format(type="ects-max", content=pref.ects_max))
        filters.append(Module.ects <= pref.ects_max)

    if pref.school:
        logging.info(log_template.format(type="school", content=pref.school.value))
        # Retrieve the school_id based on the school name
        school_id = (
            session.query(Organisation.org_id)
            .filter(Organisation.name == pref.school.value)
            .first()[0]
        )

        # Join Modules with Organisations to filter by school_id
        query = query.join(Organisation, Module.org_id == Organisation.org_id)
        filters.append(Organisation.school_id == school_id)

    if pref.departments:
        logging.info(log_template.format(type="school", content=pref.departments))
        if not pref.school:
            query = query.join(Organisation, Module.org_id == Organisation.org_id)

        department_rows = (
            session.query(Organisation.org_id)
            .filter(Organisation.name.in_([dep.value for dep in pref.departments]))
            .all()
        )
        department_ids = map(department_rows, lambda row: row[0])
        filters.append(Organisation.dep_id.in_(department_ids))

    if pref.previous_courses:
        logging.info(
            log_template.format(type="previous courses", content=pref.previous_courses)
        )
        filters.append(~Module.name.in_(pref.previous_courses))

    if filters:
        query = query.filter(and_(*filters))

    filtered_modules = query.all()

    if (pref.topics_of_interest and len(pref.topics_of_interest) > 0) or (
        pref.topics_to_exclude and len(pref.topics_to_exclude) > 0
    ):
        module_ids = [f.module_id for f in filtered_modules]
        topics = (
            session.query(Topic)
            .join(ModuleTopicMapping)
            .filter(ModuleTopicMapping.module_id.in_(module_ids))
            .distinct()
            .all()
        )
        vector_store = VectorStore(topics=topics)
        if pref.topics_of_interest and len(pref.topics_of_interest) > 0:
            logging.info(
                log_template.format(
                    type="topics of interest", content=pref.topics_of_interest
                )
            )
            mapped_topics = vector_store.map_topics(topics=pref.topics_of_interest, k=1)

            print(mapped_topics)

            # Flatten the list of lists of topics
            all_topics = list(
                chain.from_iterable([items[1] for items in mapped_topics.items()])
            )

            # Extract topic_ids from the flattened list of topics
            topic_ids_to_filter = [topic.topic_id for topic in all_topics]

            filtered_modules = (
                session.query(Module)
                .join(ModuleTopicMapping)
                .filter(Module.module_id.in_(module_ids))
                .filter(ModuleTopicMapping.topic_id.in_(topic_ids_to_filter))
                .all()
            )

        if pref.topics_to_exclude and len(pref.topics_to_exclude) > 0:
            logging.info(
                log_template.format(
                    type="excluded topics", content=pref.topics_to_exclude
                )
            )
            mapped_topics = vector_store.map_topics(topics=pref.topics_to_exclude, k=1)

            print(mapped_topics)

            # Flatten the list of lists of topics
            all_topics = list(
                chain.from_iterable([items[1] for items in mapped_topics.items()])
            )

            # Extract topic_ids from the flattened list of topics
            topic_ids_to_filter = [topic.topic_id for topic in all_topics]
            module_ids = [f.module_id for f in filtered_modules]
            print(topic_ids_to_filter)
            print(module_ids)
            subquery = select(ModuleTopicMapping).where(
                and_(
                    ModuleTopicMapping.module_id == Module.module_id,
                    ModuleTopicMapping.topic_id.in_(topic_ids_to_filter),
                )
            )
            print(filtered_modules)
            # Main query
            filtered_modules_query = (
                session.query(Module)
                .distinct()
                .filter(Module.module_id.in_(module_ids))
                .filter(~exists(subquery))
            )
            filtered_modules = filtered_modules_query.all()

    session.close()
    return filtered_modules


# Example usage
pref = StudentPreferences(
    # module_languages={"English"},
    # study_level="Bachelor",
    school=School.COMPUTATION_INFORMATION_TECHNOLOGY,
    departments=[Department.MATHEMATICS],
    # previous_courses={"Math 101", "CS 201"},
    topics_of_interest=["Dikstra Algorithm"],
    topics_to_exclude=["Affine space"],
)
filtered_modules = filter_modules(pref)

print(len(filtered_modules))
print(filtered_modules)

# print([m for m in filtered_modules])
