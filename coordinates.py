"""Load the pre-generated island coordinates.

The deployment uses coordinates_cache.json directly. It does not call external
geocoding services during startup, so deployments are predictable and fast.
"""
import json
import os

CACHE_FILE = os.path.join(os.path.dirname(__file__), "coordinates_cache.json")

with open(CACHE_FILE, "r", encoding="utf-8") as f:
    coordinates = json.load(f)

if not coordinates:
    raise RuntimeError("coordinates_cache.json is empty; cannot start the map.")
