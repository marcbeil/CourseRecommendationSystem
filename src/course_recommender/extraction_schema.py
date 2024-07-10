import enum
from typing import Optional, Set

from langchain_core.pydantic_v1 import BaseModel, Field


class Major(enum.Enum):
    COMPUTER_SCIENCE = "Computer Science"
    MATHEMATICS = "Mathematics"
    INFORMATION_SYSTEMS = "Information Systems"
    MEDICINE = "Medicine"
    ECONOMICS = "Economics"


class StudyLevel(enum.Enum):
    BACHELOR = "Bachelor"
    MASTER = "Master"
    DOCTOR = "Doctor"
    OTHER = "Other"
    UNKNOWN = "Unknown"

    def get_level_filter(self):
        default_level = ["Unknown"]
        match self:
            case StudyLevel.BACHELOR:
                return ["Bachelor", "Bachelor/Master"] + default_level
            case StudyLevel.MASTER:
                return ["Bachelor", "Bachelor/Master", "Master"] + default_level
            case _:
                return default_level


class School(enum.Enum):
    COMPUTATION_INFORMATION_TECHNOLOGY = "Computation, Information and Technology"
    ENGINEERING_DESIGN = "Engineering and Design"
    NATURAL_SCIENCES = "Natural Sciences"
    LIFE_SCIENCES = "Life Sciences"
    MEDICINE_HEALTH = "Medicine and Health"
    MANAGEMENT = "Management"
    SOCIAL_SCIENCES_TECHNOLOGY = "Social Sciences and Technology"


class ModuleLanguage(enum.Enum):
    ENGLISH = "English"
    GERMAN = "German"
    OTHER = "Other"


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
    semester: Optional[int] = Field(
        default=None, description="Current Semester of the student"
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
