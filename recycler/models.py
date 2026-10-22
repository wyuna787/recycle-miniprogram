from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)

    role = Column(String, nullable=False)
    # platform_admin
    # merchant_owner
    # merchant_staff
    # recycler_owner
    # recycler_keeper
    # recycler_staff

    company_type = Column(String, nullable=False)
    # merchant / recycler / platform

    company_id = Column(Integer, nullable=True)

    can_create_inquiry = Column(Boolean, default=True)
    can_view_all_inquiry = Column(Boolean, default=False)
    can_accept_quote = Column(Boolean, default=False)
    can_manage_staff = Column(Boolean, default=False)

    session_version = Column(Integer, default=0, nullable=False)
    password_hash = Column(String, nullable=True)
    apply_reason = Column(Text, nullable=True)
    reject_reason = Column(Text, nullable=True)

    # pending / approved / rejected
    status = Column(String, default="pending")
    create_time = Column(DateTime, default=datetime.now)


class MerchantCompany(Base):
    __tablename__ = "merchant_companies"

    id = Column(Integer, primary_key=True, index=True)

    company_name = Column(String, nullable=False)
    owner_user_id = Column(Integer, nullable=False)

    contact_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    address = Column(String, nullable=True)

    deposit_amount = Column(Float, default=0)
    deposit_followup = Column(Text, nullable=True)
    deposit_followup_by = Column(String, nullable=True)
    deposit_followup_time = Column(DateTime, nullable=True)
    join_code = Column(String, nullable=False)

    status = Column(String, default="active")
    create_time = Column(DateTime, default=datetime.now)


class RecyclerCompany(Base):
    __tablename__ = "recycler_companies"

    id = Column(Integer, primary_key=True, index=True)

    company_name = Column(String, nullable=False)
    owner_user_id = Column(Integer, nullable=True)

    contact_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    address = Column(String, nullable=True)

    employee_limit = Column(Integer, default=20)
    status = Column(String, default="active")

    create_time = Column(DateTime, default=datetime.now)


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, nullable=False)

    device_type = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    condition = Column(String, nullable=True)
    fault_desc = Column(Text, nullable=True)
    images = Column(Text, nullable=True)

    # 设备明细：基础规格 + 逐项检测结果(JSON)
    storage = Column(String, nullable=True)
    color = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    warranty = Column(String, nullable=True)
    detail_json = Column(Text, nullable=True)

    create_time = Column(DateTime, default=datetime.now)


class DeviceInquiry(Base):
    __tablename__ = "device_inquiries"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False)
    merchant_id = Column(Integer, nullable=False)
    merchant_company_id = Column(Integer, nullable=True)

    status = Column(String, default="pending_quote")
    recycler_company_ids = Column(Text, nullable=True)

    create_time = Column(DateTime, default=datetime.now)


