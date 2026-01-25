from typing import List, Dict, Optional

from storage.sqlite import record_sample, get_last

MINOR_CHANGE = 0.01   # 1%
MAJOR_CHANGE = 0.10   # 10%


def _baseline_key(metric_key: str) -> str:
    return f"{metric_key}:baseline"


def handle_rate_metric(
    *,
    key: str,
    name: str,
    value: float,
    unit: Optional[str],
) -> List[Dict]:
    """
    Delta-based alerting for rate metrics with sticky baseline.
    """
    alerts: List[Dict] = []

    baseline_key = _baseline_key(key)
    baseline = get_last(baseline_key)

    # first observation -> set baseline
    if baseline is None:
        record_sample(
            metric_key=baseline_key,
            name=f"{name} (baseline)",
            value=value,
            unit=unit,
        )
        alerts.append(
            {
                "category": "rates",
                "level": "minor",
                "metric_key": key,
                "message": f"{name} initial value: {value:.2%}",
            }
        )
        return alerts

    delta = value - baseline
    abs_delta = abs(delta)
    direction = "⬆️" if delta > 0 else "⬇️"

    # major alert
    if abs_delta >= MAJOR_CHANGE:
        alerts.append(
            {
                "category": "rates",
                "level": "major",
                "metric_key": key,
                "message": (
                    f"🚨🚨 {direction} {name} moved ≥ 10%\n"
                    f"Baseline: {baseline:.2%}\n"
                    f"Current: {value:.2%}"
                ),
            }
        )

        record_sample(
            metric_key=baseline_key,
            name=f"{name} (baseline)",
            value=value,
            unit=unit,
        )

    # minor alert
    elif abs_delta >= MINOR_CHANGE:
        alerts.append(
            {
                "category": "rates",
                "level": "minor",
                "metric_key": key,
                "message": (
                    f"🚨 {direction} {name} moved ≥ 1%\n"
                    f"Baseline: {baseline:.2%}\n"
                    f"Current: {value:.2%}"
                ),
            }
        )

        record_sample(
            metric_key=baseline_key,
            name=f"{name} (baseline)",
            value=value,
            unit=unit,
        )

    return alerts