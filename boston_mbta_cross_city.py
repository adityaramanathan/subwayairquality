import pandas as pd
import numpy as np
import os
import re
import math
import json
import zipfile
from pathlib import Path
from urllib.request import urlopen, urlretrieve
import argparse

# Boston MBTA cross city comparison
# This keeps the same functionality as the other file, but is written in a
# simpler EDA-style layout.

# Data:
# https://gis.data.mass.gov/datasets/84c9d171d32945f594fbb4d889153c44/about
# https://mbta-massdot.opendata.arcgis.com/datasets/ccb2941254944803bbd4e2df58e09906/about

# Usage: python boston_mbta_cross_city.py --data-dir mbta_data

# Constants

mbta_item_ids = {
    "2024": "ccb2941254944803bbd4e2df58e09906",
    "2025": "84c9d171d32945f594fbb4d889153c44",
}

keep_lines = ["Red", "Orange", "Blue"]
min_headway_sec = 30
max_headway_sec = 30 * 60
chunksize = 250000

ir = 10
nyc_mean_conc = 139
nyc_wait = 5
nyc_reference_dose = nyc_mean_conc * nyc_wait * ir * 0.001

# Luglio 2021 Table 1: Boston underground real-time PM2.5
boston_conc = 327
boston_sd = 136

nyc_scenarios = [
    ["NYC reference / system mean", "NYC", "system mean", 139, 5],
    ["NYC low station, long wait", "NYC", "low/Q1 station", 96, 20],
    ["NYC Broadway-Lafayette, 5 min", "NYC", "Broadway-Lafayette", 208, 5],
    ["NYC West 4th St, 5 min", "NYC", "West 4th St", 207, 5],
    ["NYC 181st St, 5 min", "NYC", "181st St", 600, 5],
    ["NYC 181st St, 10 min", "NYC", "181st St", 600, 10],
    ["NYC 181st St, 20 min", "NYC", "181st St", 600, 20],
]


# Functions


def dose(conc, wait_time):
    return conc * wait_time * ir * 0.001


def calculate_edf(conc, wait_time):
    return dose(conc, wait_time) / nyc_reference_dose


def get_csv_files(data_dir):
    files = []
    for root, dirs, filenames in os.walk(data_dir):
        for filename in filenames:
            if filename.lower().endswith(".csv"):
                files.append(os.path.join(root, filename))
    files.sort()
    return files


def unpack_zip(path, out_dir):
    if str(path).lower().endswith(".zip"):
        os.makedirs(out_dir, exist_ok=True)
        with zipfile.ZipFile(path) as zf:
            zf.extractall(out_dir)


def download_mbta_files(data_dir):
    os.makedirs(data_dir, exist_ok=True)

    for year in mbta_item_ids:
        item_id = mbta_item_ids[year]
        resources_url = (
            "https://www.arcgis.com/sharing/rest/content/items/"
            + item_id
            + "/resources?f=json"
        )
        print("Looking up ArcGIS resources for " + year)

        with urlopen(resources_url) as r:
            resources = json.load(r).get("resources", [])

        if len(resources) == 0:
            data_url = (
                "https://www.arcgis.com/sharing/rest/content/items/" + item_id + "/data"
            )
            year_dir = os.path.join(data_dir, year)
            os.makedirs(year_dir, exist_ok=True)
            dest = os.path.join(year_dir, "mbta_headways_" + year + ".zip")
            print("Trying item data endpoint for " + year)
            urlretrieve(data_url, dest)
            unpack_zip(dest, year_dir)

        for resource in resources:
            name = (
                resource.get("resource")
                or resource.get("resourceName")
                or resource.get("name")
            )
            if name is None:
                continue
            if not name.lower().endswith((".csv", ".zip")):
                continue

            year_dir = os.path.join(data_dir, year)
            os.makedirs(year_dir, exist_ok=True)
            url = (
                "https://www.arcgis.com/sharing/rest/content/items/"
                + item_id
                + "/resources/"
                + name
            )
            dest = os.path.join(year_dir, os.path.basename(name))

            if os.path.exists(dest):
                continue

            print("Downloading " + url)
            urlretrieve(url, dest)
            unpack_zip(dest, year_dir)


def find_column(columns, exact_names, words=None):
    lower_cols = {}
    for c in columns:
        lower_cols[c.lower()] = c

    for name in exact_names:
        if name.lower() in lower_cols:
            return lower_cols[name.lower()]

    if words is not None:
        for c in columns:
            found = True
            for word in words:
                if word not in c.lower():
                    found = False
            if found:
                return c

    return None


def clean_line_name(value):
    if pd.isna(value):
        return None

    value = str(value).strip()
    for line in keep_lines:
        pattern = r"(^|[^A-Za-z])" + re.escape(line) + r"([^A-Za-z]|$)"
        if re.search(pattern, value, flags=re.I):
            return line
    return None


def percentile_from_histogram(hist, percentile):
    n = int(hist.sum())
    if n == 0:
        raise ValueError("No headways were left after cleaning.")

    rank = math.ceil(percentile * n)
    cumulative = np.cumsum(hist)
    return int(np.searchsorted(cumulative, rank, side="left"))


