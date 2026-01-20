import numpy as np
import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

# Load environment
load_dotenv("../../.env")  # Path from training/test/ to project root
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/myapp")

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def test_vibes():
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()

    print("--- Song Vibe Check ---\n")
    
    # Define test cases: (Name query, Expected Vibe)
    test_cases = [
        ("Smells Like Teen Spirit", "High Energy Rock (90s)"),
        ("Toxic", "Dance Pop (2000s)"),
        ("Hotel California", "Classic Rock (70s)"),
        ("Shape of You", "Modern Pop (2010s)") 
    ]
    
    for query_name, expected_vibe in test_cases:
        print(f"\nQuerying: '{query_name}' (Expect: {expected_vibe})")
        
        # 1. Find the song
        cursor.execute(f"""
            SELECT id, name, artists, genre, year, energy, valence, danceability 
            FROM songs 
            WHERE name ILIKE %s 
            LIMIT 1
        """, (f"%{query_name}%",))
        
        source = cursor.fetchone()
        
        if not source:
            print(f"  ❌ Song not found in DB.")
            continue
            
        sid, sname, sartists, sgenre, syear, senergy, svalence, sdance = source
        print(f"  Found: {sname} by {sartists}")
        print(f"  Attributes: Year={syear}, Genre={sgenre}")
        print(f"  Vibes: Energy={senergy:.2f}, Valence={svalence:.2f}, Dance={sdance:.2f}")
        
        # 2. Find similar songs
        cursor.execute("""
            SELECT s.name, s.artists, s.genre, s.year, s.energy, s.valence, s.danceability,
                   1 - (sv.embedding <=> (SELECT embedding FROM song_vectors WHERE spotify_id = %s)) as similarity
            FROM song_vectors sv
            JOIN songs s ON sv.spotify_id = s.id
            WHERE sv.spotify_id != %s
            ORDER BY sv.embedding <=> (SELECT embedding FROM song_vectors WHERE spotify_id = %s)
            LIMIT 5;
        """, (sid, sid, sid))
        
        recommendations = cursor.fetchall()
        
        print(f"  Top 5 Similar Songs:")
        print(f"  {'Title':<30} | {'Artist':<20} | {'Year':<4} | {'Genre':<15} | {'En.':<4} | {'Val.':<4} | {'Dan.':<4} | {'Sim.'}")
        print(f"  {'-'*115}")
        
        for r in recommendations:
            name, artist, genre, year, energy, valence, dance, sim = r
            # Ensure values are strings
            if isinstance(name, list): name = str(name)
            if isinstance(artist, list): artist = str(artist)
            if isinstance(genre, list): genre = ", ".join(genre)
            elif genre is None: genre = ""

            # Truncate strings
            name = (name[:27] + '..') if len(name) > 27 else name
            artist = (artist[:17] + '..') if len(artist) > 17 else artist
            genre = (genre[:12] + '..') if len(genre) > 12 else genre
            
            print(f"  {name:<30} | {artist:<20} | {year:<4} | {genre:<15} | {energy:.2f} | {valence:.2f} | {dance:.2f} | {sim:.3f}")

    conn.close()

if __name__ == "__main__":
    test_vibes()