class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)

    no = Column(String, nullable=False)

    merchant_company_id = Column(Integer, nullable=False)
    merchant_company_name = Column(String, nullable=True)

    created_by_user_id = Column(Integer, nullable=False)
    created_by_user_name = Column(String, nullable=True)

    device_type = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)

    storage = Column(String, nullable=True)
    color = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    warranty = Column(String, nullable=True)

    device_detail_json = Column(Text, nullable=True)
    photos_json = Column(Text, nullable=True)

    status = Column(String, default="waiting_quote")
    # waiting_quote / quoted / accepted / cancelled / ordered

    create_time = Column(DateTime, default=datetime.now)


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)

    inquiry_id = Column(Integer, nullable=False)
    device_id = Column(Integer, nullable=True)
    merchant_id = Column(Integer, nullable=True)

    recycler_company_id = Column(Integer, nullable=False)
    recycler_company_name = Column(String, nullable=True)

    quote_user_id = Column(Integer, nullable=False)
    quote_user_name = Column(String, nullable=True)
    quote_user_role = Column(String, nullable=False)

    price = Column(Float, nullable=False)
    valid_hours = Column(Integer, default=24)
    valid_days = Column(Integer, default=3)
    remark = Column(Text, nullable=True)

    # quoted / accepted / expired / cancelled
    status = Column(String, default="quoted")

    create_time = Column(DateTime, default=datetime.now)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    order_no = Column(String, nullable=False)

    inquiry_id = Column(Integer, nullable=False)
    quote_id = Column(Integer, nullable=False)
    device_id = Column(Integer, nullable=True)

    merchant_id = Column(Integer, nullable=True)
    recycler_id = Column(Integer, nullable=True)

    merchant_company_id = Column(Integer, nullable=True)
    recycler_company_id = Column(Integer, nullable=False)

    price = Column(Float, nullable=True)
    accepted_price = Column(Float, nullable=False)

    # confirmed / shipped / received / inspection_done / completed / appealing / closed
    status = Column(String, default="confirmed")

    express_company = Column(String, nullable=True)
    tracking_no = Column(String, nullable=True)
    shipping_images = Column(Text, nullable=True)
    ship_time = Column(DateTime, nullable=True)
    receive_time = Column(DateTime, nullable=True)

    inspection_type = Column(String, nullable=True)
    inspection_price = Column(Float, nullable=True)
    inspection_reason = Column(Text, nullable=True)
    inspection_time = Column(DateTime, nullable=True)

    merchant_confirm_time = Column(DateTime, nullable=True)
    appeal_reason = Column(Text, nullable=True)
    appeal_time = Column(DateTime, nullable=True)
    close_reason = Column(Text, nullable=True)
    close_time = Column(DateTime, nullable=True)

    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ---- 金额快照（确认成交时一次性写入，历史快照不随比例变更） ----
    recycler_quote_amount = Column(Float, nullable=True)
    platform_fee_rate = Column(Float, default=0.02)
    platform_fee_amount = Column(Float, nullable=True)
    merchant_base_amount = Column(Float, nullable=True)
    merchant_owner_rate = Column(Float, default=0)
    merchant_owner_commission = Column(Float, nullable=True)
    merchant_staff_rate = Column(Float, default=0)
    merchant_staff_commission = Column(Float, nullable=True)
    merchant_real_amount = Column(Float, nullable=True)      # 留小数，结算/分析
    merchant_display_amount = Column(Integer, nullable=True)  # 去小数，工作台展示

    settlement_mode = Column(String, nullable=True)  # ship / receive；成交时锁定

    # ---- 资金状态机 ----
    fund_status = Column(String, nullable=True)               # frozen / deducted / released
    fund_frozen_amount = Column(Float, nullable=True)
    fund_deducted_amount = Column(Float, nullable=True)

    # ---- 取消申请 ----
    cancel_apply_status = Column(String, nullable=True)       # pending / approved / rejected
    cancel_apply_reason = Column(String, nullable=True)
    cancel_apply_time = Column(DateTime, nullable=True)
    cancel_reject_reason = Column(String, nullable=True)


# ===== 资金池：每个回收商公司一条 =====
class RecyclerFundPool(Base):
    __tablename__ = "recycler_fund_pools"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, unique=True, index=True, nullable=False)
    balance = Column(Float, default=0)            # 总余额
    frozen_amount = Column(Float, default=0)      # 冻结中
    deducted_amount = Column(Float, default=0)    # 累计已扣款
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    # 可用余额 = balance - frozen_amount（不存库，查询时算）


# ===== 资金流水：逐条 =====
class FundFlow(Base):
    __tablename__ = "fund_flows"

    id = Column(Integer, primary_key=True, index=True)
    company_type = Column(String, nullable=False, default="recycler")
    operation_key = Column(String, nullable=True, unique=True)
    type = Column(String, nullable=False)   # recharge / freeze / release / deduct / platform_fee
    company_id = Column(Integer, index=True, nullable=False)
    order_no = Column(String, nullable=True)
    order_id = Column(Integer, nullable=True)
    merchant_id = Column(Integer, nullable=True)
    operator = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    remark = Column(String, nullable=True)
    status = Column(String, default="success")
    create_time = Column(DateTime, default=datetime.now)


# ===== 充值申请 =====
class RechargeApply(Base):
    __tablename__ = "recharge_applies"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, index=True, nullable=False)
    company_name = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    proof_image = Column(Text, nullable=True)
    apply_user_id = Column(Integer, nullable=True)
    status = Column(String, default="pending")      # pending / approved / rejected
    reject_reason = Column(String, nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    review_time = Column(DateTime, nullable=True)


# ===== 抽成比例：按用户 =====
class CommissionRate(Base):
    __tablename__ = "commission_rates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    company_id = Column(Integer, nullable=True)
    role = Column(String, nullable=True)            # merchant_owner / merchant_staff
    rate = Column(Float, default=0)                 # 0~1，例如 0.05 = 5%
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class MerchantDepositApply(Base):
    __tablename__ = "merchant_deposit_applies"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, nullable=False, index=True)
    applicant_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    remark = Column(Text, nullable=True)
    status = Column(String, default="pending")
    create_time = Column(DateTime, default=datetime.now)
    review_time = Column(DateTime, nullable=True)
    reviewer_id = Column(Integer, nullable=True)
    review_remark = Column(Text, nullable=True)
