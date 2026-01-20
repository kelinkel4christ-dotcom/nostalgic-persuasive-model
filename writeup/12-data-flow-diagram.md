# Data Flow Diagram (DFD)

## Overview

A **Data Flow Diagram (DFD)** is a graphical representation of the flow of data through a system. It illustrates how data is processed by a system in terms of inputs and outputs. DFDs are hierarchical, starting from a high-level overview (Level 0/Context Diagram) and decomposing into more detailed views (Level 1, Level 2, etc.).

This document presents the **Level 1 DFD** for the Nostalgic Persuasive System, which decomposes the single process from the Context Diagram into its constituent sub-processes.

---

## DFD Components

A Data Flow Diagram consists of four fundamental components:

| Component      | Symbol                          | Description                                                         |
| -------------- | ------------------------------- | ------------------------------------------------------------------- |
| **Process**    | Circle/Oval                     | A function that transforms input data into output data              |
| **Entity**     | Rectangle                       | An external source or destination of data (outside system boundary) |
| **Data Store** | Open Rectangle (parallel lines) | A repository where data is held for later use                       |
| **Data Flow**  | Arrow                           | The pathway along which data travels between components             |

---

## External Entities

External entities exist outside the system boundary and represent sources or destinations of data.

| Entity    | Description                                                                                       |
| --------- | ------------------------------------------------------------------------------------------------- |
| **User**  | The study participant who logs habits, receives recommendations, and provides feedback on content |
| **Admin** | The researcher who views aggregated statistics and exports experiment data for analysis           |

---

## Data Stores

Data stores represent repositories where data is persisted within the system.

| ID  | Store Name        | Description                                                                                   |
| --- | ----------------- | --------------------------------------------------------------------------------------------- |
| D1  | **User Store**    | Contains user profiles, authentication credentials (hashed), preferences, and birth year data |
| D2  | **Content Store** | Catalog of songs and movies with metadata (title, artist, year) and vector embeddings         |
| D3  | **Model Store**   | Trained machine learning models, bandit algorithm weights, and feature transformers           |
| D4  | **Log Store**     | Daily habit logs, journal entries, feedback records, and interaction history                  |

---

## Processes

The Level 1 DFD decomposes the system into five main processes:

### Process 1.0: Manage Authentication

Handles user identity verification and session management.

| Attribute      | Description                                                                        |
| -------------- | ---------------------------------------------------------------------------------- |
| **Input**      | Credentials (email, password) from User                                            |
| **Processing** | Validates credentials against stored hashes; generates secure session tokens (JWT) |
| **Output**     | Authenticated session token returned to User; User ID stored in D1 (User Store)    |

### Process 2.0: Collect Preferences

Gathers and stores user onboarding information to personalize the experience.

| Attribute      | Description                                                                                             |
| -------------- | ------------------------------------------------------------------------------------------------------- |
| **Input**      | Onboarding form data (birth year, habit selection, genre preferences) from User                         |
| **Processing** | Calculates the user's "Nostalgia Period" (birth year + 5 to birth year + 22); stores preference profile |
| **Output**     | User preferences written to D1 (User Store)                                                             |

### Process 3.0: Log Daily Activity

Records the user's daily habit status and emotional state.

| Attribute      | Description                                                                     |
| -------------- | ------------------------------------------------------------------------------- |
| **Input**      | Daily log data (habit completion status, journal text) from User                |
| **Processing** | Stores structured habit data; forwards journal text to Process 4.0 for analysis |
| **Output**     | Habit log written to D4 (Log Store); journal text passed to Process 4.0         |

### Process 4.0: Analyze Text

Processes unstructured journal text to extract emotional and stress indicators.

| Attribute      | Description                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Input**      | Journal text from Process 3.0                                                                                       |
| **Processing** | Tokenizes text using RoBERTa transformer; runs inference through stress detection and emotion classification models |
| **Output**     | Structured data: Stress Score (0.0–1.0) and Emotion Label (e.g., "Joy", "Sadness") passed to Process 5.0            |

### Process 5.0: Generate Recommendations

The core recommendation engine that selects personalized nostalgic content.

| Attribute      | Description                                                                                                                                                             |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Input**      | User context (stress score, emotion, preferences from D1); candidate content from D2; model weights from D3                                                             |
| **Processing** | (1) Filters content by nostalgia period; (2) Scores candidates using recommendation models; (3) Applies LinUCB bandit algorithm to balance exploration and exploitation |
| **Output**     | Selected recommendation (movie or song) returned to User                                                                                                                |

### Process 6.0: Process Feedback

Captures user feedback and updates the learning algorithms.

