#!/usr/bin/env python3
"""
Convert CDISC CORE unit test Excel files to CSV format.

Expected input structure:
  <standard>/                   e.g. SDTMIG/
    <RULE_ID>/                  e.g. CG0001/
      negative/                 only "negative" and "positive" are processed
        01/                     numbered test case directories
          data/                 Excel + any other files (xml)
          results/              ignored

Output is written to a sibling directory named <standard>_csv/, e.g.:
  SDTMIG/ -> SDTMIG_csv/

For each data/ directory the script produces:
  - <tab_name>.csv    one per dataset sheet — header row + data rows only
  - tables.csv        from the Datasets tab
  - variables.csv     one row per variable across all dataset sheets
  - .env              key=value from the Library tab + xml file paths
  - define.xml        copied if present
  results/ directories and non-xml/non-excel files are skipped.
"""

import argparse
import csv
import shutil
import sys
from pathlib import Path
import openpyxl

# Only process these subdirectories; dev is ignored
POLARITY_DIRS = {"negative", "positive"}
# Excel sheet structure: rows 1-4 are metadata, row 5+ is data
METADATA_ROWS = 4
DATA_START_ROW = 5
# non-dataset sheets
SKIP_TABS = {"Datasets", "Library"}



# ── helpers ───────────────────────────────────────────────────────────────────


def is_excel(path: Path) -> bool:
    return path.suffix.lower() in (".xlsx", ".xls", ".xlsm")


def get_max_col(ws) -> int:
    max_col = 0
    for row in ws.iter_rows(values_only=True):
        for i, v in enumerate(row):
            if v is not None:
                max_col = max(max_col, i + 1)
    return max_col


def fmt(v) -> str:
    return str(v) if v is not None else ""


