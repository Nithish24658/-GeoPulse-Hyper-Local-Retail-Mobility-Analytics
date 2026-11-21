
"""Export GeoPulse GPS data quality reports to JSON and CSV."""

import json
from pathlib import Path

import pandas as pd


def export_quality_report_json(
    report: dict,
    output_path: str | Path,
) -> Path:
    """Export a GPS data quality report as a JSON file."""

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, default=str)

    return output_file


def export_quality_report_csv(
    report: dict,
    output_path: str | Path,
) -> Path:
    """Export a GPS data quality report as a CSV file."""

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    flattened_report = []

    for key, value in report.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, default=str)

        flattened_report.append({
            "metric": key,
            "value": value,
        })

    report_dataframe = pd.DataFrame(flattened_report)
    report_dataframe.to_csv(output_file, index=False)

    return output_file
