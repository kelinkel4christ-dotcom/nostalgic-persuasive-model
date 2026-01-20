"""
Test script for nostalgia score calculation.
Final version with gated popularity and personal vs cultural nostalgia.
"""

import math
from datetime import datetime

import pandas as pd


def age_nostalgia(
    age_at_release: int,
    peak_age: float = 13.0,
    width: float = 8.0,
    prebirth_decay: float = 0.03,
) -> float:
    """
    Age-based nostalgia score.
    - Post-birth: Gaussian centered at peak_age
    - Pre-birth: Exponential decay from birth point
    """
    if age_at_release >= 0:
        return math.exp(-((age_at_release - peak_age) ** 2) / (2 * width ** 2))
    else:
        birth_score = math.exp(-((0 - peak_age) ** 2) / (2 * width ** 2))
        return birth_score * math.exp(-prebirth_decay * abs(age_at_release))


def popularity_score(rating_count: float, max_count: float) -> float:
    """Log-scaled popularity to prevent mega-hits from dominating."""
    if rating_count <= 0 or max_count <= 0:
        return 0.0
    return math.log1p(rating_count) / math.log1p(max_count)


def nostalgia_score(
    birth_year: int,
    release_year: int,
    rating_count: float,
    max_count: float,
    min_years_ago: int = 10,
) -> float:
    """
    Final nostalgia score combining personal and cultural nostalgia.
    
    Key insight: Popularity BOOSTS nostalgia but cannot CREATE it.
    """
    current_year = datetime.now().year
    years_ago = current_year - release_year
    age_at_release = release_year - birth_year

    # Too recent → not nostalgic
    if years_ago < min_years_ago:
        return 0.0

    age_score = age_nostalgia(age_at_release)
    pop_score = popularity_score(rating_count, max_count)

    # ---- PERSONAL NOSTALGIA ----
    # Based on lived experience (age when content released)
    personal = age_score

    # ---- CULTURAL NOSTALGIA ----
    # Only applies to pre-birth content (inherited cultural memory)
    cultural = pop_score * 0.4 if age_at_release < 0 else 0.0

    # ---- FINAL SCORE ----
    # Popularity boosts nostalgia but cannot create it
    final = personal * (0.7 + 0.3 * pop_score) + cultural

    return round(min(1.0, max(0.0, final)), 3)


def main() -> None:
    birth_year = 2004
    current_year = datetime.now().year
    
    output_lines: list[str] = []
    
    def log(msg: str = "") -> None:
        print(msg)
        output_lines.append(msg)
    
    log("=== Nostalgia Score Test (Final Formula) ===")
    log(f"User: born {birth_year}, age {current_year - birth_year}")
    log(f"Current year: {current_year}")
    log()
    log("Formula: personal * (0.7 + 0.3 * pop) + cultural")
    log("  - personal = age_nostalgia (Gaussian + prebirth decay)")
    log("  - cultural = pop * 0.4 (only for pre-birth content)")
    log("  - pop = log-scaled popularity")
    log()
    
    # Load movies
    log("Loading movies...")
    movies_df = pd.read_csv("../dataset/ml-32m/movies.csv")
    movies_df["year"] = movies_df["title"].str.extract(r"\((\d{4})\)").astype(float)
    movies_df = movies_df.dropna(subset=["year"])
    movies_df["year"] = movies_df["year"].astype(int)
    log(f"Loaded {len(movies_df)} movies with year")
    
    # Load ratings
    log("Loading ratings...")
    ratings_df = pd.read_csv("../dataset/ml-32m/ratings.csv", usecols=["movieId", "rating"])
    rating_stats = ratings_df.groupby("movieId").agg(
        rating_count=("rating", "count"),
        avg_rating=("rating", "mean")
    ).reset_index()
    log(f"Got rating stats for {len(rating_stats)} movies")
    
    # Merge
    df = movies_df.merge(rating_stats, left_on="movieId", right_on="movieId", how="left")
    df["rating_count"] = df["rating_count"].fillna(0)
    max_count = df["rating_count"].max()
    log(f"Max rating count: {max_count}")
    log()
    
    # Calculate scores
    df["age_at_release"] = df["year"] - birth_year
    df["age_score"] = df["age_at_release"].apply(age_nostalgia)
    df["pop_score"] = df["rating_count"].apply(lambda x: popularity_score(x, max_count))
    df["nostalgia_score"] = df.apply(
        lambda row: nostalgia_score(
            birth_year=birth_year,
            release_year=int(row["year"]),
            rating_count=row["rating_count"],
            max_count=max_count,
        ),
        axis=1,
    )
    df["short_title"] = df["title"].str[:42]
    
    # TOP 20 ALL MOVIES
    log("=" * 90)
    log("TOP 20 MOVIES BY NOSTALGIA SCORE")
    log("=" * 90)
    log(f"{'Score':<7} {'Year':<6} {'Age':<6} {'AgeSc':<7} {'Pop':<6} Title")
    log("-" * 90)
    top = df.nlargest(20, "nostalgia_score")
    for _, row in top.iterrows():
        log(f"{row['nostalgia_score']:<7.3f} {row['year']:<6} {row['age_at_release']:+5}  {row['age_score']:<7.3f} {row['pop_score']:<6.3f} {row['short_title']}")
    log()
    
    # TOP 20 PRE-BIRTH
    log("=" * 90)
    log("TOP 20 PRE-BIRTH MOVIES (released before 2004)")
    log("=" * 90)
    log(f"{'Score':<7} {'Year':<6} {'Age':<6} {'AgeSc':<7} {'Pop':<6} Title")
    log("-" * 90)
    pre_birth = df[df["year"] < birth_year].nlargest(20, "nostalgia_score")
    for _, row in pre_birth.iterrows():
        log(f"{row['nostalgia_score']:<7.3f} {row['year']:<6} {row['age_at_release']:+5}  {row['age_score']:<7.3f} {row['pop_score']:<6.3f} {row['short_title']}")
    log()
    
    # DECADE AVERAGES
    log("=" * 90)
    log("AVERAGE NOSTALGIA SCORE BY DECADE")
    log("=" * 90)
    df["decade"] = (df["year"] // 10) * 10
    for decade, avg in df.groupby("decade")["nostalgia_score"].mean().items():
        log(f"{decade}s: {avg:.3f}")
    log()
    
    # AGE SCORE CURVE
    log("=" * 90)
    log("AGE NOSTALGIA CURVE (age_nostalgia function)")
    log("=" * 90)
    for age in [-50, -30, -20, -10, -5, 0, 5, 10, 13, 15, 20, 25, 30]:
        score = age_nostalgia(age)
        bar = "█" * int(score * 40)
        log(f"Age {age:+4}: {score:.3f} {bar}")
    
    # Save to file
    with open("test/output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print("\n\nResults saved to test/output.txt")


if __name__ == "__main__":
    main()
