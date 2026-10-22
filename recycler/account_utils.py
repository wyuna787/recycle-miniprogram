from datetime import datetime

from sqlalchemy.orm import Session

from models import MerchantCompany, RecyclerCompany, User


def format_datetime(value):
    if not value:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")

    return str(value)


def get_company_name(db: Session, company_type: str, company_id):
    if company_type == "platform" or not company_id:
        return "平台"

    if company_type == "merchant":
        company = db.query(MerchantCompany).filter(
            MerchantCompany.id == company_id
        ).first()
        return company.company_name if company else ""

    if company_type == "recycler":
        company = db.query(RecyclerCompany).filter(
            RecyclerCompany.id == company_id
        ).first()
        return company.company_name if company else ""

    return ""


def build_user_info(db: Session, user: User) -> dict:
    role = user.role

    return {
        "id": user.id,
        "phone": user.phone,
        "username": user.username,
        "nickname": user.username,
        "role": role,
        "company_type": user.company_type,
        "company_id": user.company_id or 0,
        "company_name": get_company_name(db, user.company_type, user.company_id),
        "status": user.status,
        "can_create_inquiry": role == "merchant_owner" or (role == "merchant_staff" and bool(user.can_create_inquiry)),
        "can_view_all_inquiry": role == "merchant_owner" or (role == "merchant_staff" and bool(user.can_view_all_inquiry)),
        "can_accept_quote": role == "merchant_owner" or (role == "merchant_staff" and bool(user.can_accept_quote)),
        "can_manage_staff": role in ("merchant_owner", "recycler_owner"),
        "can_recharge": role in ("recycler_owner", "recycler_keeper"),
        "can_sign": role in ("recycler_owner", "recycler_keeper"),
        "can_view_all_orders": role in ("recycler_owner", "recycler_keeper"),
        "can_view_trade_data": role in ("recycler_owner", "recycler_keeper"),
        "can_grab_order": role == "recycler_staff",
        "can_quote": role == "recycler_staff"
    }


def serialize_account(db: Session, user: User) -> dict:
    return {
        "id": user.id,
        "phone": user.phone,
        "nickname": user.username,
        "username": user.username,
        "role": user.role,
        "company_type": user.company_type,
        "company_id": user.company_id or 0,
        "company_name": get_company_name(db, user.company_type, user.company_id),
        "status": user.status,
        "apply_reason": user.apply_reason or "",
        "reject_reason": user.reject_reason or "",
        "created_at": format_datetime(user.create_time)
    }


def is_staff_role(role: str) -> bool:
    return role in ("merchant_staff", "recycler_staff", "recycler_keeper")


def check_employee_limit(db: Session, company_type: str, company_id: int):
    if not company_id:
        return False, "请选择所属公司"

    if company_type == "merchant":
        company = db.query(MerchantCompany).filter(
            MerchantCompany.id == company_id
        ).first()
        employee_limit = 20
    elif company_type == "recycler":
        company = db.query(RecyclerCompany).filter(
            RecyclerCompany.id == company_id
        ).first()
        employee_limit = company.employee_limit if company else 0
    else:
        return False, "公司不存在"

    if not company:
        return False, "公司不存在"

    staff_count = db.query(User).filter(
        User.company_type == company_type,
        User.company_id == company_id,
        User.role.in_(("merchant_staff", "recycler_staff", "recycler_keeper")),
        User.status.in_(["pending", "approved"])
    ).count()

    if staff_count >= employee_limit:
        return False, f"{company.company_name} 员工数量已达上限 {employee_limit} 人"

    return True, ""
