"""
Dynamic Grafana dashboard generator from CSV data
"""
import json
from typing import Dict, List, Any
from datetime import datetime


def generate_dashboard_json(
    table_name: str, columns: Dict[str, str], rows: List[Dict]
) -> Dict[str, Any]:
    """
    Generate a complete Grafana dashboard JSON from CSV data
    """
    dashboard = {
        "annotations": {"list": []},
        "description": f"Auto-generated dashboard for {table_name}",
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": [],
        "refresh": "30s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": ["auto-generated", table_name],
        "templating": {"list": []},
        "time": {"from": "now-6h", "to": "now"},
        "timepicker": {},
        "timezone": "",
        "title": f"{table_name.replace('_', ' ').title()} Dashboard",
        "uid": table_name.lower(),
        "version": 1,
        "weekStart": "",
    }

    # Extract numeric and string columns
    numeric_cols = []
    string_cols = []
    datetime_cols = []

    for col_name, col_type in columns.items():
        if col_name == "id":
            continue
        if col_type in ["Integer", "Float"]:
            numeric_cols.append(col_name)
        elif col_type == "TIMESTAMP":
            datetime_cols.append(col_name)
        else:
            string_cols.append(col_name)

    panel_id = 1
    row_position = 0

    # Create table panel showing all data
    dashboard["panels"].append(
        _create_table_panel(
            panel_id, table_name, columns, row_position, datasource="Governance Postgres"
        )
    )
    panel_id += 1
    row_position += 8

    # Create numeric metric panels
    for i, col in enumerate(numeric_cols[:4]):  # Limit to 4 panels per row
        row = i // 2
        col_pos = (i % 2) * 12

        dashboard["panels"].append(
            _create_stat_panel(
                panel_id,
                col,
                table_name,
                col_pos,
                row_position + row * 8,
                datasource="Governance Postgres",
            )
        )
        panel_id += 1

    if numeric_cols:
        row_position += 8 * ((len(numeric_cols) + 1) // 2)

    # Create time series panel if datetime columns exist
    if datetime_cols and numeric_cols:
        dashboard["panels"].append(
            _create_timeseries_panel(
                panel_id,
                numeric_cols[0],
                datetime_cols[0],
                table_name,
                0,
                row_position,
                datasource="Governance Postgres",
            )
        )
        panel_id += 1
        row_position += 8

    return dashboard


def _create_table_panel(
    panel_id: int, table_name: str, columns: Dict, y_pos: int, datasource: str
) -> Dict[str, Any]:
    """Create a table panel showing query results"""
    col_names = ", ".join([f'"{col}"' for col in columns.keys() if col != "id"])

    return {
        "datasource": {"type": "postgres", "uid": "-100"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "custom": {
                    "align": "auto",
                    "cellOptions": {"type": "auto"},
                    "inspect": False,
                    "width": 100,
                },
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
            },
            "overrides": [],
        },
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": y_pos},
        "id": panel_id,
        "options": {"footer": {"countRows": False, "fields": "", "reducer": ["sum"], "show": False}, "showHeader": True},
        "pluginVersion": "10.0.0",
        "targets": [
            {
                "datasource": {"type": "postgres", "uid": "-100"},
                "format": "table",
                "rawSql": f'SELECT {col_names} FROM "{table_name}" ORDER BY id DESC LIMIT 100',
                "refId": "A",
            }
        ],
        "title": f"{table_name.replace('_', ' ').title()} - Recent Records",
        "type": "table",
    }


def _create_stat_panel(
    panel_id: int, column: str, table_name: str, x_pos: int, y_pos: int, datasource: str
) -> Dict[str, Any]:
    """Create a stat/gauge panel for numeric columns"""
    return {
        "datasource": {"type": "postgres", "uid": "-100"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "red", "value": 80},
                    ],
                },
                "unit": "short",
            },
            "overrides": [],
        },
        "gridPos": {"h": 8, "w": 12, "x": x_pos, "y": y_pos},
        "id": panel_id,
        "options": {
            "colorMode": "background",
            "graphMode": "area",
            "justifyMode": "auto",
            "orientation": "auto",
            "reduceOptions": {"values": False, "fields": "", "calcs": ["lastNotNull"]},
            "text": {},
        },
        "pluginVersion": "10.0.0",
        "targets": [
            {
                "datasource": {"type": "postgres", "uid": "-100"},
                "format": "table",
                "rawSql": f'SELECT AVG("{column}") as value FROM "{table_name}"',
                "refId": "A",
            }
        ],
        "title": f"Average {column.replace('_', ' ').title()}",
        "type": "stat",
    }


def _create_timeseries_panel(
    panel_id: int,
    value_col: str,
    time_col: str,
    table_name: str,
    x_pos: int,
    y_pos: int,
    datasource: str,
) -> Dict[str, Any]:
    """Create a time series panel"""
    return {
        "datasource": {"type": "postgres", "uid": "-100"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {
                    "axisLabel": "",
                    "axisPlacement": "auto",
                    "barAlignment": 0,
                    "drawStyle": "line",
                    "fillOpacity": 10,
                    "gradMode": "none",
                    "hideFrom": {"tooltip": False, "viz": False, "legend": False},
                    "lineInterpolation": "linear",
                    "lineWidth": 1,
                    "pointSize": 5,
                    "scaleDistribution": {"type": "linear"},
                    "showPoints": "auto",
                    "spanNulls": True,
                },
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
            },
            "overrides": [],
        },
        "gridPos": {"h": 8, "w": 24, "x": x_pos, "y": y_pos},
        "id": panel_id,
        "options": {
            "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
            "tooltip": {"mode": "single", "sort": "none"},
        },
        "pluginVersion": "10.0.0",
        "targets": [
            {
                "datasource": {"type": "postgres", "uid": "-100"},
                "format": "table",
                "rawSql": f'SELECT "{time_col}" as time, "{value_col}" as value FROM "{table_name}" ORDER BY "{time_col}" ASC',
                "refId": "A",
            }
        ],
        "title": f"{value_col.replace('_', ' ').title()} Over Time",
        "type": "timeseries",
    }


def save_dashboard_json(dashboard: Dict, output_path: str):
    """Save dashboard JSON to file"""
    with open(output_path, "w") as f:
        json.dump(dashboard, f, indent=2)
    print(f"Saved dashboard to {output_path}")
