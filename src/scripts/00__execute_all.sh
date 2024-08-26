#!/bin/bash
# These Scripts build the database
# Step 1: Run 00_build_db.py first
python3 00_build_db.py

# Step 2: Run all 01_*.py scripts concurrently
python3 01_create_topic_embeddings.py &
python3 01_organisation_scraper.py &

# Wait for all 01_*.py scripts to finish
wait

# Step 3: Run the remaining scripts sequentially
python3 02_label_organisations.py
python3 03_prerequisites_extraction.py
python3 04_map_prerequisites.py
