"""
金额计算工具 —— 与前端 utils/moneyMock.js 保持完全一致的口径。

计算顺序（2026-07 重定义）：
  平台服务费     = round2(回收商报价 × 0.02)          ← 平台从成交额抽 2%
  真实成交金额   = round2(回收商报价 − 平台服务费)     = 报价 × 0.98  ← 商家/员工看到的成交额
  老板抽成      = round2(报价 × 老板比例)             ← 按「报价」算，不减平台费
  员工抽成      = round2(报价 × 员工比例)
  员工业绩      = 真实成交金额
  展示金额      = floor(真实成交金额)                  ← 去小数，工作台展示
  （已取消「商家可见金额=报价+2%」的旧口径）
"""

import math
from decimal import Decimal, ROUND_HALF_UP

PLATFORM_FEE_RATE = 0.02  # 平台从成交额抽 2%（从报价里扣，得到真实成交金额）


def round2(v) -> float:
    """四舍五入保留2位小数，与 JS Math.round(x*100)/100 等价。"""
    return float(Decimal(str(v or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def floor_money(v) -> int:
    """向下取整，去掉小数，工作台展示用。"""
    return int(math.floor(v or 0))


def build_amount_snapshot(
    quote_amount: float,
    owner_rate: float = 0,
    staff_rate: float = 0,
) -> dict:
    """
    根据成交价和抽成比例计算完整财务快照。
    返回值字段与 Order 模型字段一一对应，可直接 **解包 写入 order。
    """
    full = round2(quote_amount)                       # 回收商报价
    platform_fee = round2(full * PLATFORM_FEE_RATE)   # 平台 2%
    real = round2(full - platform_fee)                # 真实成交金额 = 报价 × 0.98
    owner_c = round2(full * (owner_rate or 0))        # 老板抽成 = 报价 × 老板率
    staff_c = round2(full * (staff_rate or 0))        # 员工抽成 = 报价 × 员工率
    return {
        "recycler_quote_amount": full,
        "platform_fee_rate": PLATFORM_FEE_RATE,
        "platform_fee_amount": platform_fee,
        # 兼容旧字段名：merchant_base_amount 现在就是真实成交金额（不再是"报价+2%"）
        "merchant_base_amount": real,
        "merchant_owner_rate": owner_rate or 0,
        "merchant_owner_commission": owner_c,
        "merchant_staff_rate": staff_rate or 0,
        "merchant_staff_commission": staff_c,
        "merchant_real_amount": real,                 # 真实成交金额（= 员工业绩）
        "merchant_display_amount": floor_money(real),
    }
