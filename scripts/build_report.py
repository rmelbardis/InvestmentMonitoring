#!/usr/bin/env python3
"""
Build the monthly newsletter markdown report from a content JSON file.

Usage: python scripts/build_report.py YYYYMM

Reads:  reports/YYYYMM_content.json
Writes: reports/YYYY_MM_Newsletter.md
"""

import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

DUNE_FINANCIALS = "https://dune.com/nexus_mutual/capital-pool-and-ownership"
DUNE_RAMM = "https://dune.com/nexus_mutual/ramm"
DUNE_COVERS = "https://dune.com/nexus_mutual/covers"


def rel_chart(yyyymm: str, name: str) -> str:
    """Chart path relative to the reports/ directory."""
    return f"charts/{yyyymm}/{name}.png"


def build_report(content: dict, output_path: Path) -> None:
    yyyymm = content["yyyymm"]
    month_year = content["month_year"]
    month_abbr = month_year[:3]
    year_short = month_year.split()[1][2:]
    t = content["investment_table"]

    lines = []

    # Title + intro
    lines += [
        f"# Investment Committee Newsletter - {month_year}",
        "",
        content["intro"],
        "",
    ]

    # State of the Capital Pool
    lines += [
        "## State of the Capital Pool",
        "",
        "### Monthly Change - ETH value",
        "",
        content["capital_pool_eth_paragraph"],
        "",
        "The various impacts on the capital pool are summarised in the waterfall chart below.",
        "",
        f"![Capital Pool Waterfall]({rel_chart(yyyymm, 'waterfall_eth')})",
        "",
        "The cover fee income is net of distribution commissions and excludes covers paid for in NXM. "
        "In such a case, the cover fee gets burned and there is no change in the Capital Pool.",
        "",
        "### Monthly Change in NXM Book Value",
        "",
        content["capital_pool_bv_paragraph"],
        "",
        "The various impacts on the capital pool are summarised in the waterfall chart below.",
        "",
        f"![Book Value Waterfall]({rel_chart(yyyymm, 'waterfall_bv')})",
        "",
        f"→ Members can track protocol's revenue on the [Financials Dune Dashboard]({DUNE_FINANCIALS})",
        f"→ Members can track in/outflows on the [Ratcheting AMM Dune Dashboard]({DUNE_RAMM})",
        f"→ Members can track the cover income on the [Covers Dune Dashboard]({DUNE_COVERS})",
        "",
    ]

    # End of Month Pool Split
    lines += [
        "### End of Month Pool Split",
        "",
        f"The split of the Capital Pool at the end of {month_abbr} '{year_short} in ETH terms is as follows.",
        "",
        f"![End of Month Pool Split]({rel_chart(yyyymm, 'pie_chart')})",
        "",
        f"→ Members can find the updated split at any time on the [Capital Pool and Ownership Dune Dashboard]({DUNE_FINANCIALS})",
        "",
    ]

    # State of the Investments
    lines += [
        "## State of the Investments",
        "",
        f"In the last month, the Mutual earned {t['total_return']:.1f} ETH on its investments, overall, as broken down below.",
        "",
        "```",
        f"stETH Monthly Return: {t['steth_return']}",
        f"stETH Monthly APY: {t['steth_apy']:.3f}%",
        "",
        f"rETH Monthly Return: {t['reth_return']}",
        f"rETH Monthly APY: {t['reth_apy']:.3f}%",
        "",
        f"Enzyme Vault Monthly Return: {t['enzyme_return']}",
        f"Enzyme Vault Monthly APY: {t['enzyme_apy']:.3f}%",
        "Enzyme Vault includes EtherFi investments",
        "",
        f"Total ETH Earned: {t['total_return']}",
        f"Total Monthly APY: {t['total_apy']:.3f}%",
        "Based on average Capital Pool amount over the monthly period",
        "",
        "All returns after fees",
        "```",
        "",
        f"![Investment Returns]({rel_chart(yyyymm, 'investment_returns')})",
        "",
        content["investment_summary_paragraph"],
        "",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report saved: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_report.py YYYYMM", file=sys.stderr)
        sys.exit(1)

    yyyymm = sys.argv[1]
    content_path = REPO_ROOT / "reports" / f"{yyyymm}_content.json"

    if not content_path.exists():
        print(f"Error: content file not found: {content_path}", file=sys.stderr)
        sys.exit(1)

    with open(content_path) as f:
        content = json.load(f)

    year = yyyymm[:4]
    month = int(yyyymm[4:])
    output_path = REPO_ROOT / "reports" / f"{year}_{month:02d}_Newsletter.md"
    build_report(content, output_path)


if __name__ == "__main__":
    main()
