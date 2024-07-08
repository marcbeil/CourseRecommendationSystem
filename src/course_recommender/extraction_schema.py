from typing import Optional

from langchain_core.pydantic_v1 import BaseModel, Field


class StudentPreferences(BaseModel):
    """Student Message about his current state of studies"""

    university: Optional[str] = Field(
        default="TUM", description="University the student is studying at"
    )
    major: Optional[str] = Field(
        description="Major subject of the student",
        examples=[
            "Computer Science",
            "Mathematics",
            "Information Systems",
            "Medicine",
            "Economics",
        ],
    )
    minor: Optional[str] = Field(
        description="Minor subject of the student",
        examples=["Economics", "Mathematics"],
    )
    school: Optional[str] = Field(
        description="School the student is studying at. This is not the university. It is one level lower in the hierarchy. University -> School -> Department -> Chair. Assign the student to one of the schools in the examples if he hasn't specified a school. You can use the major to identify the school",
        examples=[
            "Computation, Information and Technology",
            "Engineering and Design",
            "Natural Sciences",
            "Life Sciences",
            "Medicine and Health",
            "Management",
            "Social Sciences and Technology",
        ],
    )
    semester: Optional[int] = Field(
        default=None, description="Current Semester of the student"
    )
    topics_of_interest: set[str] = Field(
        default=None, description="The topics the student is interested in."
    )
    topics_to_exclude: set[str] = Field(
        default=None, description="Topics that should be excluded"
    )
    previous_courses: set[str] = Field(
        default=None, description="Courses the student has previously taken"
    )
    language_preference: Optional[str] = Field(
        default=None, description="Course language preference of the student"
    )
