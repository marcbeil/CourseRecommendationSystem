import logging
from collections import defaultdict
from enum import Enum
from typing import Optional, Set, Dict

from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic.v1 import validator


class StudyLevel(Enum):
    BACHELOR = "Bachelor"
    MASTER = "Master"
    OTHER = "Other"


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


class ModuleLanguage(Enum):
    GERMAN = "German"
    ENGLISH = "English"
    OTHER = "Other"


class StudentPreferences(BaseModel):
    study_level: Optional[StudyLevel] = Field(
        description="Degree the student is pursuing. Select one level out of the provided ones",
        default=None,  # Optional, defaults to None if not provided
    )

    @validator("study_level", pre=True)
    def validate_study_level(cls, value):
        if isinstance(value, str):
            try:
                return StudyLevel(value)
            except ValueError:
                logging.warning(f"Invalid study level value: {value}, skipping.")
                return None

    schools: Optional[Set[School]] = Field(
        default=set(),  # Ensures empty set if not provided or None
        description="Schools the student is interested in / studying at. This is not the university. It is one level lower in the hierarchy.",
    )

    departments: Optional[Set[Department]] = Field(
        default=set(),  # Ensures empty set if not provided or None
        description="Departments the student is interested in. Choose out of Departments of the provided List.",
    )

    @validator("departments", pre=True, each_item=False)
    def validate_departments(cls, value):
        if not isinstance(value, set):
            value = set(value)  # Ensure value is a set

        valid_departments = set()
        for dept in value:
            try:
                valid_departments.add(Department(dept))
            except ValueError:
                logging.warning(f"Invalid department value: {dept}, skipping.")
        return valid_departments

    ects_min: Optional[int] = Field(
        default=1,  # Defaults to 1 if not provided
        description="Minimum amount of ECTS for the module.",
        gt=0,
    )

    ects_max: Optional[int] = Field(
        default=30,  # Defaults to 30 if not provided
        description="Maximum amount of ECTS for the module.",
        gt=0,
    )

    topics_of_interest: Optional[Set[str]] = Field(
        default=set(),  # Ensures empty set if not provided or None
        description="The topics the student is interested in.",
    )

    topics_to_exclude: Optional[Set[str]] = Field(
        default=set(),  # Ensures empty set if not provided or None
        description="Topics that should be excluded.",
    )

    previous_modules: Optional[Set[str]] = Field(
        default=set(),  # Ensures empty set if not provided or None
        description="Courses the student has previously taken.",
    )

    previous_module_ids: Optional[Set[str]] = Field(
        default=set(),  # Ensures empty set if not provided or None
        description="Module IDs of courses the student has previously taken.",
    )

    module_languages: Optional[Set[ModuleLanguage]] = Field(
        default=set(),  # Ensures empty set if not provided or None
        description="Course language preference of the student. Do NOT infer the language from the written language. ",
    )

    @validator("module_languages", pre=True, each_item=True)
    def validate_module_languages(cls, value):
        if isinstance(value, str):
            try:
                return ModuleLanguage(
                    value.title()
                )  # Convert to title case to match enum values
            except ValueError:
                logging.warning(f"Invalid language value: {value}, skipping.")
                return None  # Skip invalid values
        return value

    def to_json(self) -> Dict:
        # Initialize a defaultdict to group departments by schools
        departments_by_school = defaultdict(list)
        departments = self.departments or set()
        module_languages = self.module_languages or set()
        # Iterate over departments and group them by their school using department_mapper
        for dept in departments:
            school = department_mapper[dept.value]
            # Ensure self.schools is a set
            if isinstance(self.schools, set):
                self.schools.add(School(school))
            else:
                self.schools = {
                    School(school)
                }  # Create a new set if it's not already a set
            departments_by_school[school].append(dept.value)

        # Convert defaultdict to a regular dictionary
        departments = dict(departments_by_school)

        return {
            "studyLevel": self.study_level.value if self.study_level else None,
            "schools": [school.value for school in self.schools],
            "departments": departments,
            "ectsMin": self.ects_min,
            "ectsMax": self.ects_max,
            "topicsOfInterest": list(self.topics_of_interest),
            "topicsToExclude": list(self.topics_to_exclude),
            "previousModules": list(self.previous_modules),
            "previousModuleIds": list(self.previous_module_ids),
            "languages": [lang.value for lang in module_languages],
        }


department_mapper = {
    "Department Mathematics": "Computation, Information and Technology",
    "Department Computer Science": "Computation, Information and Technology",
    "Department Computer Engineering": "Computation, Information and Technology",
    "Department Electrical Engineering": "Computation, Information and Technology",
    "Department Aerospace and Geodesy": "Engineering and Design",
    "Department Architecture": "Engineering and Design",
    "Department Civil and Environmental Engineering": "Engineering and Design",
    "Department Energy and Process Engineering": "Engineering and Design",
    "Department Engineering Physics and Computation": "Engineering and Design",
    "Department Materials Engineering": "Engineering and Design",
    "Department Mechanical Engineering": "Engineering and Design",
    "Department Mobility Systems Engineering": "Engineering and Design",
    "Department Molecular Life Sciences": "Life Sciences",
    "Department Life Science Engineering": "Life Sciences",
    "Department Life Science Systems": "Life Sciences",
    "Department Economics and Policy": "Management",
    "Department Finance and Accounting": "Management",
    "Department Innovation and Entrepreneurship": "Management",
    "Department Marketing, Strategy and Leadership": "Management",
    "Department Operations and Technology": "Management",
    "Department Health and Sport Sciences": "Medicine and Health",
    "Department Preclinical Medicine": "Medicine and Health",
    "Department Clinical Medicine": "Medicine and Health",
    "Department Physics": "Natural Sciences",
    "Department Bioscience": "Natural Sciences",
    "Department Chemistry": "Natural Sciences",
    "Department Educational Sciences": "Social Sciences and Technology",
    "Department Governance": "Social Sciences and Technology",
    "Department Science, Technology and Society": "Social Sciences and Technology",
}
