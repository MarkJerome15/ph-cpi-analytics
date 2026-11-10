"""Rebuild everything: fetch from PSA -> clean -> database -> CSVs for Power BI -> charts -> forecast."""
import subprocess
import sys
import time

steps = ["fetch.py", "clean.py", "export.py", "charts.py", "forecast.py"]  

for step in steps:
    start = time.time()
    print(f"\n=== Running {step} ===")
    subprocess.run([sys.executable, step], check=True)
    print(f"=== {step} done in {time.time() - start:.0f}s ===")

print("\nAll steps finished.")