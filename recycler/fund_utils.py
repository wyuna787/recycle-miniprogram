"""
资金状态机 —— 与前端 utils/fundFlow.js 保持一致的操作语义。

所有写操作都在调用方的 DB 事务内执行（调用方负责 db.commit()），
本模块只做 db.flush() 确保 ID 生成；不单独 commit。

幂等门闩：
  - freeze  → 仅当可用余额 >= amount 时才执行
  - release → 仅当 order.fund_status == "frozen" 时（release_if_frozen）
  - deduct  → 仅当 order.fund_status == "frozen" 时（调用方在 ship 接口里判断）
"""

from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models import RecyclerFundPool, FundFlow
from money_utils import round2, PLATFORM_FEE_RATE


# ─────────────────────────────────────────────
# 内部工具
# ─────────────────────────────────────────────

def _get_or_create_pool(db: Session, company_id: int) -> RecyclerFundPool:
    pool = db.query(RecyclerFundPool).filter(
        RecyclerFundPool.company_id == company_id
    ).first()
    if not pool:
        pool = RecyclerFundPool(
            company_id=company_id,
            balance=0,
            frozen_amount=0,
            deducted_amount=0,
        )
        db.add(pool)
        db.flush()
    return pool


def _add_flow(db: Session, type: str, company_id: int, amount: float, **ctx):
    db.add(FundFlow(
        type=type,
        company_id=company_id,
        amount=round2(amount),
        order_no=ctx.get("order_no"),
        order_id=ctx.get("order_id"),
        merchant_id=ctx.get("merchant_id"),
        operator=ctx.get("operator"),
        remark=ctx.get("remark"),
        create_time=datetime.now(),
    ))


# ─────────────────────────────────────────────
# 公共查询
# ─────────────────────────────────────────────

def get_available(db: Session, company_id: int) -> float:
    """可用余额 = balance - frozen_amount"""
    pool = _get_or_create_pool(db, company_id)
    return round2((pool.balance or 0) - (pool.frozen_amount or 0))


def get_pool_info(db: Session, company_id: int) -> dict:
    pool = _get_or_create_pool(db, company_id)
    return {
        "company_id": company_id,
        "balance": round2(pool.balance or 0),
        "frozen_amount": round2(pool.frozen_amount or 0),
        "deducted_amount": round2(pool.deducted_amount or 0),
        "available_amount": round2((pool.balance or 0) - (pool.frozen_amount or 0)),
    }


# ─────────────────────────────────────────────
# 写操作
# ─────────────────────────────────────────────

def freeze_fund(db: Session, company_id: int, amount: float, **ctx) -> dict:
    """商家确认成交时冻结额度。可用不足返回 ok=False，调用方应回滚事务。"""
    amount = round2(amount)
    if amount <= 0:
        return {"ok": False, "msg": "冻结金额不正确"}
    avail = get_available(db, company_id)
    if amount > avail:
        return {"ok": False, "msg": f"可用余额不足（可用 {avail}，需冻结 {amount}）"}
    pool = _get_or_create_pool(db, company_id)
    pool.frozen_amount = round2((pool.frozen_amount or 0) + amount)
    _add_flow(db, "freeze", company_id, amount,
              remark="商家确认成交,冻结额度", **ctx)
    return {"ok": True}


def release_fund(db: Session, company_id: int, amount: float, **ctx) -> dict:
    """释放冻结额度（订单取消/关闭时）。"""
    amount = round2(amount)
    if amount <= 0:
        return {"ok": False}
    pool = _get_or_create_pool(db, company_id)
    if round2(pool.frozen_amount or 0) < amount:
        return {"ok": False, "msg": "冻结金额与订单不一致，请先核对资金流水"}
    pool.frozen_amount = round2((pool.frozen_amount or 0) - amount)
    _add_flow(db, "release", company_id, amount,
              remark="订单取消/关闭,释放冻结", **ctx)
    return {"ok": True}


def deduct_fund(db: Session, company_id: int, amount: float, **ctx) -> dict:
    """商家发货后冻结转扣款，同时附加平台 2% 服务费流水（仅记录，不二次扣余额）。"""
    amount = round2(amount)
    if amount <= 0:
        return {"ok": False}
    pool = _get_or_create_pool(db, company_id)
    if (pool.frozen_amount or 0) < amount or (pool.balance or 0) < amount:
        return {"ok": False, "msg": "冻结余额或资金池余额不足"}
    pool.frozen_amount = round2((pool.frozen_amount or 0) - amount)
    pool.balance = round2((pool.balance or 0) - amount)
    pool.deducted_amount = round2((pool.deducted_amount or 0) + amount)
    _add_flow(db, "deduct", company_id, amount,
              remark="商家已发货,冻结转扣款", **ctx)
    platform_fee = round2(amount * PLATFORM_FEE_RATE)
    if platform_fee > 0:
        _add_flow(db, "platform_fee", company_id, platform_fee,
                  remark="平台 2% 服务费", **ctx)
    return {"ok": True, "platform_fee": platform_fee}


def record_recharge_flow(db: Session, company_id: int, amount: float, **ctx):
    """充值审核通过后补一条 recharge 流水（余额由审核接口直接写，这里仅记账）。"""
    _add_flow(db, "recharge", company_id, round2(amount),
              remark="充值审核通过,额度入账", **ctx)


def release_if_frozen(db: Session, order, **ctx) -> dict:
    """
    幂等释放：仅当订单仍处于 frozen 状态时才执行释放，已扣款(deducted)时 no-op。
    order 需有 fund_status / fund_frozen_amount / recycler_company_id / order_no / id 等字段。
    """
    if order and order.fund_status == "deducted":
        # 平台批准取消/关闭已提前结算订单时，撤销额度账务，保留历史流水。
        amount = round2(order.fund_deducted_amount or 0)
        if amount <= 0:
            return {"released": False}
        pool = _get_or_create_pool(db, order.recycler_company_id)
        if round2(pool.deducted_amount or 0) < amount:
            raise HTTPException(400, "累计扣款与订单不一致，请先核对资金流水")
        pool.balance = round2((pool.balance or 0) + amount)
        pool.deducted_amount = round2(max(0, (pool.deducted_amount or 0) - amount))
        _add_flow(db, "refund", order.recycler_company_id, amount,
                  order_no=order.order_no, order_id=order.id, remark="平台关闭订单，撤销提前结算", **ctx)
        order.fund_status = "refunded"
        return {"released": True, "amount": amount}
    if not order or order.fund_status != "frozen":
        return {"released": False}
    amount = round2(order.fund_frozen_amount or order.recycler_quote_amount or order.accepted_price or 0)
    r = release_fund(db, order.recycler_company_id, amount,
                     order_no=order.order_no, order_id=order.id, **ctx)
    if not r.get("ok"):
        raise HTTPException(400, r.get("msg", "订单冻结金额无效，请先核对资金流水"))
    order.fund_status = "released"
    return {"released": bool(r.get("ok")), "amount": amount}
