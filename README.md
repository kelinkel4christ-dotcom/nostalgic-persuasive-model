# Nostalgic Persuasive Model for Habit Formation

> A research-driven application that leverages nostalgic content recommendations to promote positive habit formation and reduce relapse risk.

[![Nuxt](https://img.shields.io/badge/Nuxt-4.x-00DC82?logo=nuxt.js)](https://nuxt.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/License-Academic-blue)]()

---

## 📋 Table of Contents

- [Overview](#overview)
- [Research Objectives](#research-objectives)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Datasets](#datasets)
- [API Documentation](#api-documentation)
- [Research Methodology](#research-methodology)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project is part of an **academic study on habit formation**, investigating how **nostalgia-based interventions** can improve outcomes in:

- **🚭 Smoking Cessation** — Supporting users in quitting smoking
- **🏃 Exercise Consistency** — Helping users build and maintain workout habits

The application uses a **100% Nostalgic Recommendation Pipeline** to deliver personalized content from the user's past:

- **🎵 Music**: Content-based filtering with pgvector, filtered to nostalgic years.
- **🎬 Movies**: Hybrid LightFM model, filtered to nostalgic years.
- **🧠 Selection**: Contextual Bandit (LinUCB) selects based on mood/stress.

---

## Research Objectives

The primary goal of this system is to test the hypothesis that **nostalgia reduces stress and improves habit adherence**.

Key research questions:

1.  **Effectiveness**: Does consuming nostalgic content reduce self-reported stress levels in real-time?
2.  **Adherence**: Do users who receive nostalgic interventions stick to their habits (e.g., daily exercise) longer than a control group?
3.  **Personalization**: Does a Reinforcement Learning (Bandit) model improve recommendation engagement over time compared to static baselines?

---

## Features

### 👤 User Experience

- **Onboarding Calibration**: Calculates the user's "Nostalgia Window" (reminiscence bump) based on birth year.
- **Daily Habit Logging**: Users log habit completion and write a short journal entry about their mood.
- **Real-time Mood Analysis**: NLP models analyze journal text to detect stress and emotions (Joy, Sadness, Fear, etc.).
- **Personalized Interventions**: Delivers specific song or movie recommendations targeted to alleviate current stress levels.
- **Feedback Loop**: Users rate recommendations ("Did this bring back memories?"), training the underlying AI model.

### 🔬 Research Admin Dashboard

- **Cohort Management**: Track participation across Control vs. Nostalgia groups.
- **Data Export**: Download anonymized CSV datasets for statistical analysis (P-Value tests, etc.).
- **Analytics**: View completion rates and mood trends over time.

---

## Architecture

The system follows a modern microservices-like architecture, separating the research UI from the heavy ML lifting.

```mermaid
graph TD
    Client[Web Client - Nuxt 4] --> Gateway[API Gateway - FastAPI]
    Gateway --> Auth[Auth Service]
    Gateway --> RecSys[Recommendation Engine]

    subgraph "Machine Learning Core"
        RecSys --> Bandit[Contextual Bandit (LinUCB)]
        RecSys --> NLP[Text Analyzer (RoBERTa)]
        RecSys --> Content[Content Selectors (LightFM)]
    end

    subgraph "Data Persistence"
        Bandit --> DB[(PostgreSQL)]
        Content --> VectorDB[(pgvector)]
    end
```

---

## Tech Stack

### Frontend & Application Layer

- **Framework**: [Nuxt 4](https://nuxt.com) (Vue 3, TypeScript)
- **UI Library**: [Nuxt UI](https://ui.nuxt.com) (TailwindCSS)
- **State Management**: Pinia
- **Authentication**: Better Auth
- **Data Fetching**: Drizzle ORM

### Backend & ML Service

- **Framework**: FastAPI (Python)
- **Dependency Manager**: [Pixi](https://prefix.dev)
- **Machine Learning**:
  - **PyTorch** & **Scikit-learn**: Core ML operations.
  - **Transformers (HuggingFace)**: Emotion and stress detection (RoBERTa).
  - **LightFM**: Hybrid collaborative filtering for movies.
  - **MABWiser**: Contextual Bandit implementation.
- **Database**: PostgreSQL 16 with `pgvector` extension.

---

## Getting Started

### Prerequisites

- [Bun](https://bun.sh) (JavaScript Runtime)
- [Docker](https://www.docker.com) (For Database)
- [Pixi](https://prefix.dev) (For Python Environment)

### Installation

1.  **Clone the repository**

    ```bash
    git clone https://github.com/your-org/nostalgic-persuasive-model.git
    cd nostalgic-persuasive-model
    ```

2.  **Start the Database**

    ```bash
    docker compose up -d postgres
    ```

3.  **Setup the Backend (Python)**
    Navigate to the backend directory and install dependencies using Pixi.

    ```bash
    cd fastapi-backend
    pixi install
    ```

    Start the ML API server:

    ```bash
    pixi run dev
    # Runs on http://localhost:8000
    ```

4.  **Setup the Frontend (Nuxt)**
    In a new terminal, go to the root directory.
    ```bash
    bun install
    ```
    Initialize the database schema:
    ```bash
    bun run db:migrate
    bun run db:seed  # Optional: Seeds initial data
    ```
    Start the application:
    ```bash
    bun run dev
    # Runs on http://localhost:3000
    ```

---

## Project Structure

```bash
├── app/                  # Nuxt 4 application source
├── server/               # Nuxt server-side API (BFF)
├── fastapi-backend/      # Python ML API & Recommendation Engine
│   ├── core/             # Configuration & Shared Logic
│   ├── routes/           # API Endpoints
│   ├── services/         # ML Models (Bandit, NLP, Recommenders)
│   └── main.py           # Entry point
├── writeup/              # Academic documentation & Algorithms
├── dataset/              # Raw datasets (Movies, Songs)
├── docker-compose.yml    # Infrastructure configuration
└── nuxt.config.ts        # Nuxt configuration
```

---

## Datasets

The system utilizes custom-curated datasets for nostalgic content:

- **Movies**: A subset of datasets enriched with release years and popularity metrics, filtered for the "Nostalgia Window" of participants.
- **Music**: Songs tagged with year and genre, processed into vector embeddings for similarity matching.
- **User Data**: Anonymized logs of habit completion, mood entries, and recommendation feedback (stored in local Postgres).

---

## API Documentation

When the backend is running, full interactive API documentation (Swagger UI) is available at:

- **Local**: `http://localhost:8000/docs`
- **Redoc**: `http://localhost:8000/redoc`

Key Endpoints:

- `POST /predict/stress`: Analyze journal text for stress levels.
- `POST /recommend`: Get a contextual bandit recommendation.
- `POST /feedback`: Update the bandit model with user feedback.

---

## Research Methodology

This project implements advanced algorithms documented in the `writeup/` directory:

1.  **Nostalgia Score Algorithm**: Calculates a score `[0, 1]` based on the **Reminiscence Bump** (ages 10-30), giving higher weight to content released during a user's formative years.
2.  **Hierarchical LinUCB Bandit**:
    - **Context**: User Stress Level, Emotion, Historical Positive Rate.
    - **Arms**: 12 Normalized Genres (e.g., "Rock", "Comedy", "Action").
    - **Exploration/Exploitation**: Balances showing known favorites vs. exploring new nostalgic candidates.
3.  **Hybrid Filtering**: Combines Collaborative Filtering (what similar users liked) with Content-Based Filtering (year, genre, audio features).

For detailed algorithmic descriptions, see [`writeup/13-academic-algorithms.md`](writeup/13-academic-algorithms.md).

---

## Contributing

1.  Fork the repository
2.  Create your feature branch (`git checkout -b feature/amazing-feature`)
3.  Commit your changes (`git commit -m 'Add some amazing feature'`)
4.  Push to the branch (`git push origin feature/amazing-feature`)
5.  Open a Pull Request

---

## License

This project is intended for **Academic Research Purposes**.
See the LICENSE file for details.
