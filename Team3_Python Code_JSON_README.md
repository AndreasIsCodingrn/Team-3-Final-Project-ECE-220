# Team 3 — Cuba, NM energy data collector

This script reads **all `.json` files on the public GitHub repository's `main` branch** each time it runs. It preserves original source data and creates `team3_master_dataset.json`. It never writes to GitHub.

**Repository:** https://github.com/AndreasIsCodingrn/Team-3-Final-Project-ECE-220  
**Script:** `collect_team_data.py`  
**Runtime:** Python 3.9 or later; standard library only.

## Easiest way — Google Colab

1. Go to https://colab.research.google.com/ and create a new notebook.
2. Click the **Files** folder icon on the left, then click **Upload** and select the single file `collect_team_data.py` (not a folder).
3. Create a **new code cell** and run **only this command** (do not paste the contents of the `.py` file into the cell):

   ```python
   !python collect_team_data.py --repo AndreasIsCodingrn/Team-3-Final-Project-ECE-220 --branch main --output team3_master_dataset.json --require-all
   ```

4. If the command succeeds, the output will list collected `.json` files and say `Created: team3_master_dataset.json`. Download it from the Files pane, or run this in a **second code cell**:

   ```python
   from google.colab import files
   files.download('team3_master_dataset.json')
   ```

5. Run the same command again after more teammates commit their JSON files to `main`.

## What it includes

- `source_datasets`: full original content of every successfully loaded JSON, its GitHub path and a SHA-256 checksum.
- `normalized_tables.eia861_jmec_sales_by_sector`: consistent records from the known Team Member 2 EIA-861 structure.
- `validation_warnings` and `collection_errors`: notices that require review.

Different teammates may use different JSON structures. Their data are **collected and preserved**, but **not falsely converted** into the same measurement table; to align fields for the dashboard, add mappings after reviewing their schemas.

A successful run does **not** mean all 6 team members uploaded data. Count and inspect `source_dataset_paths`. One member can have multiple JSON files.

## Branches

Only files **committed to `main`** are included. Files present only on `Data-Energy_Burden` won't be collected until merged into `main` (or you run with `--branch Data-Energy_Burden` to inspect that branch separately). Do not combine branch outputs as if they were independent datasets; shared files might duplicate.

## Reproducibility and errors

- The program prints each collected filename and a summary at the end.
- If a JSON file is malformed or inaccessible, `--require-all` makes the process exit with a failure code; any partial master output lists its `collection_errors`.
- Files named `team3_master_dataset.json`, `master_dataset.json`, and `merged_dataset.json` are excluded so previous generated outputs cannot be recursively reimported.
- Source values are not independently fact-checked by this script; data validation and scientific interpretation remain separate tasks.
- GitHub API access for public repositories normally needs no account credentials but may be rate-limited. If an HTTP 403 occurs, try later or provide a properly authorized workflow.

## Local test (without GitHub)

With `collect_team_data.py` and your `member2_cuba_nm_eia861_openei_consolidated.json` in the same folder:

```bash
python collect_team_data.py --local-dir . --output team3_master_dataset.json
```

To run the bundled regression tests, place `test_team3_collector.py` and your member-2 JSON beside the script and run:

```bash
python -m unittest -v test_team3_collector
```
