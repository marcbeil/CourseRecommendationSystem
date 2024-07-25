#!/bin/bash
python3 00_build_db.py
python3 01_organisation_scraper.py & python3 01_create_topic_embeddings.py && fg
python3 02_label_organisation.py