def write_csv(path: Path, rows: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


# ── Excel processing ──────────────────────────────────────────────────────────

def process_excel(xlsx_path: Path, out_dir: Path) -> list[str]:
    errors = []
    try:
        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    except Exception as e:
        return [f"{xlsx_path}: failed to open Excel file — {e}"]

    dataset_sheets = [n for n in wb.sheetnames if n not in SKIP_TABS]

    if not dataset_sheets:
        errors.append(f"{xlsx_path}: no dataset sheets found")

    # tables.csv — from Datasets tab
    if "Datasets" not in wb.sheetnames:
        errors.append(f"{xlsx_path}: missing Datasets tab")
    if "Datasets" in wb.sheetnames:
        ws = wb["Datasets"]
        max_col = get_max_col(ws)
        rows = [[fmt(v) for v in row[:max_col]] for row in ws.iter_rows(values_only=True)]
        while rows and all(v == "" for v in rows[-1]):
            rows.pop()
        write_csv(out_dir / "tables.csv", rows)

    # variables.csv — one row per variable from the metadata rows of each dataset sheet
    var_rows = [["dataset", "variable", "label", "type", "length"]]
    for sheet_name in dataset_sheets:
        ws = wb[sheet_name]
        meta = list(ws.iter_rows(min_row=1, max_row=METADATA_ROWS, values_only=True))
        if not meta:
            continue
        var_names = meta[0] if len(meta) > 0 else []
        labels    = meta[1] if len(meta) > 1 else []
        types     = meta[2] if len(meta) > 2 else []
        lengths   = meta[3] if len(meta) > 3 else []
        for i, var in enumerate(var_names):
            if var is None:
                continue
            var_rows.append([
                sheet_name,
                fmt(var),
                fmt(labels[i])  if i < len(labels)  else "",
                fmt(types[i])   if i < len(types)   else "",
                fmt(lengths[i]) if i < len(lengths) else "",
            ])
    write_csv(out_dir / "variables.csv", var_rows)

    # <worksheer>.csv — one per dataset sheet, header row + data rows
    for sheet_name in dataset_sheets:
        ws = wb[sheet_name]
        max_col = get_max_col(ws)
        all_rows = list(ws.iter_rows(min_row=1, values_only=True))
        if not all_rows:
            continue
        header = [fmt(v) for v in all_rows[0][:max_col]]
        data_rows = [
            [fmt(v) for v in row[:max_col]]
            for row in all_rows[DATA_START_ROW - 1:]
            if any(v is not None for v in row[:max_col])
        ]
        display_name = sheet_name
        for _ext in (".xpt", ".csv"):
            if display_name.lower().endswith(_ext):
                display_name = display_name[:-len(_ext)]
                break
        safe_name = display_name.replace("/", "_").replace("\\", "_")
        write_csv(out_dir / f"{safe_name}.csv", [header] + data_rows)
        write_csv(out_dir / f"{safe_name}.csv", [header] + data_rows)

    # .env creation
    env_lines = []
    if "Library" in wb.sheetnames:
        ws = wb["Library"]
        lib_rows = list(ws.iter_rows(values_only=True))
        if len(lib_rows) >= 2:
            # Row 1 = headers, Row 2 = standard values
            headers = [fmt(h).strip() for h in lib_rows[0]]
            for h, v in zip(headers, lib_rows[1]):
                if h and v is not None:
                    env_lines.append(f"{h.upper().replace(' ', '_')}={v}")
            # Row 3+ = CT packages, all in column A (no label)
            ct_values = [
                fmt(row[0])
                for row in lib_rows[2:]
                if row[0] is not None and fmt(row[0]).strip() != ""
            ]
            if ct_values:
                env_lines.append(f"CT={','.join(ct_values)}")

    xml_files = sorted(xlsx_path.parent.glob("*.xml"))
    if xml_files:
        env_lines.append(f"DEFINE_XML={xml_files[0].name}")

    (out_dir / ".env").write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    return errors


# ── directory traversal ───────────────────────────────────────────────────────

def process_data_dir(data_dir: Path, out_data_dir: Path) -> list[str]:
    """Convert Excel files and copy define.xml."""
    out_data_dir.mkdir(parents=True, exist_ok=True)
    errors = []
    files = sorted(f for f in data_dir.iterdir() if f.is_file())
    if not any(is_excel(f) for f in files):
        errors.append(f"{data_dir}: no Excel file found — non-Excel files copied as-is")
    for f in files:
        if is_excel(f):
            errors.extend(process_excel(f, out_data_dir))
        else:
            shutil.copy2(f, out_data_dir / f.name)
    return errors



def process_results_dir(results_dir: Path, out_results_dir: Path, label: str) -> list[str]:
    errors = []
    for f in sorted(results_dir.iterdir()):
        if not f.is_file():
            continue
        out_results_dir.mkdir(parents=True, exist_ok=True)
        if f.suffix.lower() == ".json":
            shutil.copy2(f, out_results_dir / f.name)
        elif is_excel(f):
            shutil.copy2(f, out_results_dir / f.name)
            errors.append(f"{label}/results/{f.name}: result file is Excel, expected JSON")
        else:
            shutil.copy2(f, out_results_dir / f.name)
    return errors


def process_standard(standard_dir: Path, output_dir: Path):
    all_errors = []
    for rule_dir in sorted(standard_dir.iterdir()):
        if not rule_dir.is_dir():
            continue
        if not any(child.is_dir() and child.name.lower() in POLARITY_DIRS for child in rule_dir.iterdir()):
            continue

        for polarity_dir in sorted(rule_dir.iterdir()):
            if not polarity_dir.is_dir():
                continue
            if polarity_dir.name.lower() not in POLARITY_DIRS:
                continue

            for num_dir in sorted(polarity_dir.iterdir()):
                if not num_dir.is_dir():
                    continue

                data_dir = num_dir / "data"
                if not data_dir.exists():
                    continue

                rel = num_dir.relative_to(standard_dir)
                out_data_dir = output_dir / rel / "data"

                errs = process_data_dir(data_dir, out_data_dir)
                if errs:
                    all_errors.extend(errs)
                    print(f"  {rule_dir.name}/{polarity_dir.name}/{num_dir.name}/data [errors: {len(errs)}]")
                else:
                    print(f"  {rule_dir.name}/{polarity_dir.name}/{num_dir.name}/data")

                results_dir = num_dir / "results"
                if results_dir.exists():
                    out_results_dir = output_dir / rel / "results"
                    label = f"{rule_dir.name}/{polarity_dir.name}/{num_dir.name}"
                    errs = process_results_dir(results_dir, out_results_dir, label)
                    if errs:
                        all_errors.extend(errs)
                        print(f"  {label}/results [errors: {len(errs)}]")


    log_path = output_dir / "conversion_errors.log"
    if all_errors:
        log_path.write_text("\n".join(all_errors) + "\n", encoding="utf-8")
        print(f"  {len(all_errors)} error(s) written to {log_path}")
    elif log_path.exists():
        log_path.unlink()


# ── entry point ───────────────────────────────────────────────────────────────
'''
Process a full standard directory
  python convert_tests.py SDTMIG/

Process a single Excel file
  python convert_tests.py --file path/to/test.xlsx
'''


def main():
    parser = argparse.ArgumentParser(
        description="Convert CDISC CORE unit test Excel files to CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=None,
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
    )
    parser.add_argument("--file", metavar="XLSX", help="Process a single Excel file instead")
    args = parser.parse_args()

    if args.file:
        xlsx = Path(args.file)
        if not xlsx.exists():
            print(f"Error: {xlsx} not found", file=sys.stderr)
            sys.exit(1)
        output_dir = xlsx.parent
        process_excel(xlsx, output_dir)
        print(f"Done. Output in: {output_dir}")
        return

    if not args.input_dir:
        parser.error("input_dir is required when --file is not specified")

    input_dir = Path(args.input_dir).resolve()
    output_dir = input_dir.parent / f"{input_dir.name}_csv"

    if not input_dir.exists():
        print(f"Error: {input_dir} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Processing: {input_dir}")
    print(f"Output:     {output_dir}")
    process_standard(input_dir, output_dir)
    print("Done.")


if __name__ == "__main__":
    main()
