import json
from pathlib import Path

import pandas as pd

DATA_PATH = Path("data/customer_features.parquet")
REPORT_PATH = Path("reports/quality_report.json")


def main():
    df = pd.read_parquet(DATA_PATH)

    checks = {
        "row_count": int(len(df)),
        "null_counts": {
            col: int(count)
            for col, count in df.isna().sum().items()
        },
        "duplicate_customer_timestamps": int(
            df.duplicated(
                ["customer_id", "event_timestamp"]
            ).sum()
        ),
        "negative_purchase_count": int(
            (df["purchase_count_7d"] < 0).sum()
        ),
        "negative_order_value": int(
            (df["avg_order_value"] < 0).sum()
        ),
        "negative_session_duration": int(
            (df["session_duration_sec"] < 0).sum()
        ),
        "age_out_of_range": int(
            (~df["customer_age"].between(18, 100)).sum()
        ),
    }

    checks["passed"] = (
        sum(checks["null_counts"].values()) == 0
        and checks["duplicate_customer_timestamps"] == 0
        and checks["negative_purchase_count"] == 0
        and checks["negative_order_value"] == 0
        and checks["negative_session_duration"] == 0
        and checks["age_out_of_range"] == 0
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(checks, indent=2, ensure_ascii=False))

    if not checks["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