def process_headway_files(files):
    hist = np.zeros(max_headway_sec + 1, dtype=np.int64)
    total_count = 0
    total_headway_seconds = 0

    if len(files) == 0:
        raise FileNotFoundError(
            "No CSV files found. Put the 24 MBTA CSVs in --data-dir, or run with --download first."
        )

    for file in files:
        print("Processing " + file)

        try:
            header = pd.read_csv(file, nrows=0)
        except UnicodeDecodeError:
            header = pd.read_csv(file, nrows=0, encoding="latin1")

        columns = list(header.columns)

        route_col = find_column(
            columns, ["route_id", "route", "line", "route_or_line"], ["route"]
        )
        line_col = find_column(columns, ["line", "route_or_line", "route_id"], ["line"])
        headway_col = find_column(
            columns,
            [
                "headway_trunk_seconds",
                "headway_branch_seconds",
                "headway_time_sec",
                "headway_seconds",
                "headway_sec",
            ],
            ["headway"],
        )

        if headway_col is None:
            raise ValueError("Could not find a headway column in " + file)

        usecols = []
        for c in [route_col, line_col, headway_col]:
            if c is not None and c not in usecols:
                usecols.append(c)

        for chunk in pd.read_csv(file, usecols=usecols, chunksize=chunksize, low_memory=False):
            line_series = None

            if line_col is not None and line_col in chunk.columns:
                line_series = chunk[line_col].apply(clean_line_name)

            if route_col is not None and route_col in chunk.columns:
                route_series = chunk[route_col].apply(clean_line_name)
                if line_series is None:
                    line_series = route_series
                else:
                    line_series = line_series.fillna(route_series)

            if line_series is None:
                raise ValueError("Could not find line values in " + file)

            line_mask = line_series.isin(keep_lines)
            headways = pd.to_numeric(chunk.loc[line_mask, headway_col], errors="coerce")
            headways = headways.dropna()
            headways = headways[
                (headways >= min_headway_sec) & (headways <= max_headway_sec)
            ]
            headways = headways.astype(int)

            if len(headways) == 0:
                continue

            counts = np.bincount(headways.values, minlength=max_headway_sec + 1)
            hist = hist + counts[: max_headway_sec + 1]
            total_count = total_count + len(headways)
            total_headway_seconds = total_headway_seconds + int(headways.sum())

    return hist, total_count, total_headway_seconds


def calculate_wait_stats(data_dir, download=False):
    if download:
        download_mbta_files(data_dir)

    files = get_csv_files(data_dir)
    hist, n, total_headway_seconds = process_headway_files(files)

    mean_headway = total_headway_seconds / n
    p75_headway = percentile_from_histogram(hist, 0.75)
    p90_headway = percentile_from_histogram(hist, 0.90)

    mean_wait = (mean_headway / 2) / 60
    p75_wait = (p75_headway / 2) / 60
    p90_wait = (p90_headway / 2) / 60

    return n, mean_wait, p75_wait, p90_wait


def make_tables(n, mean_wait, p75_wait, p90_wait):
    boston_waits = [
        ["Boston mean wait", mean_wait],
        ["Boston P75 wait", p75_wait],
        ["Boston P90 wait", p90_wait],
    ]

    comparison_rows = []
    comparison_rows.append(
        {
            "scenario": "NYC reference",
            "city": "NYC",
            "concentration_ug_m3": nyc_mean_conc,
            "wait_min": nyc_wait,
            "dose_ug": dose(nyc_mean_conc, nyc_wait),
            "EDF": 1.0,
        }
    )

    for item in boston_waits:
        label = item[0]
        wait_time = item[1]
        comparison_rows.append(
            {
                "scenario": label,
                "city": "Boston",
                "concentration_ug_m3": boston_conc,
                "wait_min": wait_time,
                "dose_ug": dose(boston_conc, wait_time),
                "EDF": calculate_edf(boston_conc, wait_time),
            }
        )

    comparison_df = pd.DataFrame(comparison_rows)

    uncertainty_rows = []
    for item in boston_waits:
        label = item[0]
        wait_time = item[1]
        concentrations = [
            ["low: mean-SD", max(0, boston_conc - boston_sd)],
            ["mid: mean", boston_conc],
            ["high: mean+SD", boston_conc + boston_sd],
        ]

        for concentration_item in concentrations:
            band = concentration_item[0]
            conc = concentration_item[1]
            uncertainty_rows.append(
                {
                    "scenario": label,
                    "band": band,
                    "concentration_ug_m3": conc,
                    "wait_min": wait_time,
                    "dose_ug": dose(conc, wait_time),
                    "EDF": calculate_edf(conc, wait_time),
                }
            )

    uncertainty_df = pd.DataFrame(uncertainty_rows)

    scenario_rows = []
    for s in nyc_scenarios:
        scenario_rows.append(
            {
                "scenario": s[0],
                "city": s[1],
                "station": s[2],
                "concentration": s[3],
                "wait_min": s[4],
                "dose_ug": dose(s[3], s[4]),
                "EDF": calculate_edf(s[3], s[4]),
            }
        )

    for item in boston_waits:
        label = item[0]
        wait_time = item[1]
        scenario_rows.append(
            {
                "scenario": label,
                "city": "Boston",
                "station": "underground platforms",
                "concentration": boston_conc,
                "wait_min": wait_time,
                "dose_ug": dose(boston_conc, wait_time),
                "EDF": calculate_edf(boston_conc, wait_time),
            }
        )

    all_scenarios_df = pd.DataFrame(scenario_rows)

    flip_rows = []
    nyc_df = all_scenarios_df[all_scenarios_df["city"] == "NYC"]
    boston_df = all_scenarios_df[all_scenarios_df["city"] == "Boston"]

    for i, nyc_row in nyc_df.iterrows():
        for j, boston_row in boston_df.iterrows():
            if (
                nyc_row["EDF"] > boston_row["EDF"]
                and nyc_row["concentration"] > nyc_mean_conc
                and nyc_mean_conc < boston_conc
            ):
                flip_rows.append(
                    {
                        "NYC scenario higher than Boston scenario": nyc_row["scenario"],
                        "NYC station": nyc_row["station"],
                        "NYC wait_min": nyc_row["wait_min"],
                        "NYC EDF": nyc_row["EDF"],
                        "Boston scenario": boston_row["scenario"],
                        "Boston wait_min": boston_row["wait_min"],
                        "Boston EDF": boston_row["EDF"],
                    }
                )

    flip_df = pd.DataFrame(flip_rows)

    return comparison_df, uncertainty_df, all_scenarios_df, flip_df


