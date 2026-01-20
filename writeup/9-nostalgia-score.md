# Nostalgia Score Algorithm

This document explains how the **Nostalgia Score** is calculated in the recommendation system. The score ranges from `0` to `1` and measures how likely a piece of content (movie or song) is to evoke nostalgic feelings for a specific user.

---

## Overview

The nostalgia score combines two psychological concepts:

1. **Personal Nostalgia** - Content experienced during formative years (the "reminiscence bump")
2. **Cultural Nostalgia** - Popular content from before the user's birth that forms part of collective memory

```
Final Score = personal × (0.7 + 0.3 × popularity) + cultural
```

---

## Core Formula

```python
def nostalgia_score(birth_year, release_year, rating_count, max_count) -> float:
    age_at_release = release_year - birth_year

    age_score = age_nostalgia(age_at_release)
    pop_score = popularity_score(rating_count, max_count)

    # Personal nostalgia (lived experience)
    personal = age_score

    # Cultural nostalgia (only for pre-birth content)
    cultural = pop_score * 0.4 if age_at_release < 0 else 0.0

    # Final: popularity boosts but doesn't create nostalgia
    final = personal * (0.7 + 0.3 * pop_score) + cultural

    return min(1.0, max(0.0, final))
```

---

## Component 1: Age-Based Nostalgia

The `age_nostalgia` function models the **reminiscence bump** - the psychological phenomenon where memories from ages 10-30 are more vivid and emotionally significant.

### Formula

```python
def age_nostalgia(age_at_release, peak_age=13.0, width=8.0, prebirth_decay=0.03):
    if age_at_release >= 0:
        # Post-birth: Gaussian centered at peak_age
        return exp(-((age_at_release - peak_age)² / (2 × width²)))
    else:
        # Pre-birth: Exponential decay from birth
        birth_score = exp(-((0 - peak_age)² / (2 × width²)))
        return birth_score × exp(-prebirth_decay × |age_at_release|)
```

### Parameters

| Parameter        | Default | Meaning                                                 |
| ---------------- | ------- | ------------------------------------------------------- |
| `peak_age`       | 13      | Age when nostalgia peaks (based on psychology research) |
| `width`          | 8       | Spread of the Gaussian curve                            |
| `prebirth_decay` | 0.03    | How fast nostalgia decays for pre-birth content         |

### Visualization

```
Score
  1.0 ┤          ★
      │         /  \
  0.8 ┤       /      \
      │      /        \
  0.6 ┤     /          \
      │    /            \
  0.4 ┤───┘              \
      │                    \
  0.2 ┤                      ───────
      │
  0.0 └────────────────────────────────
     -20  -10   0   10   20   30   40  → Age at Release
           ↑         ↑
       Pre-birth   Peak (13)
```

### Why Peak at 13?

Research shows that the **reminiscence bump** peaks during adolescence:

- Ages 10-25 form core identity and lasting memories
- Music and movies from this period have strong emotional associations
- Peak is slightly earlier for media consumption (age 13) vs life events (age 20)

### Examples

| User Birth Year | Content Year | Age at Release | Score                    |
| --------------- | ------------ | -------------- | ------------------------ |
| 1990            | 2003         | 13             | **1.0** (peak)           |
| 1990            | 1998         | 8              | 0.73                     |
| 1990            | 2010         | 20             | 0.58                     |
| 1990            | 1985         | -5             | 0.30 (pre-birth)         |
| 1990            | 1970         | -20            | 0.16 (distant pre-birth) |

---

## Component 2: Popularity Score

Popularity uses **log-scaling** to prevent mega-hits from dominating while still rewarding well-known content.

### Formula

```python
def popularity_score(rating_count, max_count):
    if rating_count <= 0 or max_count <= 0:
        return 0.0
    return log(1 + rating_count) / log(1 + max_count)
```

### Data Sources by Content Type

| Content Type | Metric Used    | Max Value | Scaling    | Source                           |
| ------------ | -------------- | --------- | ---------- | -------------------------------- |
| **Movies**   | `rating_count` | 100,000   | Log        | MovieLens dataset ratings        |
| **Songs**    | `popularity`   | 100       | **Linear** | Spotify's 0-100 popularity score |

