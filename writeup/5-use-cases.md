# Use Case Diagram

## Actors

### Primary Actor

| Actor    | Description                                                                                                                  |
| -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **User** | A participant in the habit formation study who uses the system to track habits and receive nostalgic content recommendations |

### Secondary Actor

| Actor              | Description                                                                                                |
| ------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Research Admin** | A researcher or administrator who monitors the experiment, views statistics, and exports data for analysis |

---

## Use Cases

### User Use Cases

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                    SYSTEM                                          │
│                                                                                    │
│    ┌─────────────────────┐                                                         │
│    │   UC1: Register     │◄───────────────────┐                                    │
│    └─────────────────────┘                    │                                    │
│                                               │                                    │
│    ┌─────────────────────┐                    │                                    │
│    │   UC2: Login        │◄───────────────────┤                                    │
│    └─────────────────────┘                    │                                    │
│                                               │                                    │
│    ┌─────────────────────┐                    │                                    │
│    │   UC3: Complete     │◄───────────────────┤                                    │
│    │      Onboarding     │                    │                                    │
│    └─────────────────────┘                    │      ┌──────────────┐              │
│                                               ├──────│              │              │
│    ┌─────────────────────┐                    │      │     User     │              │
│    │   UC4: Log Daily    │◄───────────────────┤      │              │              │
│    │      Habit          │                    │      └──────────────┘              │
│    └─────────────────────┘                    │                                    │
│                                               │                                    │
│    ┌─────────────────────┐                    │                                    │
│    │   UC5: Receive      │◄───────────────────┤                                    │
│    │   Recommendation    │                    │                                    │
│    └─────────────────────┘                    │                                    │
│                                               │                                    │
│    ┌─────────────────────┐                    │                                    │
│    │   UC6: Provide      │◄───────────────────┤                                    │
│    │   Feedback          │                    │                                    │
│    └─────────────────────┘                    │                                    │
│                                               │                                    │
│    ┌─────────────────────┐                    │                                    │
│    │   UC7: View         │◄───────────────────┘                                    │
│    │   Progress History  │                                                         │
│    └─────────────────────┘                                                         │
│                                                                                    │
│                                                                                    │
│    ┌─────────────────────┐                                                         │
│    │   UC8: View         │◄───────────────────┐                                    │
│    │   Statistics        │                    │      ┌──────────────┐              │
│    └─────────────────────┘                    ├──────│   Research   │              │
│                                               │      │    Admin     │              │
│    ┌─────────────────────┐                    │      └──────────────┘              │
│    │   UC9: Export       │◄───────────────────┘                                    │
│    │   Data              │                                                         │
│    └─────────────────────┘                                                         │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Use Case Descriptions

### UC3: Complete Onboarding (The Setup)

- **Narrative**: When a new participant joins, we need to calibrate the system. They tell us their birth year so we can calculate their "Nostalgic Window" (e.g., if born in 1990, we focus on music from 1995-2010). They also give us a few "seed" likes so the recommender isn't blind at the start.
- **Preconditions**: User is authenticated, onboarding not completed.
- **Main Flow**:
  1. User enters birth year.
  2. User selects habit type (Exercise vs Smoking).
  3. User picks 3+ songs/movies they love.
  4. System saves profile and marks onboarding as done.

### UC4: Log Daily Habit (The Daily Check-in)

- **Narrative**: Every day, the user tells us two things: "Did I succeed?" (Accountability) and "How do I feel?" (Context). The feeling part is free-text, which we analyze for hidden stress signals.
- **Preconditions**: User is authenticated.
- **Main Flow**:
  1. User toggles "Completed" status for the day.
  2. User writes "I felt really anxious about work today..."
  3. System runs NLP to detect `Stress: High`.
  4. System saves the log.

### UC5: Receive Recommendation (The Intervention)

- **Narrative**: The user hits "Recommend". The system looks at their high stress (from UC4) and thinks, "They need something comforting." It scans the 1998-2002 catalog (their high school years) and picks a song that worked for similar stressed users.
- **Preconditions**: Onboarding complete.
- **Main Flow**:
  1. User requests recommendation.
  2. System queries Bandit model with Context(Stress=High).
  3. System returns "Song: Don't Panic by Coldplay".

### UC6: Provide Feedback (The Learning)

- **Narrative**: The user listens. If they feel that warm, fuzzy nostalgic feeling, they click "This brings back memories." The system takes this as a "Win" and reinforces the decision to play Coldplay when the user is stressed.
- **Preconditions**: Recommendation displayed.
- **Main Flow**:
  1. User votes Yes/No.
  2. System updates Bandit Weights: `Stress=High` -> `Coldplay` connection strengthened.

### Research Admin Use Cases

#### UC8: View Statistics

- **Narrative**: The researcher wants to know: "Is the Nostalgia group doing better than the Control group?" They view a dashboard comparing habit completion rates between the two cohorts.

#### UC9: Export Data

- **Narrative**: The study is over. The researcher needs the raw CSVs to run P-Value tests in Python/R to prove the hypothesis. They click "Export" to get the full dataset.
