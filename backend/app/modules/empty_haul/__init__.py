"""空驶补公里模块：空驶费 = 空驶单价 × 空驶公里。

空驶段不加起步、不计低速、不吃夜间系数；单价可落库，全部停用时空驶费为零。
"""


def calc_empty_fee(empty_km: float, per_km: float | None) -> dict:
    """按启用的空驶单价计费；per_km 为 None（无启用单价）时空驶费为零。"""
    km = float(empty_km)
    if km < 0:
        raise ValueError("empty_km 不能为负")
    if per_km is None:
        return {"empty_km": round(km, 2), "empty_per_km": None, "empty_fee": 0.0}
    price = float(per_km)
    return {"empty_km": round(km, 2), "empty_per_km": price, "empty_fee": round(km * price, 2)}
