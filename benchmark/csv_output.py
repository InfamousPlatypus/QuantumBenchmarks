from pathlib import Path
import pandas as pd


def append_to_csv(results: dict, csv_path: str) -> None:
    """Append evaluation results to a CSV file.

    Creates the CSV file with headers on the first run, then appends subsequent
    results as new rows.

    Args:
        results: Dictionary containing evaluation metrics
        csv_path: Path to the CSV output file
    """
    CSV_PATH = Path(csv_path)
    CREATE = not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0

    if CREATE:
        DF = pd.DataFrame([results])
        DF.to_csv(csv_path, index=False)
    else:
        DF = pd.read_csv(csv_path)
        DF = pd.concat([DF, pd.DataFrame([results])], ignore_index=True)
        DF.to_csv(csv_path, index=False)
