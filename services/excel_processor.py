import pandas as pd

def process_excel_file(filepath: str):
    """
    Process the uploaded Excel file and extract required fields.
    Expected columns (normalized): "Full Name", "Class", "Total Fees"
    Returns a tuple (results, errors).
    """
    results = []
    errors = []
    try:
        df = pd.read_excel(filepath)
        # Normalize column names: remove extra spaces and convert to title case
        normalized_columns = [col.strip().title() for col in df.columns]
        print("Normalized columns:", normalized_columns)  # Debug line
        df.columns = normalized_columns
        required_cols = {"Full Name", "Class", "Total Fees"}
        if not required_cols.issubset(set(df.columns)):
            missing = required_cols - set(df.columns)
            errors.append(f"Missing required columns: {', '.join(missing)}")
            return results, errors

        # Process each row
        for idx, row in df.iterrows():
            record = {
                "Full Name": row["Full Name"],
                "Class": row["Class"],
                "Total Fees": row["Total Fees"]
            }
            results.append(record)
    except Exception as e:
        errors.append(str(e))
    return results, errors
