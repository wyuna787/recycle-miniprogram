from pydantic import BaseModel
from typing import Optional, List, Any


class CreateMerchantCompanyRequest(BaseModel):
    owner_user_id: int
    company_name: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None


class UpdateStaffPermissionRequest(BaseModel):
    can_create_inquiry: bool = True
    can_view_all_inquiry: bool = False
    can_accept_quote: bool = False
    can_manage_staff: bool = False


class CreateInquiryRequest(BaseModel):
    merchant_company_id: int
    merchant_company_name: str
    created_by_user_id: int
    created_by_user_name: str

    device_type: str
    brand: str
    model: str

    storage: Optional[str] = None
    color: Optional[str] = None
    channel: Optional[str] = None
    warranty: Optional[str] = None

    device_detail_json: Optional[str] = None
    photos_json: Optional[str] = None


class CreateQuoteRequest(BaseModel):
    inquiry_id: int
    recycler_company_id: int
    recycler_company_name: str
    quote_user_id: int
    quote_user_name: str
    quote_user_role: str
    price: float
    valid_hours: int = 24
    remark: Optional[str] = None


class AcceptQuoteRequest(BaseModel):
    user_id: int
    inquiry_id: int
    quote_id: int


class RegisterAccountRequest(BaseModel):
    phone: str
    nickname: str
    password: str
    role: str
    company_type: str
    company_id: Optional[int] = None
    new_company_name: Optional[str] = None  # 老板注册时新建公司名称
    apply_reason: Optional[str] = None


class LoginAccountRequest(BaseModel):
    phone: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class RejectAccountRequest(BaseModel):
    reason: str


class CreateDeviceRequest(BaseModel):
    device_type: str
    brand: str
    model: str
    condition: Optional[str] = "正常"
    fault_desc: Optional[str] = ""
    images: Optional[List[Any]] = []
    recyclerCompanyIds: Optional[List[Any]] = []

    # 设备明细
    storage: Optional[str] = None
    color: Optional[str] = None
    channel: Optional[str] = None
    warranty: Optional[str] = None
    detail: Optional[dict] = None


class CreateApiQuoteRequest(BaseModel):
    inquiry_id: int
    price: float
    valid_days: int = 3
    remark: Optional[str] = ""


class ShipOrderRequest(BaseModel):
    express_company: str
    tracking_no: str
    shipping_images: Optional[List[Any]] = []


class InspectOrderRequest(BaseModel):
    inspection_type: str
    inspection_price: Optional[float] = None
    inspection_reason: Optional[str] = ""


class ConfirmOrderRequest(BaseModel):
    confirm_remark: Optional[str] = ""


class AppealOrderRequest(BaseModel):
    appeal_reason: str


class CloseOrderRequest(BaseModel):
    close_reason: str


# ─────────────────────────────────────────────
# 资金相关
# ─────────────────────────────────────────────

class SetFundBalanceRequest(BaseModel):
    balance: float


class RechargeApplyRequest(BaseModel):
    company_id: int
    amount: float
    proof_image: Optional[str] = None


class RejectReasonRequest(BaseModel):
    reason: str


# ─────────────────────────────────────────────
# 抽成比例
# ─────────────────────────────────────────────

class SetCommissionRequest(BaseModel):
    user_id: int
    rate: float   # 0~1，如 0.05 = 5%


# ─────────────────────────────────────────────
# 取消申请
# ─────────────────────────────────────────────

class CancelApplyRequest(BaseModel):
    reason: str