def round_number_columns(df):
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].round(4)
    return df


def write_outputs(out_dir, n, mean_wait, p75_wait, p90_wait):
    os.makedirs(out_dir, exist_ok=True)

    comparison_df, uncertainty_df, all_scenarios_df, flip_df = make_tables(
        n, mean_wait, p75_wait, p90_wait
    )

    comparison_df = round_number_columns(comparison_df)
    uncertainty_df = round_number_columns(uncertainty_df)
    all_scenarios_df = round_number_columns(all_scenarios_df)
    flip_df = round_number_columns(flip_df)

    comparison_df.to_csv(os.path.join(out_dir, "boston_cross_city_comparison.csv"), index=False)
    uncertainty_df.to_csv(os.path.join(out_dir, "boston_uncertainty_edf.csv"), index=False)
    all_scenarios_df.to_csv(os.path.join(out_dir, "nyc_boston_scenario_table.csv"), index=False)
    flip_df.to_csv(os.path.join(out_dir, "decision_flip_scenarios.csv"), index=False)

    p90_row = comparison_df[comparison_df["scenario"] == "Boston P90 wait"].iloc[0]

    paragraph = (
        "Using cleaned MBTA Red, Orange, and Blue line headways from 2024-2025, "
        + "the model estimated Boston expected waits of "
        + str(round(mean_wait, 2))
        + " minutes at the mean, "
        + str(round(p75_wait, 2))
        + " minutes at P75, and "
        + str(round(p90_wait, 2))
        + " minutes at P90. With Boston underground PM2.5 set to "
        + str(boston_conc)
        + " μg/m³ and IR=10 L/min, the corresponding doses were "
        + str(round(comparison_df.loc[1, "dose_ug"], 2))
        + ", "
        + str(round(comparison_df.loc[2, "dose_ug"], 2))
        + ", and "
        + str(round(comparison_df.loc[3, "dose_ug"], 2))
        + " μg, producing EDF values of "
        + str(round(comparison_df.loc[1, "EDF"], 2))
        + ", "
        + str(round(comparison_df.loc[2, "EDF"], 2))
        + ", and "
        + str(round(comparison_df.loc[3, "EDF"], 2))
        + " relative to the NYC reference dose of "
        + str(round(nyc_reference_dose, 2))
        + " μg. The P90 result means that a long-waiting Boston commuter in the cleaned MBTA data receives "
        + str(round(p90_row["dose_ug"], 2))
        + " μg in this platform-wait component, or "
        + str(round(p90_row["EDF"], 2))
        + " times the NYC reference scenario."
    )

    with open(os.path.join(out_dir, "results_paragraph.txt"), "w", encoding="utf-8") as f:
        f.write(paragraph)

    print("\nCleaned MBTA observations: " + str(n))
    print("\nComparison table:")
    print(comparison_df.to_string(index=False))
    print("\nUncertainty table:")
    print(uncertainty_df.to_string(index=False))
    print("\nDecision-flip scenarios:")
    if len(flip_df) == 0:
        print("None")
    else:
        print(flip_df.to_string(index=False))
    print("\nWrote outputs to " + out_dir)


# main

parser = argparse.ArgumentParser()
parser.add_argument("--data-dir", default="mbta_headways")
parser.add_argument("--out-dir", default="boston_cross_city_outputs")
parser.add_argument("--download", action="store_true")
args = parser.parse_args()

n, mean_wait, p75_wait, p90_wait = calculate_wait_stats(args.data_dir, args.download)
write_outputs(args.out_dir, n, mean_wait, p75_wait, p90_wait)
