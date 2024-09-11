import logging
from functools import lru_cache, cache

from pydantic import BaseModel, Field
from openai import OpenAI, RateLimitError

# Initialize the OpenAI client
client = OpenAI()


# Model representing a module with an associated reasoning for its ranking
class RankedModule(BaseModel):
    module_id: str = Field(..., description="The unique identifier for the module.")
    reasoning: str = Field(
        ..., description="Explanation for why the module was ranked in its position."
    )


# Model representing the ranking of multiple modules
class ModuleRankings(BaseModel):
    ranked_modules: list[RankedModule] = Field(
        ...,
        description="A list of modules ranked based on relevance to the student's input, each with an associated reasoning. The first module in the list should be the one with the highest ranking.",
    )


# Function to rank modules based on student input
@cache
def rank_modules(student_input, modules: tuple):
    logging.info("rank_modules")
    try:
        completion = client.beta.chat.completions.parse(
            temperature=0,
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful tutor at the help office of TUM university. You will be provided with a list of modules containing fields such as module id, description, language, etc. Also, you will be provided with a message from a student. Please rank the modules according to the student's message. Provide a reason for each module.",
                },
                {"role": "user", "content": f"Student input: {student_input}"},
                {"role": "user", "content": f"Modules:\n{modules}"},
            ],
            response_format=ModuleRankings,
        )
        ranked_modules = completion.choices[0].message.parsed.ranked_modules
    except RateLimitError:
        ranked_modules = []
    return ranked_modules