| Attribute      | Description                                                                                 |
| -------------- | ------------------------------------------------------------------------------------------- |
| **Input**      | Feedback signal (Like/Dislike) from User                                                    |
| **Processing** | Converts feedback to reward signal (1 or 0); updates LinUCB inverse covariance matrix       |
| **Output**     | Updated model weights written to D3 (Model Store); feedback record stored in D4 (Log Store) |

### Process 7.0: Generate Reports

Provides aggregated analytics and data export functionality for researchers.

| Attribute      | Description                                                                        |
| -------------- | ---------------------------------------------------------------------------------- |
| **Input**      | Query request from Admin; aggregated data from D1, D4                              |
| **Processing** | Computes statistics (completion rates, group comparisons); formats data for export |
| **Output**     | Statistics dashboard and CSV exports returned to Admin                             |

---

## Data Flows

Data flows represent the movement of data between entities, processes, and data stores.

### Entity-to-Process Flows

| Data Flow      | Source | Destination | Description                                    |
| -------------- | ------ | ----------- | ---------------------------------------------- |
| Credentials    | User   | Process 1.0 | Email and password for authentication          |
| Preferences    | User   | Process 2.0 | Birth year, habit selection, genre preferences |
| Daily Log      | User   | Process 3.0 | Habit completion status and journal text       |
| Feedback       | User   | Process 6.0 | Like/Dislike response to recommendations       |
| Report Request | Admin  | Process 7.0 | Request for statistics or data export          |

### Process-to-Entity Flows

| Data Flow               | Source      | Destination | Description                                |
| ----------------------- | ----------- | ----------- | ------------------------------------------ |
| Session Token           | Process 1.0 | User        | JWT token for authenticated session        |
| Recommendation          | Process 5.0 | User        | Selected nostalgic content (song or movie) |
| Statistics, Data Export | Process 7.0 | Admin       | Aggregated metrics and CSV files           |

### Process-to-Process Flows

| Data Flow             | Source      | Destination | Description                                   |
| --------------------- | ----------- | ----------- | --------------------------------------------- |
| Journal Text          | Process 3.0 | Process 4.0 | Raw text for sentiment analysis               |
| Stress Score, Emotion | Process 4.0 | Process 5.0 | Analyzed emotional context for recommendation |

### Process-to-Data Store Flows

| Data Flow         | Source      | Data Store | Description                           |
| ----------------- | ----------- | ---------- | ------------------------------------- |
| User Record       | Process 1.0 | D1         | New user account or session update    |
| Preference Record | Process 2.0 | D1         | User preferences and nostalgia period |
| Habit Log Record  | Process 3.0 | D4         | Daily habit status and timestamp      |
| Feedback Record   | Process 6.0 | D4         | Recommendation feedback with context  |
| Weight Update     | Process 6.0 | D3         | Updated bandit algorithm parameters   |

### Data Store-to-Process Flows

| Data Flow         | Data Store | Destination | Description                                        |
| ----------------- | ---------- | ----------- | -------------------------------------------------- |
| User Preferences  | D1         | Process 5.0 | Birth year, nostalgia period, genre preferences    |
| Candidate Content | D2         | Process 5.0 | Songs and movies filtered by nostalgia period      |
| Model Weights     | D3         | Process 5.0 | Bandit parameters and recommendation model weights |
| Aggregated Logs   | D4         | Process 7.0 | Historical data for reporting                      |
| User Profiles     | D1         | Process 7.0 | User demographics for group analysis               |

---

## Key Transformations

The DFD illustrates several critical data transformations within the system:

| Transformation                            | Description                                                                                                                                 |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Text → Emotion/Stress**                 | Unstructured journal text is converted into structured emotional indicators (stress score 0–1, emotion category) using RoBERTa transformers |
| **Content Catalog → Filtered Candidates** | Thousands of content items are filtered down to those matching the user's nostalgia period (birth year + 5 to + 22)                         |
| **Candidates → Recommendation**           | Multiple candidate items are reduced to a single optimal recommendation using the LinUCB contextual bandit algorithm                        |
| **Feedback → Learning**                   | User Like/Dislike signals are converted into mathematical weight updates that improve future recommendations                                |

---

## Closed-Loop Learning

The DFD reveals a **closed-loop feedback system**:

1. User provides **Daily Logs** → System extracts **Emotional Context**
2. System generates **Recommendation** based on context
3. User provides **Feedback** on recommendation
4. Feedback **Updates Model Weights** → Improves future recommendations

This continuous learning cycle enables the system to progressively personalize its recommendations to each user's preferences and emotional patterns.
