# Context Diagram

## Overview

A **Context Diagram** (also known as a Level 0 Data Flow Diagram) represents the highest-level view of a system. It abstracts the entire system as a **single process** and illustrates its interactions with external entities through data flows. Crucially, a context diagram excludes internal data stores, focusing exclusively on the system's boundary and external interfaces.

## The Central Process

The **Nostalgic Persuasive System** (Process 1.0) represents the entire system abstracted as a single process. It is a recommendation platform designed to support habit formation—specifically smoking cessation and exercise consistency—through nostalgic content delivery.

### Core Capabilities

The system encapsulates the following capabilities within its boundary:

| Capability                     | Description                                                                                          |
| ------------------------------ | ---------------------------------------------------------------------------------------------------- |
| **Habit Formation Support**    | Tracks daily habit logs and monitors user progress toward behavioral goals                           |
| **Nostalgic Content Delivery** | Recommends music and movies from the user's formative years (ages 5–22)                              |
| **Stress/Emotion Analysis**    | Analyzes journal entries using machine learning models to detect stress levels and emotional states  |
| **Personalized Learning**      | Employs contextual bandit algorithms (LinUCB) to learn user preferences and optimize recommendations |

### System Boundary Characteristics

The system operates as a **self-contained unit** with the following boundary considerations:

- **Data Privacy**: All journal entries and stress data remain within the system boundary. Local machine learning models (RoBERTa transformers) perform text analysis, eliminating dependency on external cloud NLP providers.
- **Content Independence**: Recommendations are generated from a local catalog of songs and movies, without real-time queries to external APIs (e.g., Spotify, Netflix).

---

## External Entities

External entities (also called terminators or actors) represent sources or destinations of data that exist outside the system boundary.

### 1. User (Study Participant)

The **User** is the primary actor and subject of the study. This entity represents an individual participating in the habit formation research program.

| Attribute                 | Description                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Role**                  | Provides behavioral signals (mood, habit success, feedback) that enable the system to learn and adapt  |
| **Interaction Frequency** | Daily. Submits one habit log per day and requests multiple recommendations throughout the day          |
| **Significance**          | The source of all training data for the bandit algorithms and the recipient of content recommendations |

### 2. Admin (Research Observer)

The **Admin** is a secondary actor representing the scientist or research team conducting the study. This entity operates outside the main user interaction loop.

| Attribute        | Description                                                                                    |
| ---------------- | ---------------------------------------------------------------------------------------------- |
| **Role**         | Observes and analyzes aggregated data; cannot influence individual user recommendations        |
| **Access Level** | Read-only access to system statistics and data export functionality                            |
| **Significance** | Responsible for evaluating the efficacy of nostalgia-based interventions through data analysis |

---

## Data Flows

Data flows represent the movement of data between external entities and the system. In a context diagram, these flows cross the system boundary.

### Inbound Data Flows

| Data Flow                             | Source → Destination | Description                                                                                                                                                                                      |
| ------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Registration, Login Credentials**   | User → System        | Initial account creation (email, password, demographic information) and authentication data to establish secure sessions                                                                         |
| **Preferences, Daily Logs, Feedback** | User → System        | Onboarding preferences (birth year, habit selection), structured habit data (e.g., "Did you exercise today?"), unstructured journal text, and boolean feedback (Like/Dislike) on recommendations |
| **Login Credentials**                 | Admin → System       | Authentication data for research administrators to access the admin dashboard                                                                                                                    |

### Outbound Data Flows

| Data Flow                   | Source → Destination | Description                                                                                                                                               |
| --------------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Recommendations**         | System → User        | Personalized nostalgic content (songs or movies from the user's formative years) selected based on current stress level, mood, and historical preferences |
| **Statistics, Data Export** | System → Admin       | Aggregated analytics (study progress, group comparisons, emotion/stress distributions) and CSV exports of anonymized research data for external analysis  |

---

## Significance of the Data Flows

The context diagram reveals a **bidirectional learning loop** that distinguishes this system from static recommendation platforms:

1. **Input Acquisition**: The system collects both structured (habit logs) and unstructured (journal text) data from users
2. **Output Delivery**: The system returns personalized nostalgic content tailored to the user's emotional state
3. **Feedback Integration**: User feedback directly influences future recommendations through the contextual bandit algorithm
4. **Research Observation**: The entire process generates valuable research data for studying the efficacy of nostalgia-based interventions

This creates a **closed-loop system** where user behavior shapes system behavior, enabling the research team to measure the impact of nostalgic content on habit formation outcomes.
