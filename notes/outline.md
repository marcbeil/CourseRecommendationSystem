# Outline

1. Requirements
    - Student should be able to formulate his module preferences in natural language
    - The system should filter the modules based on the preferences
    - The modules should be ordered by relevance
    - The student should be able to adjust the filters afterwards
    - Available Filters:
        - Departments
        - Digital Score
        - ECTS Range
        - Excluded Topics
        - Included Topics
        - Language Preference
        - Previous Modules
        - Schools
2. Transformation of Database
    - Database Schema
3. Filters
    1. Organisation Scraping
        - Scrape TUM organisations
        - Label organisations
            - school, department, chair, former organisation etc.
        - Specify school and department for each organisation
    2. Structuring of Prerequisites
        - Extraction of possible module prerequisites identifiers (titles, ids) by LLM and REGEX
        - Mapping these identifiers to modules in the db
            - ids: equality matching
            - titles: fuzzy matching with threshold
        - Evaluation of mapping and extraction
            - Labeling unstructured prerequisites by hand
            - Maximising recall metric (>80%)
    3. Ranking the filtered modules
        - by amount of matching topics
        - by LLM (LLM gets list of module descriptions as well as natural language input of student and is asked to rank
          based on students input)
4. Extraction of unstructured student input
   - LLM extraction of filters:
   - Language preference, ECTS range, schools, departments, included topics, excluded topics, previous modules
5. Visual User Interface
    - Frontend: React
    - Backend: Python Flask
