"""Rolling relationships between aligned return series."""
import pandas as pd


def compute_correlations(target_returns, driver_returns) -> dict:
    """Compute pairwise 20- and 60-observation correlations from overlapping data."""
    target = pd.Series(target_returns, dtype="float64").rename("target")
    driver = pd.Series(driver_returns, dtype="float64").rename("driver")
    aligned = pd.concat([target, driver], axis=1).dropna()
    if len(aligned) < 20:
        return {"20d": None, "60d": None, "observations": len(aligned), "status": "insufficient_data"}

    corr20 = aligned.tail(20).corr().iloc[0, 1]
    corr60 = aligned.tail(60).corr().iloc[0, 1] if len(aligned) >= 60 else None
    return {
        "20d": round(float(corr20), 4) if pd.notna(corr20) else None,
        "60d": round(float(corr60), 4) if corr60 is not None and pd.notna(corr60) else None,
        "observations": len(aligned),
        "status": "ok",
    }
