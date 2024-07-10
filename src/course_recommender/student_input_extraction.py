import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from src.course_recommender.extraction_schema import StudentPreferences

load_dotenv()



EXAMPLE_INPUT = "Im a student in my 6th semester currently studying Computer Science at TUM. I already did the following electory courses: ERDB, IT Securiy and Business Analytics and Machine Learning. I really liked Machine Learning and I want to specialize in this subject for my masters. Im also interested in System Design especially in Microservice and Cloud Architecture. I don't like low level programming such as C. I like high level languages such as Java and Python"


def extract_student_preferences(student_input=EXAMPLE_INPUT) -> StudentPreferences:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert extraction algorithm. "
                "Only extract relevant information from the text. "
                "If you do not know the value of an attribute asked to extract, "
                "return null for the attribute's value.",
            ),
            # Please see the how-to about improving performance with
            # reference examples.
            # MessagesPlaceholder('examples'),
            ("human", "{text}"),
        ]
    )

    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)

    runnable = prompt | llm.with_structured_output(schema=StudentPreferences)

    return runnable.invoke(student_input)
