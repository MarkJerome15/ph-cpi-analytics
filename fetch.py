"""Download the PSA tables through the OpenSTAT API and save them in the same
layout as the website's 'Download CSV', so clean.py works unchanged."""
import csv
import json
import os
import time
import requests

BASE = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/2M/PI/CPI/2018NEW/"
TABLES = {
    "Consumer_Price_Index_All_Income_Households_API.csv": "0012M4ACP22.px",
    "Year-on-Year_Changes_CPI_API.csv": "0012M4ACP23.px",
    "Weights_CPI_API.csv": "0012M4ACP25.px",
}
OUT_DIR = "data/raw"      # CHANGED: validated against the manual download, now the real source
MAX_CELLS = 100_000       # values per request (PSA limits how big one request can be)


def read_json(response):
    """PSA's replies can start with an invisible BOM; utf-8-sig removes it before parsing."""
    return json.loads(response.content.decode("utf-8-sig"))


def post_with_retry(url, body, tries=4):
    """Ask the API for data. If PSA says 'too many requests' (429), wait and try again."""
    for attempt in range(tries):
        r = requests.post(url, json=body, timeout=180)
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        return read_json(r)
    raise RuntimeError("PSA API kept refusing; try again later")


def fetch_table(url):
    """Download a whole table, a few places at a time."""
    meta = read_json(requests.get(url, timeout=60))
    variables = meta["variables"]
    geo, com = variables[0], variables[1]
    others = variables[2:]                     # Year and Period (none for Weights)

    # Column labels like "2018 Jan": every combination of the other variables
    labels = [""]
    for v in others:
        labels = [f"{a} {b}".strip() for a in labels for b in v["valueTexts"]]

    cells_per_place = len(com["values"]) * len(labels)
    chunk = max(1, MAX_CELLS // cells_per_place)

    values = {}                                # (place code, item code, label) -> value
    for i in range(0, len(geo["values"]), chunk):
        geo_codes = geo["values"][i:i + chunk]
        query = [{"code": v["code"],
                  "selection": {"filter": "item",
                                "values": geo_codes if v is geo else v["values"]}}
                 for v in variables]
        js = post_with_retry(url, {"query": query, "response": {"format": "json"}})

        for point in js["data"]:
            key = point["key"]                 # the codes, in variable order
            parts = [v["valueTexts"][v["values"].index(k)] for v, k in zip(others, key[2:])]
            values[(key[0], key[1], " ".join(parts))] = point["values"][0]

        print(f"   places {i + 1}-{i + len(geo_codes)} of {len(geo['values'])}")
        time.sleep(1)                          # be polite to PSA's server
    return meta, geo, com, labels, values


def write_csv(path, meta, geo, com, labels, values):
    """Same layout as the website's CSV: title row, header, one row per place + item."""
    header = labels if labels != [""] else ["Weights"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        f.write(f'"{meta["title"]}"\n')
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["Geolocation", "Commodity Description", *header])
        for g_code, g_text in zip(geo["values"], geo["valueTexts"]):
            for c_code, c_text in zip(com["values"], com["valueTexts"]):
                row = []
                for lab in labels:
                    v = values.get((g_code, c_code, lab))
                    row.append(v if v not in (None, "") else "..")
                w.writerow([g_text, c_text, *row])


os.makedirs(OUT_DIR, exist_ok=True)
for filename, table in TABLES.items():
    print(f"Fetching {filename} ...")
    meta, geo, com, labels, values = fetch_table(BASE + table)
    write_csv(os.path.join(OUT_DIR, filename), meta, geo, com, labels, values)
    print(f"   saved {len(geo['values']) * len(com['values']):,} rows")