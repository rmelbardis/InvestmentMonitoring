#!/usr/bin/env python3
"""
Execute a monthly investment notebook and extract charts + numbers.

Usage: python scripts/execute_notebook.py YYYYMM

Outputs:
  - Chart images to reports/charts/YYYYMM/
  - Data JSON to reports/YYYYMM_data.json (also printed to stdout)
"""

import sys
import json
import base64
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Chart cells, keyed by stable notebook cell ID (cells move when the notebook
# is edited; IDs are copied unchanged from month to month). Listed in the order
# they appear in the newsletter (not the order they appear in the notebook).
CHART_CELLS = [
    ("87b4c553", "waterfall_eth"),       # Capital pool ETH waterfall - newsletter position 1
    ("1830a3b1", "waterfall_bv"),        # Book value per NXM waterfall - newsletter position 2
    ("ff85e094", "pie_chart"),           # End of month pool split pie - newsletter position 3
    ("58aece89", "investment_returns"),  # Investment returns bar chart - newsletter position 4
]

# Cell IDs whose stream (print) output contains key numbers
TEXT_OUTPUT_CELLS = {
    "investment_returns": "8f17ffb5",  # stETH, rETH, Enzyme, total returns + APYs
    "summary": "95812e88",             # Capital pool opening/closing, BV/NXM, % changes
}


def cells_by_id(cells: list) -> dict:
    """Map cell ID -> cell, failing loudly if an expected ID is missing."""
    by_id = {c.get("id"): c for c in cells}
    expected = [cid for cid, _ in CHART_CELLS] + list(TEXT_OUTPUT_CELLS.values())
    missing = [cid for cid in expected if cid not in by_id]
    if missing:
        raise KeyError(
            f"Notebook is missing expected cell ID(s): {missing}. "
            "Update CHART_CELLS / TEXT_OUTPUT_CELLS in scripts/execute_notebook.py."
        )
    return by_id


def execute_notebook(notebook_path: Path) -> None:
    """Execute notebook in-place via nbconvert."""
    result = subprocess.run(
        [
            "jupyter", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--inplace",
            "--ExecutePreprocessor.timeout=600",
            "--ExecutePreprocessor.kernel_name=python3",
            str(notebook_path),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Notebook execution failed.\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )


def extract_charts(by_id: dict, charts_dir: Path) -> dict:
    """Extract chart images from executed notebook cells."""
    chart_paths = {}
    for cell_id, name in CHART_CELLS:
        cell = by_id[cell_id]
        for output in cell.get("outputs", []):
            if output.get("output_type") in ("display_data", "execute_result"):
                png_data = output.get("data", {}).get("image/png")
                if png_data:
                    img_path = charts_dir / f"{name}.png"
                    with open(img_path, "wb") as f:
                        f.write(base64.b64decode(png_data))
                    chart_paths[name] = str(img_path)
                    break
        if name not in chart_paths:
            print(f"Warning: no chart found in cell {cell_id} ({name})", file=sys.stderr)
    return chart_paths


def extract_text_outputs(by_id: dict) -> dict:
    """Extract stream (print) outputs from key cells."""
    outputs = {}
    for key, cell_id in TEXT_OUTPUT_CELLS.items():
        cell = by_id[cell_id]
        parts = []
        for output in cell.get("outputs", []):
            if output.get("output_type") == "stream":
                parts.append("".join(output.get("text", [])))
        outputs[key] = "\n".join(parts).strip()
    return outputs


def main():
    if len(sys.argv) < 2:
        print("Usage: python execute_notebook.py YYYYMM", file=sys.stderr)
        sys.exit(1)

    yyyymm = sys.argv[1]
    notebook_path = REPO_ROOT / f"InvestmentMonitoring-{yyyymm}.ipynb"

    if not notebook_path.exists():
        print(f"Error: notebook not found: {notebook_path}", file=sys.stderr)
        sys.exit(1)

    charts_dir = REPO_ROOT / "reports" / "charts" / yyyymm
    charts_dir.mkdir(parents=True, exist_ok=True)

    print(f"Executing {notebook_path.name} ...", file=sys.stderr)
    execute_notebook(notebook_path)
    print("Execution complete.", file=sys.stderr)

    with open(notebook_path) as f:
        nb = json.load(f)
    by_id = cells_by_id(nb["cells"])

    print("Extracting charts ...", file=sys.stderr)
    chart_paths = extract_charts(by_id, charts_dir)

    print("Extracting output numbers ...", file=sys.stderr)
    text_outputs = extract_text_outputs(by_id)

    result = {
        "yyyymm": yyyymm,
        "chart_paths": chart_paths,
        **text_outputs,
    }

    data_path = REPO_ROOT / "reports" / f"{yyyymm}_data.json"
    with open(data_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Data written to {data_path}", file=sys.stderr)

    # Print to stdout so the skill can read it
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
