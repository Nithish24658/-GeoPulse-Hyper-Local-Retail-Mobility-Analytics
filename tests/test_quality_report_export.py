
"""Tests for GPS data quality report exports."""

import json

import pandas as pd

from src.data_quality.export_quality_report import (
    export_quality_report_csv,
    export_quality_report_json,
)


def create_sample_report():
    """Create a sample quality report for testing."""

    return {
        "total_records": 100,
        "unique_devices": 10,
        "missing_values": 2,
        "missing_values_by_column": {
            "device_id": 0,
            "latitude": 2,
        },
        "missing_required_columns": [],
        "duplicate_records": 0,
        "invalid_coordinates": 0,
        "timezone_aware": True,
        "quality_status": "PASS",
    }


def test_json_export_creates_file(tmp_path):
    report = create_sample_report()
    output_path = tmp_path / "reports" / "quality_report.json"

    result = export_quality_report_json(report, output_path)

    assert result.exists()
    assert result == output_path


def test_json_export_preserves_report_data(tmp_path):
    report = create_sample_report()
    output_path = tmp_path / "quality_report.json"

    export_quality_report_json(report, output_path)

    with output_path.open(encoding="utf-8") as file:
        exported_report = json.load(file)

    assert exported_report["total_records"] == 100
    assert exported_report["quality_status"] == "PASS"
    assert exported_report["missing_values_by_column"]["latitude"] == 2


def test_csv_export_creates_file(tmp_path):
    report = create_sample_report()
    output_path = tmp_path / "reports" / "quality_report.csv"

    result = export_quality_report_csv(report, output_path)

    assert result.exists()
    assert result == output_path


def test_csv_export_preserves_report_metrics(tmp_path):
    report = create_sample_report()
    output_path = tmp_path / "quality_report.csv"

    export_quality_report_csv(report, output_path)

    exported_report = pd.read_csv(output_path)

    total_records = exported_report.loc[
        exported_report["metric"] == "total_records", "value"
    ].iloc[0]

    quality_status = exported_report.loc[
        exported_report["metric"] == "quality_status", "value"
    ].iloc[0]

    assert int(total_records) == 100
    assert quality_status == "PASS"


def test_csv_export_preserves_nested_values(tmp_path):
    report = create_sample_report()
    output_path = tmp_path / "quality_report.csv"

    export_quality_report_csv(report, output_path)

    exported_report = pd.read_csv(output_path)

    missing_values = exported_report.loc[
        exported_report["metric"] == "missing_values_by_column",
        "value",
    ].iloc[0]

    assert json.loads(missing_values)["latitude"] == 2
