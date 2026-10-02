"""Forecasting wrapper: prediction + model + features + uncertainty. stdlib.
Predictions are labeled as predictions, never facts.
"""
import time
try:
    from ..analytics.ml import forecast_ewma, forecast_linear
except ImportError:
    from analytics.ml import forecast_ewma, forecast_linear
def predict(series: list, model="ewma", features=None):
    if len(series) < 3: return {"ok": False, "reason": "insufficient data (need >=3 points)"}
    fn = forecast_linear if model == "linear" else forecast_ewma
    val = fn(series)
    lo, hi = min(series), max(series)
    spread = (hi - lo) / abs(sum(series) / len(series)) if sum(series) else 0
    return {"ok": True, "prediction": val, "model": f"price-{model}-v1",
            "features": features or {"n": len(series), "last": series[-1]},
            "timestamp": time.time(), "uncertainty": round(spread, 4),
            "note": "prediction, not a fact"}