In the code ([recommend.py](file:///c:/Users/USER/Documents/Code/nostalgic-persuasive-model/fastapi-backend/routes/recommend.py#L253-L314)):

```python
# Movies - Log scaling for raw counts
MAX_MOVIE_RATINGS = 100000.0
ns = nostalgia_score(..., rating_count=float(rating_count), max_count=MAX_MOVIE_RATINGS)

# Songs - Linear scaling for pre-normalized Spotify popularity
MAX_SONG_POPULARITY = 100.0
ns = nostalgia_score(..., rating_count=float(song_popularity), max_count=MAX_SONG_POPULARITY, use_linear=True)
```

### Why Different Scaling?

**Movies use log scaling** because raw rating counts have extreme variance (1 to 100,000+). Log scaling prevents mega-hits from dominating:

| Rating Count | Raw Ratio | Log-Scaled Score |
| ------------ | --------- | ---------------- |
| 1,000        | 0.01      | 0.60             |
| 10,000       | 0.10      | 0.80             |
| 50,000       | 0.50      | 0.94             |
| 100,000      | 1.00      | 1.00             |

**Songs use linear scaling** because Spotify's popularity score is **already normalized** to 0-100. No transformation needed:

| Popularity | Score (Linear) |
| ---------- | -------------- |
| 20         | 0.20           |
| 50         | 0.50           |
| 80         | 0.80           |
| 100        | 1.00           |

---

## Combining Personal and Cultural Nostalgia

```python
final = personal × (0.7 + 0.3 × pop_score) + cultural
```

### Personal Component

```
personal × (0.7 + 0.3 × pop_score)
```

- **Base weight**: 70% of the age-based score is guaranteed
- **Popularity boost**: Up to 30% additional boost based on popularity
- **Key insight**: Popularity _amplifies_ personal nostalgia but cannot create it

### Cultural Component

```
cultural = pop_score × 0.4  (only if age_at_release < 0)
```

- Only applies to **pre-birth content**
- Maximum contribution: 40% of popularity score
- Represents "inherited memory" - classics parents played, cultural touchstones

### Why This Balance?

| Scenario                 | Personal          | Cultural | Total    |
| ------------------------ | ----------------- | -------- | -------- |
| Peak age + popular       | 1.0 × 1.0 = 1.0   | 0        | **1.0**  |
| Peak age + obscure       | 1.0 × 0.7 = 0.7   | 0        | **0.7**  |
| Pre-birth + very popular | 0.30 × 1.0 = 0.30 | 0.4      | **0.7**  |
| Pre-birth + obscure      | 0.30 × 0.7 = 0.21 | 0.0      | **0.21** |

---

## Pre-filtering: 10-Year Minimum Age

Before nostalgia scoring, all content is pre-filtered to be **at least 10 years old** at the recommender level:

```sql
WHERE year <= (CURRENT_YEAR - 10)
```

This ensures:

1. Content has had time to become "nostalgic"
2. No recent releases pollute the nostalgic experience
3. Aligns with the research goal of studying nostalgia's effects

---

## Secondary Filtering by Score

After scoring, candidates are filtered by a minimum threshold:

```python
MIN_NOSTALGIA_SCORE = 0.3

nostalgic_candidates = [c for c in candidates if c["nostalgia_score"] >= 0.3]
```

This removes content that is technically old enough but has low personal relevance.

---

## Design Rationale

### Why Not Just Use Age?

Age alone misses cultural impact. A user born in 2000 may feel nostalgic about 1980s classics they grew up watching with parents, even though they weren't born yet.

### Why Not Just Use Popularity?

Popularity alone would just recommend blockbusters. The goal is _personal_ nostalgia, which requires matching content to the user's formative years.

### Why Multiplicative Boost?

```
personal × (0.7 + 0.3 × popularity)
```

This ensures:

- Obscure childhood favorites still rank well (0.7 base)
- Cultural hits get a boost without being required
- A song from your childhood you've never heard of still beats a popular song you were too young for

---

## Code Location

The nostalgia scoring functions are defined in:

- [contextual_bandit.py](file:///c:/Users/USER/Documents/Code/nostalgic-persuasive-model/fastapi-backend/services/contextual_bandit.py#L618-L701)

Used in:

- [recommend.py](file:///c:/Users/USER/Documents/Code/nostalgic-persuasive-model/fastapi-backend/routes/recommend.py#L272-L313)
