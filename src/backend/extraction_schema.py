from enum import Enum
from typing import Optional, Set, Dict

from langchain_core.pydantic_v1 import BaseModel, Field


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


"""
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
print(
    "\n".join(
        sorted(
            [f'{k.replace(",", "").replace(" ", "_")} = "{v}"' for k, v in departments]
        )
    )
)
"""


class Department(Enum):
    AEROSPACE_AND_GEODESY = "Department Aerospace and Geodesy"
    ARCHITECTURE = "Department Architecture"
    BIOSCIENCE = "Department Bioscience"
    CHEMISTRY = "Department Chemistry"
    CIVIL_AND_ENVIRONMENTAL_ENGINEERING = (
        "Department Civil and Environmental Engineering"
    )
    CLINICAL_MEDICINE = "Department Clinical Medicine"
    COMPUTER_ENGINEERING = "Department Computer Engineering"
    COMPUTER_SCIENCE = "Department Computer Science"
    ECONOMICS_AND_POLICY = "Department Economics and Policy"
    EDUCATIONAL_SCIENCES = "Department Educational Sciences"
    ELECTRICAL_ENGINEERING = "Department Electrical Engineering"
    ENERGY_AND_PROCESS_ENGINEERING = "Department Energy and Process Engineering"
    ENGINEERING_PHYSICS_AND_COMPUTATION = (
        "Department Engineering Physics and Computation"
    )
    FINANCE_AND_ACCOUNTING = "Department Finance and Accounting"
    GOVERNANCE = "Department Governance"
    HEALTH_AND_SPORT_SCIENCES = "Department Health and Sport Sciences"
    INNOVATION_AND_ENTREPRENEURSHIP = "Department Innovation and Entrepreneurship"
    LIFE_SCIENCE_ENGINEERING = "Department Life Science Engineering"
    LIFE_SCIENCE_SYSTEMS = "Department Life Science Systems"
    MARKETING_STRATEGY_AND_LEADERSHIP = "Department Marketing, Strategy and Leadership"
    MATERIALS_ENGINEERING = "Department Materials Engineering"
    MATHEMATICS = "Department Mathematics"
    MECHANICAL_ENGINEERING = "Department Mechanical Engineering"
    MOBILITY_SYSTEMS_ENGINEERING = "Department Mobility Systems Engineering"
    MOLECULAR_LIFE_SCIENCES = "Department Molecular Life Sciences"
    OPERATIONS_AND_TECHNOLOGY = "Department Operations and Technology"
    PHYSICS = "Department Physics"
    PRECLINICAL_MEDICINE = "Department Preclinical Medicine"
    SCIENCE_TECHNOLOGY_AND_SOCIETY = "Department Science, Technology and Society"


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

    major: Optional[str] = Field(
        description="Major subject of the student",
        examples=[
            "Computer Science",
            "Mechanical Enginieering",
            "Mathematics",
            "Information Systems",
            "Medicine",
            "Economics",
        ],
    )
    minor: Optional[str] = Field(description="Minor subject of the student")
    study_level: Optional[StudyLevel] = Field(
        description="Degree the student is pursuing. Select one level out of the provided ones"
    )
    schools: Set[School] = Field(
        description="School the student is interested in / studying at. This is not the university. It is one level lower in the hierarchy. University -> School -> Department -> Chair. Assign the student to at least one of the schools in the examples if he hasn't specified a school. You can use the major to identify the school"
    )

    departments: Set[Department] = Field(
        description="Departments the student is interested in.", default={}
    )

    semester: Optional[int] = Field(
        default=None, description="Current Semester of the student"
    )
    ects_min: Optional[int] = Field(
        default=1, description="Minimum amount of ects for the module", gt=0
    )
    ects_max: Optional[int] = Field(
        default=30, description="Maximum amount of ects for the module", gt=0
    )
    topics_of_interest: Set[str] = Field(
        default={}, description="The topics the student is interested in."
    )
    topics_to_exclude: Set[str] = Field(
        default={}, description="Topics that should be excluded"
    )
    previous_modules: Set[str] = Field(
        default={}, description="Courses the student has previously taken"
    )
    previous_module_ids: Set[str] = Field(
        default={}, description="Module ids of courses the student has previously taken"
    )

    module_languages: Set[ModuleLanguage] = Field(
        default={},
        description="Course language preference of the student. That is the language that is used to teach the course.",
    )

    def to_json(self) -> Dict:
        return {
            "major": self.major if self.major else None,
            "minor": self.minor if self.minor else None,
            "studyLevel": self.study_level.value if self.study_level else None,
            "schools": [school.value for school in self.schools],
            "departments": [dept.value for dept in self.departments],
            "semester": self.semester,
            "ectsMin": self.ects_min,
            "ectsMax": self.ects_max,
            "topicsOfInterest": list(self.topics_of_interest),
            "topicsToExclude": list(self.topics_to_exclude),
            "previousModules": list(self.previous_modules),
            "previousModuleIds": list(self.previous_module_ids),
            "languages": [lang.value for lang in self.module_languages],
        }
