import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path("data/customer_features.parquet")
REPORT_PATH = Path("reports/drift_report.json")

FEATURES = [
    "purchase_count_7d",
    "avg_order_value",
    "session_duration_sec",
    "customer_age",
]

PSI_WARNING = 0.10
PSI_CRITICAL = 0.25


def calculate_psi(reference, current, bins=10):
    ref = pd.to_numeric(reference, errors="coerce").dropna().to_numpy()
    cur = pd.to_numeric(current, errors="coerce").dropna().to_numpy()

    if len(ref) == 0 or len(cur) == 0:
        return None

    # Reference의 분위수로 구간을 정의
    edges = np.unique(
        np.quantile(ref, np.linspace(0, 1, bins + 1))
    )

    if len(edges) < 2:
        edges = np.array([ref[0] - 1, ref[0] + 1])

    edges[0] = -np.inf
    edges[-1] = np.inf

    ref_counts, _ = np.histogram(ref, bins=edges)
    cur_counts, _ = np.histogram(cur, bins=edges)

    # 0으로 나누는 문제 방지
    ref_pct = ref_counts / len(ref)
    cur_pct = cur_counts / len(cur)

    epsilon = 1e-6
    ref_pct = np.clip(ref_pct, epsilon, None)
    cur_pct = np.clip(cur_pct, epsilon, None)

    return float(
        np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
    )


def main():
    df = pd.read_parquet(DATA_PATH)
    df["event_timestamp"] = pd.to_datetime(
        df["event_timestamp"], utc=True
    )

    reference = df[
        (df["event_timestamp"] >= "2025-01-01")
        & (df["event_timestamp"] < "2025-01-08")
    ]
    current = df[
        (df["event_timestamp"] >= "2025-01-08")
        & (df["event_timestamp"] < "2025-01-15")
    ]

    if reference.empty or current.empty:
        raise ValueError("Reference 또는 current 데이터가 없습니다.")

    results = {}

    for feature in FEATURES:
        psi = calculate_psi(
            reference[feature],
            current[feature],
        )

        if psi is None:
            status = "INSUFFICIENT_DATA"
        elif psi >= PSI_CRITICAL:
            status = "DRIFT"
        elif psi >= PSI_WARNING:
            status = "WARNING"
        else:
            status = "OK"

        results[feature] = {
            "psi": psi,
            "status": status,
            "reference_mean": float(reference[feature].mean()),
            "current_mean": float(current[feature].mean()),
            "reference_null_rate": float(reference[feature].isna().mean()),
            "current_null_rate": float(current[feature].isna().mean()),
        }

    report = {
        "reference_rows": int(len(reference)),
        "current_rows": int(len(current)),
        "features": results,
        "has_drift": any(
            item["status"] == "DRIFT"
            for item in results.values()
        ),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if report["has_drift"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
