import pandas as pd

from python_basic_template.settings.settings import DataDirs


def load_raw_data(file_name: str) -> pd.DataFrame:
    file_path = DataDirs.RAW / file_name
    df = pd.read_csv(file_path)
    return df