import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path("data/customer_features.parquet")
RNG = np.random.default_rng(42)


def make_data(phase: str) -> pd.DataFrame:
    rows = []
    start = "2025-01-01" if phase == "baseline" else "2025-01-08"
    dates = pd.date_range(start, periods=7, freq="D", tz="UTC")

    for day in dates:
        n = 500

        purchase_count = RNG.poisson(3, n)
        avg_order_value = RNG.normal(75, 20, n).clip(5, None)
        session_duration = RNG.normal(240, 60, n).clip(10, None)
        age = RNG.integers(18, 81, n)

        if phase == "current":
            # 의도적으로 drift와 품질 문제 발생
            # 모든 주문 금액을 2배
            avg_order_value *= 2.0
            # 음수 세션 시간 — 데이터 품질 오류
            session_duration[:15] = -10
            # 비정상적으로 큰 나이 — 데이터 품질 오류
            age[15:25] = 150
            # 결측값 발생 — 데이터 품질 오류
            avg_order_value[25:45] = np.nan

        df = pd.DataFrame({
            "customer_id": np.arange(1, n + 1),
            "event_timestamp": day + pd.Timedelta(hours=12),
            "created_timestamp": day + pd.Timedelta(hours=12),
            "purchase_count_7d": purchase_count,
            "avg_order_value": avg_order_value,
            "session_duration_sec": session_duration,
            "customer_age": age,
        })
        rows.append(df)

    return pd.concat(rows, ignore_index=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=["baseline", "current"],
        required=True,
    )
    args = parser.parse_args()

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_data = make_data(args.phase)

    if args.phase == "baseline":
        new_data.to_parquet(DATA_PATH, index=False)
    else:
        if not DATA_PATH.exists():
            raise FileNotFoundError(
                "먼저 --phase baseline을 실행하세요."
            )

        baseline = pd.read_parquet(DATA_PATH)
        combined = pd.concat(
            [baseline, new_data],
            ignore_index=True,
        )
        combined.to_parquet(DATA_PATH, index=False)

    print(f"Phase: {args.phase}")
    print(f"Rows generated: {len(new_data)}")
    print(f"Saved to: {DATA_PATH}")


if __name__ == "__main__":
    main()
