from enum import Enum
from typing import Optional, Set

from langchain_core.pydantic_v1 import BaseModel, Field

from course_recommender.db.models import Session, Organisation
from db import models


class Major(Enum):
    COMPUTER_SCIENCE = "Computer Science"
    MATHEMATICS = "Mathematics"
    INFORMATION_SYSTEMS = "Information Systems"
    MEDICINE = "Medicine"
    ECONOMICS = "Economics"

    @staticmethod
    def values():
        return [major.value for major in Major]


class StudyLevel(Enum):
    BACHELOR = "Bachelor"
    MASTER = "Master"
    DOCTOR = "Doctor"
    OTHER = "Other"
    UNKNOWN = "Unknown"

    @staticmethod
    def values():
        return [level.value for level in StudyLevel]

    def get_level_filter(self):
        default_level = ["Unknown"]
        match self:
            case StudyLevel.BACHELOR:
                return ["Bachelor", "Bachelor/Master"] + default_level
            case StudyLevel.MASTER:
                return ["Bachelor", "Bachelor/Master", "Master"] + default_level
            case _:
                return default_level


# Retrieve all Departments from db
session = Session()
department_rows = (
    session.query(Organisation.name)
    .filter(Organisation.org_type == "department")
    .distinct()
    .all()
)
departments = [
    (department[0].removeprefix("Department ").upper(), department[0])
    for department in department_rows
]
Department = Enum("Department", departments)


class School(Enum):
    COMPUTATION_INFORMATION_TECHNOLOGY = "Computation, Information and Technology"
    ENGINEERING_DESIGN = "Engineering and Design"
    NATURAL_SCIENCES = "Natural Sciences"
    LIFE_SCIENCES = "Life Sciences"
    MEDICINE_HEALTH = "Medicine and Health"
    MANAGEMENT = "Management"
    SOCIAL_SCIENCES_TECHNOLOGY = "Social Sciences and Technology"

    @staticmethod
    def values():
        return [school.value for school in School]


class ModuleLanguage(Enum):
    GERMAN = "German"
    ENGLISH = "English"
    OTHER = "Other"

    @staticmethod
    def values():
        return [lang.value for lang in ModuleLanguage]

    @staticmethod
    def get_filters(languages: []):
        default_filters = set("Unknown")
        for lang in languages:
            default_filters.add(lang.value)
        if ModuleLanguage.GERMAN in languages and ModuleLanguage.ENGLISH in languages:
            default_filters.add("German/English")
        return default_filters


class StudentPreferences(BaseModel):
    """Student Message about his current state of studies"""

    university: Optional[str] = Field(
        default="TUM", description="University the student is studying at"
    )
    major: Optional[Major] = Field(description="Major subject of the student")
    minor: Optional[Major] = Field(description="Minor subject of the student")
    study_level: Optional[StudyLevel] = Field(
        description="Degree the student is pursuing. Select one level out of the provided ones"
    )
    school: Optional[School] = Field(
        description="School the student is studying at. This is not the university. It is one level lower in the hierarchy. University -> School -> Department -> Chair. Assign the student to one of the schools in the examples if he hasn't specified a school. You can use the major to identify the school"
    )

    departments: Set[Department] = Field(
        description="Departments the student is interested in."
    )

    semester: Optional[int] = Field(
        default=None, description="Current Semester of the student"
    )
    ects_min: Optional[int] = Field(
        default=None, description="Minimum amount of ects for the module", gt=0
    )
    ects_max: Optional[int] = Field(
        default=None, description="Maximum amount of ects for the module", gt=0
    )
    topics_of_interest: Set[str] = Field(
        default=None, description="The topics the student is interested in."
    )
    topics_to_exclude: Set[str] = Field(
        default=None, description="Topics that should be excluded"
    )
    previous_courses: Set[str] = Field(
        default=None, description="Courses the student has previously taken"
    )
    module_languages: Set[ModuleLanguage] = Field(
        default=None,
        description="Course language preference of the student. That is the language that is used to teach the course.",
    )
