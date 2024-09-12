# Outline 

---

## 1. Introduction

### 1.1 Problem Statement

- Challenges faced by students in selecting relevant university modules.
- Limitations of existing systems in filtering and ranking modules based on natural language input.

### 1.2 Objective

- To develop a system that allows students to input their module preferences in natural language.
- To implement a filtering and ranking mechanism that orders modules based on relevance to the student's preferences.

### 1.3 Contributions

- Introducing a novel approach that combines natural language processing with module filtering and ranking.
- Development of a user-friendly interface that allows for dynamic filter adjustments.
- (Extracting module prerequisites out of unstructured module prerequisite texts)

## 2. Related Work

### 2.1 Existing Systems for Module Selection

- Overview of current systems and their limitations.

### 2.2 Natural Language Processing in Education

- Use of NLP for extracting student preferences.

### 2.3 Relevance Ranking Techniques

- Traditional vs. modern approaches (e.g., LLM-based ranking).

## 3. System Requirements and Features

### 3.1 Student Input Processing

- Description of how the system interprets natural language input.

### 3.2 Filtering Mechanism

- Explanation of filters: departments, digital score, ECTS range, excluded/included topics, language preference,
  previous modules, schools.

### 3.3 Ranking Mechanism

- Description of relevance ranking using both matching topics and LLM-based ranking.

### 3.4 Filter Adjustment

- How students can dynamically adjust filters after initial input.

## 4. Transformation of Database

### 4.1 Database Schema Design

- Overview of the schema used to store module data.

### 4.2 Data Transformation for Filtering

- Steps taken to structure data for efficient filtering and ranking.

### 4.3 Handling Unstructured Prerequisites

- Use of LLM and REGEX to extract and map prerequisites.
- Evaluation and manual labeling process to improve accuracy.

## 5. Filter Implementation

### 5.1 Organisation Scraping

- Methodology for scraping TUM organisations.
- Labelling and categorization of organisations.

### 5.2 Prerequisite Structuring

- Detailed process of extracting and mapping module prerequisites.
- Evaluation metrics used to assess mapping quality.

### 5.3 Ranking Modules

- Criteria used for ranking modules: topic matching, LLM-based relevance scoring.

## 6. Extraction of Unstructured Student Input

### 6.1 LLM-Based Extraction

- Techniques for extracting filters from natural language input.

### 6.2 Categories of Extracted Data

- Language preference, ECTS range, schools, departments, included/excluded topics, previous modules.

### 6.3 Evaluation of Extraction Accuracy

- Metrics and results of the extraction process.

## 7. Visual User Interface

### 7.1 Frontend Design

- Overview of the React-based user interface.
- How the UI facilitates natural language input and filter adjustments.

### 7.2 Backend Implementation

- Description of the Python Flask backend and its role in processing and serving data.

### 7.3 Integration of Frontend and Backend

- How the frontend and backend interact to deliver a seamless user experience.

## 8. System Evaluation

### 8.1 User Testing

- Results from testing the system with real students.
- Feedback on ease of use, accuracy of filtering, and relevance of ranking.

## 9. Discussion

### 9.1 Advantages of Natural Language Input

- How natural language input enhances user experience and satisfaction.

### 9.2 Challenges and Limitations

- Issues encountered during system development and possible solutions.

### 9.3 Future Work

- Potential improvements, such as expanding filter options or refining LLM accuracy.

## 10. Conclusion

### 10.1 Summary of Contributions

- Recap of the system's key features and innovations.


### 10.2 Final Remarks

- Closing thoughts on the system’s potential and next steps for research.

## 11. References

- Comprehensive list of academic and technical sources referenced throughout the paper.

## 12. Appendices

### 12.1 Database Schema Diagram

- Visual representation of the database structure.

### 12.2 User Interface Screenshots

- Images of the frontend interface and key user interactions.

