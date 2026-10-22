import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import case

from models import CommissionRate, Device, DeviceInquiry, MerchantCompany, Order, Quote, RecyclerCompany, User


def dumps_json(data) -> str:
    if data is None:
        return "[]"
    return json.dumps(data, ensure_ascii=False)


def loads_json(text: Optional[str]) -> list:
    if not text:
        return []

    try:
        result = json.loads(text)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def loads_json_dict(text: Optional[str]) -> dict:
    if not text:
        return {}

    try:
        result = json.loads(text)
        return result if isinstance(result, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def format_datetime(value) -> str:
    if not value:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    return str(value)


def normalize_recycler_ids(raw_ids: list) -> list:
    normalized = []

    for item in raw_ids or []:
        if item is None or item == "":
            continue
        normalized.append(item)

    return normalized


def get_default_recycler_ids(db: Session) -> list:
    from models import RecyclerCompany

    recyclers = db.query(RecyclerCompany).order_by(RecyclerCompany.id.asc()).all()
    return [item.id for item in recyclers]


def serialize_device(device: Device) -> dict:
    images = loads_json(device.images)
    detail = loads_json_dict(getattr(device, "detail_json", None))

    return {
        "device_type": device.device_type,
        "brand": device.brand,
        "model": device.model,
        "condition": device.condition or "",
        "fault_desc": device.fault_desc or "",
        "images": images,
        "storage": getattr(device, "storage", "") or "",
        "color": getattr(device, "color", "") or "",
        "channel": getattr(device, "channel", "") or "",
        "warranty": getattr(device, "warranty", "") or "",
        "detail": detail
    }


def device_detail_fields(device: Device) -> dict:
    """把设备的基础规格 + 逐项检测结果摊平成顶层字段，方便各端口直接读取展示。"""
    if not device:
        return {}

    detail = loads_json_dict(getattr(device, "detail_json", None))

    flat = {
        "storage": getattr(device, "storage", "") or "",
        "color": getattr(device, "color", "") or "",
        "channel": getattr(device, "channel", "") or "",
        "warranty": getattr(device, "warranty", "") or "",
    }

    if isinstance(detail, dict):
        for key, value in detail.items():
            if value not in (None, ""):
                flat[key] = value

    return flat



def inquiry_deadline(inquiry):
    return inquiry.create_time + timedelta(minutes=10)


def inquiry_has_ended(db, inquiry):
    return inquiry.status not in ("pending_quote", "quoted") or datetime.now() >= inquiry_deadline(inquiry) or db.query(Order.id).filter(Order.inquiry_id == inquiry.id).first() is not None


def merchant_quote_amounts(db, quote):
    from money_utils import build_amount_snapshot
    order = db.query(Order).filter(Order.quote_id == quote.id).first()
    if order and order.merchant_base_amount is not None:
        return {
            "merchant_base_amount": order.merchant_base_amount,
            "merchant_owner_commission": order.merchant_owner_commission or 0,
            "merchant_staff_commission": order.merchant_staff_commission or 0,
        }
    merchant = db.query(User).filter(User.id == quote.merchant_id).first()
    inquiry = db.get(DeviceInquiry, quote.inquiry_id)
    company_id = inquiry_merchant_company_id(db, inquiry) if inquiry else None
    company = db.get(MerchantCompany, company_id) if company_id else None
    owner = db.query(CommissionRate).filter(CommissionRate.user_id == company.owner_user_id).first() if company else None
    staff = db.query(CommissionRate).filter(CommissionRate.user_id == merchant.id).first() if merchant and merchant.role == "merchant_staff" else None
    return build_amount_snapshot(quote.price, owner.rate if owner else 0, staff.rate if staff else 0)


def serialize_inquiry_item(
    db: Session,
    inquiry: DeviceInquiry,
    device: Device,
    include_merchant: bool = False
) -> dict:
    recycler_ids = loads_json(inquiry.recycler_company_ids)
    device_data = serialize_device(device)
    order = db.query(Order).filter(Order.inquiry_id == inquiry.id).first()
    status = order.status if order else ("expired" if datetime.now() >= inquiry_deadline(inquiry) else inquiry.status)

    item = {
        "id": inquiry.id,
        "device_id": inquiry.device_id,
        "merchant_id": inquiry.merchant_id,
        "status": status,
        "quoteStatus": "accepted" if order else status,
        "selectedRecyclerCompanyId": order.recycler_company_id if order else None,
        "quote_deadline": format_datetime(inquiry_deadline(inquiry)),
        "can_quote": not inquiry_has_ended(db, inquiry),
        "recyclerCompanyIds": recycler_ids,
        "recycler_company_ids": recycler_ids,
        "created_at": format_datetime(inquiry.create_time),
        "createTime": format_datetime(inquiry.create_time),
        "no": f"XJ{inquiry.id}",
        "deviceType": device.device_type,
        "device_type": device.device_type,
        "brand": device.brand,
        "model": device.model,
        "condition": device.condition or "",
        "fault_desc": device.fault_desc or "",
        "remark": device.fault_desc or "",
        "images": device_data["images"],
        "device": device_data,
        "quotes": [],
        **device_detail_fields(device)
    }

    if include_merchant:
        merchant_user = db.query(User).filter(User.id == inquiry.merchant_id).first()
        company_name = ""

        company_id = inquiry_merchant_company_id(db, inquiry)
        if company_id:
            company = db.query(MerchantCompany).filter(
                MerchantCompany.id == company_id
            ).first()
            company_name = company.company_name if company else ""

        item["merchantCompanyName"] = company_name
        item["merchantCompanyId"] = company_id
        item["merchant"] = {
            "id": merchant_user.id if merchant_user else inquiry.merchant_id,
            "name": merchant_user.username if merchant_user else "",
            "company_name": company_name
        }

    return item


def is_visible_to_recycler_company(recycler_company_ids: list, company_id) -> bool:
    if not recycler_company_ids:
        return True

    company_id_str = str(company_id)

    for item in recycler_company_ids:
        if str(item) == company_id_str:
            return True
        try:
            if int(item) == int(company_id):
                return True
        except (TypeError, ValueError):
            continue

    return False


def inquiry_merchant_company_id(db: Session, inquiry: DeviceInquiry):
    order = db.query(Order).filter(Order.inquiry_id == inquiry.id).first()
    if order:
        return order.merchant_company_id
    if inquiry.merchant_company_id is not None:
        return inquiry.merchant_company_id
    merchant = db.get(User, inquiry.merchant_id)
    return merchant.company_id if merchant and merchant.company_type == "merchant" else None


def get_merchant_inquiries(db: Session, user: User) -> List[DeviceInquiry]:
    if user.role not in ("merchant_owner", "merchant_staff") or not user.company_id:
        return []
    company_id = case((Order.id.isnot(None), Order.merchant_company_id), (DeviceInquiry.merchant_company_id.isnot(None), DeviceInquiry.merchant_company_id), else_=User.company_id)
    query = db.query(DeviceInquiry).outerjoin(Order, Order.inquiry_id == DeviceInquiry.id).outerjoin(
        User, User.id == DeviceInquiry.merchant_id
    ).filter(company_id == user.company_id)
    if user.role == "merchant_staff" and not user.can_view_all_inquiry:
        query = query.filter(DeviceInquiry.merchant_id == user.id)
    return query.order_by(DeviceInquiry.id.desc()).all()


def get_device_inquiry(db: Session, inquiry_id: int) -> Optional[DeviceInquiry]:
    return db.query(DeviceInquiry).filter(DeviceInquiry.id == inquiry_id).first()


def merchant_can_access_inquiry(db: Session, user: User, inquiry: DeviceInquiry) -> bool:
    if user.role not in ("merchant_owner", "merchant_staff"):
        return False
    if not user.company_id or inquiry_merchant_company_id(db, inquiry) != user.company_id:
        return False
    if user.role == "merchant_owner" or user.can_view_all_inquiry:
        return True
    return inquiry.merchant_id == user.id


def get_quote_valid_days(quote: Quote) -> int:
    if quote.valid_days:
        return quote.valid_days

    if quote.valid_hours:
        return max(1, int(quote.valid_hours / 24))

    return 3


def get_recycler_company_name(db: Session, company_id: int) -> str:
    company = db.query(RecyclerCompany).filter(
        RecyclerCompany.id == company_id
    ).first()
    return company.company_name if company else ""


def serialize_quote_for_recycler(
    db: Session,
    quote: Quote,
    include_inquiry: bool = True
) -> dict:
    recycler_user = db.query(User).filter(User.id == quote.quote_user_id).first()
    device = None

    if quote.device_id:
        device = db.query(Device).filter(Device.id == quote.device_id).first()

    item = {
        "id": quote.id,
        "inquiry_id": quote.inquiry_id,
        "device_id": quote.device_id,
        "merchant_id": quote.merchant_id,
        "recycler_id": quote.quote_user_id,
        "recycler_company_id": quote.recycler_company_id,
        "price": quote.price,
        "valid_days": get_quote_valid_days(quote),
        "remark": quote.remark or "",
        "status": quote.status,
        "created_at": format_datetime(quote.create_time),
        "quoteTime": format_datetime(quote.create_time),
        "recyclerCompanyId": quote.recycler_company_id,
        "recyclerCompanyName": quote.recycler_company_name or "",
        "quoteUserId": quote.quote_user_id,
        "quoteUserName": quote.quote_user_name or "",
        "amount": quote.price,
        "recyclerQuoteAmount": quote.price
    }

    if device:
        item["device"] = serialize_device(device)

    if include_inquiry:
        inquiry = get_device_inquiry(db, quote.inquiry_id)

        if inquiry and device:
            item["inquiry"] = serialize_inquiry_item(db, inquiry, device, include_merchant=True)

    return item


def serialize_quote_for_merchant(db: Session, quote: Quote, viewer: User = None) -> dict:
    recycler_user = db.query(User).filter(User.id == quote.quote_user_id).first()
    company_name = quote.recycler_company_name or get_recycler_company_name(
        db,
        quote.recycler_company_id
    )

    snapshot = merchant_quote_amounts(db, quote)
    own_commission = snapshot["merchant_owner_commission"] if viewer and viewer.role == "merchant_owner" else snapshot["merchant_staff_commission"]
    return {
        "id": quote.id,
        "inquiry_id": quote.inquiry_id,
        "device_id": quote.device_id,
        "price": snapshot["merchant_base_amount"],
        "valid_days": get_quote_valid_days(quote),
        "validDays": get_quote_valid_days(quote),
        "remark": quote.remark or "",
        "status": quote.status,
        "quoteStatus": quote.status,
        "created_at": format_datetime(quote.create_time),
        "quoteTime": format_datetime(quote.create_time),
        "recyclerCompanyId": quote.recycler_company_id,
        "recyclerCompanyName": company_name,
        "quoteUserId": quote.quote_user_id,
        "quoteUserName": quote.quote_user_name or (recycler_user.username if recycler_user else ""),
        "amount": snapshot["merchant_base_amount"],
        "merchantBaseAmount": snapshot["merchant_base_amount"],
        "merchantDisplayAmount": int(max(0, snapshot["merchant_base_amount"] - snapshot["merchant_owner_commission"] - snapshot["merchant_staff_commission"])),
        "myCommission": own_commission,
        "recycler": {
            "id": quote.quote_user_id,
            "name": quote.quote_user_name or (recycler_user.username if recycler_user else ""),
            "company_id": quote.recycler_company_id,
            "company_name": company_name
        }
    }


def generate_order_no() -> str:
    suffix = str(random.randint(0, 9999)).zfill(4)
    return f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"


def serialize_quote_brief(quote: Quote) -> dict:
    return {
        "price": quote.price,
        "valid_days": get_quote_valid_days(quote),
        "remark": quote.remark or ""
    }


def serialize_order_lifecycle_fields(order: Order) -> dict:
    merchant_confirm_time_text = format_datetime(order.merchant_confirm_time) if order.merchant_confirm_time else ""
    appeal_time_text = format_datetime(order.appeal_time) if order.appeal_time else ""
    close_time_text = format_datetime(order.close_time) if order.close_time else ""
    cancel_apply_time_text = format_datetime(order.cancel_apply_time) if order.cancel_apply_time else ""

    return {
        "merchant_confirm_time": merchant_confirm_time_text,
        "merchantConfirmTime": merchant_confirm_time_text,
        "appeal_reason": order.appeal_reason or "",
        "appealReason": order.appeal_reason or "",
        "appeal_time": appeal_time_text,
        "appealTime": appeal_time_text,
        "close_reason": order.close_reason or "",
        "closeReason": order.close_reason or "",
        "close_time": close_time_text,
        "closeTime": close_time_text,
        "cancel_apply_status": order.cancel_apply_status or "",
        "cancelApplyStatus": order.cancel_apply_status or "",
        "cancel_apply_reason": order.cancel_apply_reason or "",
        "cancelApplyReason": order.cancel_apply_reason or "",
        "cancel_apply_time": cancel_apply_time_text,
        "cancelApplyTime": cancel_apply_time_text,
        "cancel_reject_reason": order.cancel_reject_reason or "",
        "cancelRejectReason": order.cancel_reject_reason or ""
    }


def serialize_order(
    db: Session,
    order: Order,
    quote: Optional[Quote] = None,
    device: Optional[Device] = None,
    viewer: Optional[User] = None
) -> dict:
    if quote is None:
        quote = db.query(Quote).filter(Quote.id == order.quote_id).first()

    if device is None and order.device_id:
        device = db.query(Device).filter(Device.id == order.device_id).first()

    merchant_user = db.query(User).filter(User.id == order.merchant_id).first()
    recycler_user = db.query(User).filter(User.id == order.recycler_id).first()

    merchant_company_name = ""
    if order.merchant_company_id:
        company = db.query(MerchantCompany).filter(
            MerchantCompany.id == order.merchant_company_id
        ).first()
        merchant_company_name = company.company_name if company else ""

    recycler_company_name = get_recycler_company_name(db, order.recycler_company_id)
    device_data = serialize_device(device) if device else {}

    order_price = order.price if order.price is not None else order.accepted_price
    shipping_images = loads_json(order.shipping_images)
    ship_time_text = format_datetime(order.ship_time) if order.ship_time else ""
    receive_time_text = format_datetime(order.receive_time) if order.receive_time else ""
    inspection_time_text = format_datetime(order.inspection_time) if order.inspection_time else ""

    result = {
        "id": order.id,
        "order_no": order.order_no,
        "orderNo": order.order_no,
        "inquiry_id": order.inquiry_id,
        "quote_id": order.quote_id,
        "device_id": order.device_id,
        "merchant_id": order.merchant_id,
        "recycler_id": order.recycler_id,
        "recycler_company_id": order.recycler_company_id,
        "price": order_price,
        "status": order.status,
        "express_company": order.express_company or "",
        "tracking_no": order.tracking_no or "",
        "shipping_images": shipping_images,
        "ship_time": ship_time_text,
        "receive_time": receive_time_text,
        "expressCompany": order.express_company or "",
        "trackingNo": order.tracking_no or "",
        "shippingImages": shipping_images,
        "shipTime": ship_time_text,
        "receiveTime": receive_time_text,
        "inspection_type": order.inspection_type or "",
        "inspection_price": order.inspection_price,
        "inspection_reason": order.inspection_reason or "",
        "inspection_time": inspection_time_text,
        "inspectionType": order.inspection_type or "",
        "inspectionPrice": order.inspection_price,
        "inspectionReason": order.inspection_reason or "",
        "inspectionTime": inspection_time_text,
        **serialize_order_lifecycle_fields(order),
        # ---- 金额快照(商家可见金额=报价+2%服务费;抽成在订单完成后用于结算/分析) ----
        "recycler_quote_amount": order.recycler_quote_amount,
        "selectedRecyclerQuoteAmount": order.recycler_quote_amount,
        "platform_fee_rate": order.platform_fee_rate,
        "platform_fee_amount": order.platform_fee_amount,
        "selectedPlatformFeeAmount": order.platform_fee_amount,
        "merchant_base_amount": order.merchant_base_amount,
        "selectedMerchantBaseAmount": order.merchant_base_amount,
        "merchant_owner_commission": order.merchant_owner_commission,
        "selectedMerchantOwnerCommission": order.merchant_owner_commission,
        "merchant_staff_commission": order.merchant_staff_commission,
        "selectedMerchantStaffCommission": order.merchant_staff_commission,
        "merchant_real_amount": order.merchant_real_amount,
        "selectedMerchantRealAmount": order.merchant_real_amount,
        "merchant_display_amount": order.merchant_display_amount,
        "selectedMerchantDisplayAmount": order.merchant_display_amount,
        "created_at": format_datetime(order.create_time),
        "updated_at": format_datetime(order.update_time or order.create_time),
        "device": device_data,
        "deviceType": device.device_type if device else "",
        "brand": device.brand if device else "",
        "model": device.model if device else "",
        "condition": device.condition if device else "",
        "fault_desc": device.fault_desc if device else "",
        "remark": device.fault_desc if device else "",
        **device_detail_fields(device),
        "merchant": {
            "id": order.merchant_id,
            "name": merchant_user.username if merchant_user else "",
            "company_id": order.merchant_company_id,
            "company_name": merchant_company_name
        },
        "recycler": {
            "id": order.recycler_id,
            "name": recycler_user.username if recycler_user else "",
            "company_id": order.recycler_company_id,
            "company_name": recycler_company_name
        },
        "quote": serialize_quote_brief(quote) if quote else {}
    }


    from models import RecyclerCompany
    recipient=db.get(RecyclerCompany,order.recycler_company_id)
    result["recycler"].update({key:(getattr(recipient,key,None) or "") for key in ("contact_name","contact_phone","address")})
    result["settlement_mode"] = order.settlement_mode
    result["fund_status"] = order.fund_status or "unsettled"
    result["fund_deducted_amount"] = order.fund_deducted_amount or 0
    result["selectedMerchantOwnerRate"] = order.merchant_owner_rate or 0
    result["selectedMerchantStaffRate"] = order.merchant_staff_rate or 0
    result["merchantDisplayAmount"] = int(max(0, (order.merchant_base_amount or 0) - (order.merchant_owner_commission or 0) - (order.merchant_staff_commission or 0)))
    if viewer and viewer.role in ("merchant_owner", "merchant_staff"):
        # Enforce price confidentiality in the response, including nested quote/inspection fields.
        for key in ("recycler_quote_amount", "selectedRecyclerQuoteAmount", "platform_fee_rate", "platform_fee_amount", "selectedPlatformFeeAmount", "selectedMerchantOwnerCommission", "merchant_owner_commission", "selectedMerchantStaffCommission", "merchant_staff_commission", "selectedMerchantOwnerRate", "selectedMerchantStaffRate", "fund_deducted_amount"):
            result.pop(key, None)
        result["price"] = order.merchant_base_amount
        result["quote"] = {"price": order.merchant_base_amount, "remark": quote.remark if quote else ""}
        result["myCommission"] = (order.merchant_owner_commission if viewer.role == "merchant_owner" else order.merchant_staff_commission) or 0
        result["myCommissionRate"] = (order.merchant_owner_rate if viewer.role == "merchant_owner" else order.merchant_staff_rate) or 0
        if viewer.role == "merchant_owner":
            result["selectedMerchantOwnerCommission"] = order.merchant_owner_commission or 0
            result["selectedMerchantStaffCommission"] = order.merchant_staff_commission or 0
        else:
            result["selectedMerchantStaffCommission"] = order.merchant_staff_commission or 0
        if order.inspection_price is not None:
            from money_utils import round2
            net_inspection = round2(order.inspection_price * (1 - (order.platform_fee_rate or 0.02)))
            result["inspection_price"] = result["inspectionPrice"] = net_inspection
    return result


def serialize_admin_merchant(db: Session, merchant_id: int) -> dict:
    merchant_user = db.query(User).filter(User.id == merchant_id).first()
    company_name = ""

    if merchant_user and merchant_user.company_id:
        company = db.query(MerchantCompany).filter(
            MerchantCompany.id == merchant_user.company_id
        ).first()
        company_name = company.company_name if company else ""

    return {
        "id": merchant_user.id if merchant_user else merchant_id,
        "name": merchant_user.username if merchant_user else "",
        "phone": merchant_user.phone if merchant_user else "",
        "company_name": company_name
    }


def serialize_admin_quote(db: Session, quote: Quote) -> dict:
    recycler_user = db.query(User).filter(User.id == quote.quote_user_id).first()
    company_name = quote.recycler_company_name or get_recycler_company_name(
        db,
        quote.recycler_company_id
    )

    return {
        "id": quote.id,
        "price": quote.price,
        "valid_days": get_quote_valid_days(quote),
        "remark": quote.remark or "",
        "status": quote.status,
        "recycler_id": quote.quote_user_id,
        "recycler_company_id": quote.recycler_company_id,
        "recycler_name": quote.quote_user_name or (
            recycler_user.username if recycler_user else ""
        ),
        "recycler_company_name": company_name,
        "created_at": format_datetime(quote.create_time)
    }


def serialize_admin_trade_order(db: Session, order: Order) -> dict:
    order_price = order.price if order.price is not None else order.accepted_price

    return {
        "id": order.id,
        "order_no": order.order_no,
        "orderNo": order.order_no,
        "status": order.status,
        "price": order_price,
        "express_company": order.express_company or "",
        "tracking_no": order.tracking_no or "",
        "expressCompany": order.express_company or "",
        "trackingNo": order.tracking_no or "",
        "ship_time": format_datetime(order.ship_time),
        "shipTime": format_datetime(order.ship_time),
        "receive_time": format_datetime(order.receive_time),
        "receiveTime": format_datetime(order.receive_time),
        "inspection_type": order.inspection_type or "",
        "inspection_price": order.inspection_price,
        "inspection_reason": order.inspection_reason or "",
        "inspection_time": format_datetime(order.inspection_time),
        "inspectionType": order.inspection_type or "",
        "inspectionPrice": order.inspection_price,
        "inspectionReason": order.inspection_reason or "",
        "inspectionTime": format_datetime(order.inspection_time),
        **serialize_order_lifecycle_fields(order),
        "recycler_company_id": order.recycler_company_id,
        "recycler_company_name": get_recycler_company_name(db, order.recycler_company_id)
    }


def compute_admin_trade_status(
    order: Optional[Order],
    quotes: List[Quote]
) -> str:
    if order:
        return order.status

    active_quotes = [
        quote for quote in quotes
        if quote.status not in ("cancelled", "expired")
    ]

    if active_quotes:
        return "quoted"

    return "pending_quote"


def serialize_admin_trade(
    db: Session,
    inquiry: DeviceInquiry,
    device: Device,
    quotes: List[Quote],
    order: Optional[Order] = None
) -> dict:
    trade_status = compute_admin_trade_status(order, quotes)
    merchant = serialize_admin_merchant(db, inquiry.merchant_id)
    if order:
        company = db.get(MerchantCompany, order.merchant_company_id) if order.merchant_company_id else None
        merchant["company_name"] = company.company_name if company else ""
    quotes_data = [serialize_admin_quote(db, quote) for quote in quotes]
    order_data = serialize_admin_trade_order(db, order) if order else None

    selected_recycler_company_name = ""
    selected_amount = 0

    if order:
        selected_recycler_company_name = order_data.get("recycler_company_name") or ""
        selected_amount = order_data.get("price") or 0
    elif quotes:
        accepted_quote = next(
            (quote for quote in quotes if quote.status == "accepted"),
            None
        )
        target_quote = accepted_quote or quotes[-1]
        selected_recycler_company_name = target_quote.recycler_company_name or get_recycler_company_name(
            db,
            target_quote.recycler_company_id
        )
        if not order:
            prices = [quote.price for quote in quotes if quote.status not in ("cancelled", "expired")]
            selected_amount = max(prices) if prices else 0

    prices = [
        quote.price for quote in quotes
        if quote.status not in ("cancelled", "expired")
    ]
    min_quote_price = min(prices) if prices else None
    max_quote_price = max(prices) if prices else None

    return {
        "id": inquiry.id,
        "inquiry_id": inquiry.id,
        "device_id": inquiry.device_id,
        "merchant_id": inquiry.merchant_id,
        "status": trade_status,
        "trade_status": trade_status,
        "tradeStatus": trade_status,
        "created_at": format_datetime(inquiry.create_time),
        "createTime": format_datetime(inquiry.create_time),
        "device": serialize_device(device),
        "merchant": merchant,
        "quotes": quotes_data,
        "order": order_data,
        "brand": device.brand,
        "model": device.model,
        "merchantCompanyName": merchant.get("company_name") or merchant.get("name") or "-",
        "merchantPhone": merchant.get("phone") or "",
        "selectedRecyclerCompanyName": selected_recycler_company_name,
        "selectedAmount": order_data.get("price") if order_data else selected_amount,
        "quoteCount": len(quotes_data),
        "minQuotePrice": min_quote_price,
        "maxQuotePrice": max_quote_price,
        "orderNo": order_data.get("order_no") if order_data else "",
        "orderId": order_data.get("id") if order_data else None,
        "expressCompany": order_data.get("express_company") if order_data else "",
        "expressNo": order_data.get("tracking_no") if order_data else "",
        "cancelApplyStatus": order_data.get("cancelApplyStatus") if order_data else "",
        "cancelApplyReason": order_data.get("cancelApplyReason") if order_data else "",
        "cancelApplyTime": order_data.get("cancelApplyTime") if order_data else ""
    }


def get_admin_trades(db: Session) -> List[dict]:
    inquiries = db.query(DeviceInquiry).order_by(DeviceInquiry.id.desc()).all()

    if not inquiries:
        return []

    inquiry_ids = [inquiry.id for inquiry in inquiries]
    device_ids = [inquiry.device_id for inquiry in inquiries]

    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
    devices_map = {device.id: device for device in devices}

    quotes_map = defaultdict(list)
    quotes = db.query(Quote).filter(
        Quote.inquiry_id.in_(inquiry_ids)
    ).order_by(Quote.id.asc()).all()

    for quote in quotes:
        quotes_map[quote.inquiry_id].append(quote)

    orders_map = {}
    orders = db.query(Order).filter(Order.inquiry_id.in_(inquiry_ids)).all()

    for order in orders:
        orders_map[order.inquiry_id] = order

    result = []

    for inquiry in inquiries:
        device = devices_map.get(inquiry.device_id)

        if not device:
            continue

        result.append(
            serialize_admin_trade(
                db,
                inquiry,
                device,
                quotes_map.get(inquiry.id, []),
                orders_map.get(inquiry.id)
            )
        )

    return result


def merchant_can_access_order(db: Session, user: User, order: Order) -> bool:
    if user.role not in ("merchant_owner", "merchant_staff"):
        return False
    if not user.company_id or order.merchant_company_id != user.company_id:
        return False
    if user.role == "merchant_owner" or user.can_view_all_inquiry:
        return True
    return order.merchant_id == user.id


def recycler_can_access_order(db: Session, user: User, order: Order) -> bool:
    if user.role not in ("recycler_owner", "recycler_staff", "recycler_keeper"):
        return False

    if not user.company_id:
        return False

    if int(order.recycler_company_id) != int(user.company_id):
        return False

    if user.role in ("recycler_owner", "recycler_keeper"):
        return True

    if user.role == "recycler_staff":
        return order.recycler_id == user.id

    return False


def get_orders_for_user(db: Session, user: User) -> List[Order]:
    query = db.query(Order).order_by(Order.id.desc())

    if user.role == "platform_admin":
        return query.all()

    if user.role == "merchant_owner":
        # 商家老板可看本公司全部订单（含员工创建/成交的），否则老板找不到员工的单去发货
        return query.filter(Order.merchant_company_id == user.company_id).all()

    if user.role == "merchant_staff":
        if user.can_view_all_inquiry:
            return query.filter(Order.merchant_company_id == user.company_id).all()
        return query.filter(Order.merchant_id == user.id, Order.merchant_company_id == user.company_id).all()

    if user.role in ("recycler_owner", "recycler_keeper"):
        return query.filter(Order.recycler_company_id == user.company_id).all()

    if user.role == "recycler_staff":
        return query.filter(
            Order.recycler_company_id == user.company_id,
            Order.recycler_id == user.id
        ).all()

    return []
