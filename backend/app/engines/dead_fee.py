def calc_dead_fee(dead_km: float, active_rate: dict | None) -> dict:
    """空驶段：不加起步、不计低速、不乘夜间系数；仅单价 × 空驶公里。

    无启用单价（全部停用或尚未配置）时空驶费为零。
    """
    km = max(0.0, float(dead_km))
    if active_rate:
        price = float(active_rate["price_per_km"])
        rate_id = active_rate["id"]
        rate_code = active_rate.get("code")
    else:
        price = 0.0
        rate_id = None
        rate_code = None
    return {
        "dead_km": round(km, 2),
        "dead_rate_id": rate_id,
        "dead_rate_code": rate_code,
        "dead_price_per_km": round(price, 4),
        "dead_fee": round(km * price, 2),
    }
