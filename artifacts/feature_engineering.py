
import pandas as pd

NUMERIC_COLS = [
    "mudflowin", "rpm", "woba", "Hookload",
    "torqa", "blockpos", "bitdepth", "md", "rop", "stppress"
]


def preprocess_drilling_activity(df, feature_cols):
    df = df.copy()
    df[NUMERIC_COLS] = df[NUMERIC_COLS].astype(float)

    df["rotary_drilling_signal"] = (
        (df["woba"] > 0) &
        (df["rpm"] > 0)
    ).astype(int)

    df["slide_drilling_signal"] = (
        df["rpm"] == 0
    ).astype(int)

    df["other_activity_signal"] = (
        df["bitdepth"] == df["md"]
    ).astype(int)

    df = df.dropna(subset=feature_cols).reset_index(drop=True)

    X_raw = df[feature_cols]

    return X_raw, df
