import json
from src.heuristics.engine import HeuristicsEngine
import logging

logging.basicConfig(level=logging.INFO)
engine = HeuristicsEngine("config/heuristics_config.yaml", "data/local_warehouse.duckdb")
results = engine.run_all()
print(json.dumps(results, indent=2))
