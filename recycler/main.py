import time
import os
import uuid
import math
import unicodedata
from datetime import datetime, timedelta
from sqlalchemy import text
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_platform_admin,
    verify_password
)
from account_utils import (
    build_user_info,
    check_employee_limit,
    is_staff_role,
    serialize_account
)
from database import Base, engine, get_db, migrate_db
from models import (
    User,
    MerchantCompany,
    MerchantDepositApply,
    RecyclerCompany,
    Device,
    DeviceInquiry,
    Inquiry,
    Quote,
    Order,
    RecyclerFundPool,
    FundFlow,
    RechargeApply,
    CommissionRate,
)
from schemas import (
    CreateMerchantCompanyRequest,
    UpdateStaffPermissionRequest,
    CreateInquiryRequest,
    CreateQuoteRequest,
    AcceptQuoteRequest,
    RegisterAccountRequest,
    LoginAccountRequest,
    ChangePasswordRequest,
    RejectAccountRequest,
    CreateDeviceRequest,
    CreateApiQuoteRequest,
    ShipOrderRequest,
    InspectOrderRequest,
    ConfirmOrderRequest,
    AppealOrderRequest,
    CloseOrderRequest,
    SetFundBalanceRequest,
    RechargeApplyRequest,
    RejectReasonRequest,
    SetCommissionRequest,
    CancelApplyRequest,
)
from money_utils import build_amount_snapshot
from fund_utils import (
    freeze_fund,
    deduct_fund,
    release_if_frozen,
    record_recharge_flow,
    get_pool_info,
    get_available,
    _get_or_create_pool,
)
from trade_utils import (
    dumps_json,
    generate_order_no,
    get_default_recycler_ids,
    get_device_inquiry,
    get_merchant_inquiries,
    get_orders_for_user,
    get_recycler_company_name,
    is_visible_to_recycler_company,
    loads_json,
    merchant_can_access_inquiry,
    merchant_can_access_order,
    normalize_recycler_ids,
    recycler_can_access_order,
    serialize_device,
    serialize_inquiry_item,
    get_admin_trades,
    serialize_order,
    serialize_quote_for_merchant,
    serialize_quote_for_recycler,
    inquiry_deadline,
    inquiry_has_ended,
    merchant_quote_amounts,
)

# 创建数据库表并执行轻量迁移
Base.metadata.create_all(bind=engine)
migrate_db()

app = FastAPI(
    title="二手电子设备回收平台后端",
    version="0.1.0"
)

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 上传目录:保存设备图片、发货凭证、付款凭证等，并通过 /uploads 静态访问
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


@app.get("/")
def root():
    return {
        "message": "recycle backend running"
    }


@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        ext = ".jpg"

    filename = f"{uuid.uuid4().hex}{ext}"
    target = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空")

    with open(target, "wb") as f:
        f.write(content)

    url = f"/uploads/{filename}"

    return {
        "url": url,
        "path": url,
        "message": "上传成功"
    }


# -------------------------
# 初始化测试数据
# -------------------------
@app.post("/dev/init")
def init_dev_data(db: Session = Depends(get_db)):
    # 清空测试交易数据，避免重复调用 /dev/init 后累积询价和订单
    db.query(Order).delete()
    db.query(Quote).delete()
    db.query(DeviceInquiry).delete()
    db.query(Device).delete()
    db.query(Inquiry).delete()
    db.query(RecyclerFundPool).delete()
    db.query(FundFlow).delete()
    db.query(RechargeApply).delete()
    db.query(CommissionRate).delete()
    db.query(RecyclerCompany).delete()
    db.query(MerchantCompany).delete()
    db.query(User).delete()
    db.commit()

    # 平台管理员
    platform_admin = User(
        username="平台管理员",
        phone="30001",
        password_hash=hash_password("111"),
        role="platform_admin",
        company_type="platform",
        company_id=0,
        can_create_inquiry=False,
        can_view_all_inquiry=True,
        can_accept_quote=False,
        can_manage_staff=True,
        status="approved"
    )

    # 商家主账号
    merchant_owner = User(
        username="商家老板",
        phone="10001",
        password_hash=hash_password("111"),
        role="merchant_owner",
        company_type="merchant",
        can_create_inquiry=True,
        can_view_all_inquiry=True,
        can_accept_quote=True,
        can_manage_staff=True,
        status="approved"
    )

    # 商家员工账号
    merchant_staff = User(
        username="商家员工A",
        phone="10002",
        password_hash=hash_password("111"),
        role="merchant_staff",
        company_type="merchant",
        can_create_inquiry=True,
        can_view_all_inquiry=False,
        can_accept_quote=False,
        can_manage_staff=False,
        status="approved"
    )

    # 回收商A老板
    recycler_owner_a = User(
        username="回收商A老板",
        phone="20001",
        password_hash=hash_password("111"),
        role="recycler_owner",
        company_type="recycler",
        can_create_inquiry=False,
        can_view_all_inquiry=True,
        can_accept_quote=False,
        can_manage_staff=True,
        status="approved"
    )

    # 回收商A员工
    recycler_staff_a = User(
        username="回收商A员工1",
        phone="20002",
        password_hash=hash_password("111"),
        role="recycler_staff",
        company_type="recycler",
        can_create_inquiry=False,
        can_view_all_inquiry=False,
        can_accept_quote=False,
        can_manage_staff=False,
        status="approved"
    )

    db.add_all([
        platform_admin,
        merchant_owner,
        merchant_staff,
        recycler_owner_a,
        recycler_staff_a
    ])
    db.commit()

    db.refresh(merchant_owner)
    db.refresh(merchant_staff)
    db.refresh(recycler_owner_a)
    db.refresh(recycler_staff_a)

    # 创建商家公司
    merchant_company = MerchantCompany(
        company_name="默认商家公司",
        owner_user_id=merchant_owner.id,
        contact_name="王老板",
        contact_phone="13800000000",
        address="成都",
        join_code="M001888",
        status="active"
    )

    db.add(merchant_company)
    db.commit()
    db.refresh(merchant_company)

    merchant_owner.company_id = merchant_company.id
    merchant_staff.company_id = merchant_company.id

    # 创建固定四家回收商公司
    recycler_company_a = RecyclerCompany(
        company_name="回收商A",
        owner_user_id=recycler_owner_a.id,
        employee_limit=20,
        status="active"
    )

    recycler_company_b = RecyclerCompany(
        company_name="回收商B",
        owner_user_id=None,
        employee_limit=20,
        status="active"
    )

    recycler_company_c = RecyclerCompany(
        company_name="回收商C",
        owner_user_id=None,
        employee_limit=40,
        status="active"
    )

    recycler_company_d = RecyclerCompany(
        company_name="回收商D",
        owner_user_id=None,
        employee_limit=40,
        status="active"
    )

    db.add_all([
        recycler_company_a,
        recycler_company_b,
        recycler_company_c,
        recycler_company_d
    ])
    db.commit()

    db.refresh(recycler_company_a)

    recycler_owner_a.company_id = recycler_company_a.id
    recycler_staff_a.company_id = recycler_company_a.id

    db.commit()
    db.refresh(recycler_company_b)
    db.refresh(recycler_company_c)
    db.refresh(recycler_company_d)

    # 为每家回收商建初始资金池（测试初始余额 5000）
    for rc in [recycler_company_a, recycler_company_b, recycler_company_c, recycler_company_d]:
        db.add(RecyclerFundPool(
            company_id=rc.id,
            balance=5000.0,
            frozen_amount=0.0,
            deducted_amount=0.0,
        ))
    db.commit()

    return {
        "message": "测试数据初始化成功"
    }


# -------------------------
# 账号模块
# -------------------------
@app.get("/api/account/companies")
def get_account_companies(db: Session = Depends(get_db)):
    merchant_companies = db.query(MerchantCompany).join(User, MerchantCompany.owner_user_id == User.id).filter(
        MerchantCompany.status == "active", User.status == "approved", User.role == "merchant_owner",
        User.company_type == "merchant", User.company_id == MerchantCompany.id).order_by(
        MerchantCompany.id.asc()
    ).all()

    recycler_companies = db.query(RecyclerCompany).join(User, RecyclerCompany.owner_user_id == User.id).filter(
        RecyclerCompany.status == "active", User.status == "approved", User.role == "recycler_owner",
        User.company_type == "recycler", User.company_id == RecyclerCompany.id).order_by(
        RecyclerCompany.id.asc()
    ).all()

    return {
        "merchantCompanies": [
            {
                "id": item.id,
                "name": item.company_name,
                "employee_limit": 20
            }
            for item in merchant_companies
        ],
        "recyclerCompanies": [
            {
                "id": item.id,
                "name": item.company_name,
                "employee_limit": item.employee_limit
            }
            for item in recycler_companies
        ]
    }


def unique_company_name(db, raw_name):
    name = unicodedata.normalize("NFKC", raw_name or "").strip()
    key = "".join(name.split()).casefold()
    if not key:
        raise HTTPException(400, "请输入公司名称")
    for model in (MerchantCompany, RecyclerCompany):
        for company in db.query(model).all():
            existing = "".join(unicodedata.normalize("NFKC", company.company_name or "").split()).casefold()
            if existing == key:
                raise HTTPException(400, "该公司名称已存在，请使用不同名称；员工请选择已有公司注册")
    return name


@app.post("/api/account/register")
def register_account(data: RegisterAccountRequest, db: Session = Depends(get_db)):
    db.execute(text("BEGIN IMMEDIATE"))
    phone = data.phone.strip()

    if not phone:
        raise HTTPException(status_code=400, detail="请输入手机号")

    existed = db.query(User).filter(User.phone == phone).first()

    if existed:
        raise HTTPException(status_code=400, detail="该手机号已注册，请直接登录")

    if len(data.password) < 3:
        raise HTTPException(status_code=400, detail="密码至少3位")

    is_owner = data.role in ("merchant_owner", "recycler_owner")
    new_company_name = (data.new_company_name or "").strip()
    # 老板可新建公司：未选已有公司且填写了公司名称
    role_types = {"merchant_owner": "merchant", "merchant_staff": "merchant",
                  "recycler_owner": "recycler", "recycler_staff": "recycler", "recycler_keeper": "recycler"}
    if role_types.get(data.role) != data.company_type:
        raise HTTPException(400, "账号角色与公司类型不匹配")
    # 新老板账号必须创建独立公司，名称相同也不能继承旧公司历史数据。
    create_new_company = is_owner
    if is_owner and not new_company_name:
        raise HTTPException(400, "请输入新建公司名称，老板注册不能加入旧公司")
    if is_owner:
        new_company_name = unique_company_name(db, new_company_name)
    if is_staff_role(data.role):
        cls = MerchantCompany if data.company_type == "merchant" else RecyclerCompany
        company = db.query(cls).filter(cls.id == data.company_id, cls.status == "active").first()
        owner = db.get(User, company.owner_user_id) if company else None
        expected_role = "merchant_owner" if data.company_type == "merchant" else "recycler_owner"
        if (not company or not owner or owner.status != "approved" or owner.role != expected_role or
                owner.company_type != data.company_type or owner.company_id != company.id):
            raise HTTPException(400, "所属公司不存在、已清退或没有有效老板账号")

    if data.role != "platform_admin" and not data.company_id and not create_new_company:
        raise HTTPException(status_code=400, detail="请选择所属公司")

    if is_staff_role(data.role):
        ok, message = check_employee_limit(db, data.company_type, data.company_id)
        if not ok:
            raise HTTPException(status_code=400, detail=message)

    user = User(
        username=data.nickname.strip(),
        phone=phone,
        password_hash=hash_password(data.password),
        role=data.role,
        company_type=data.company_type,
        company_id=0 if data.role == "platform_admin" else (data.company_id or 0),
        apply_reason=data.apply_reason or "",
        status="pending"
    )

    db.add(user)
    db.flush()

    # 老板新建公司：先建用户拿到 id，再建公司并回填 company_id
    if create_new_company:
        if data.company_type == "merchant":
            company = MerchantCompany(
                company_name=new_company_name,
                owner_user_id=user.id,
                join_code=f"M{int(time.time())}",
                status="active",
            )
        else:
            company = RecyclerCompany(
                company_name=new_company_name,
                owner_user_id=user.id,
                employee_limit=20,
                status="active",
            )

        db.add(company)
        db.flush()

        user.company_id = company.id

        # 新回收商公司：初始化资金池（默认初始额度，与种子回收商一致，平台可再调整）
        if data.company_type == "recycler":
            pool = _get_or_create_pool(db, company.id)
            pool.balance = 0
            db.flush()

    db.commit()

    return {
        "message": "注册成功，请等待公司老板审核" if is_staff_role(data.role) else "注册成功，请等待平台管理员审核"
    }


@app.post("/api/account/login")
def login_account(data: LoginAccountRequest, db: Session = Depends(get_db)):
    phone = data.phone.strip()
    user = db.query(User).filter(User.phone == phone).first()

    if not user:
        raise HTTPException(status_code=404, detail="账号不存在，请先注册")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="密码错误")

    if user.status == "pending":
        raise HTTPException(
            status_code=403,
            detail={
                "status": "pending",
                "message": "账号待平台管理员审核"
            }
        )

    if user.status == "rejected":
        reason = (user.reject_reason or "").strip()
        message = f"平台管理员已驳回：{reason}" if reason else "平台管理员已驳回"
        raise HTTPException(
            status_code=403,
            detail={
                "status": "rejected",
                "message": message,
                "reject_reason": reason
            }
        )

    if user.status == "disabled":
        raise HTTPException(
            status_code=403,
            detail={
                "status": "disabled",
                "message": "账号已被平台清退，如有疑问请联系平台"
            }
        )

    if user.status != "approved":
        raise HTTPException(status_code=400, detail="账号状态异常，请联系管理员")

    token = create_access_token(user.id, user.session_version or 0)
    user_info = build_user_info(db, user)

    return {
        "token": token,
        "userInfo": user_info,
        "status": "approved",
        "message": "登录成功"
    }


@app.get("/api/company/staff")
def get_company_staff(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("merchant_owner", "recycler_owner"):
        raise HTTPException(status_code=403, detail="只有公司老板可以查看员工账号")

    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="当前账号未绑定公司")

    users = db.query(User).filter(
        User.company_id == current_user.company_id,
        User.company_type == current_user.company_type
    ).order_by(User.id.asc()).all()

    result = []
    for u in users:
        item = serialize_account(db, u)
        item.update({
            "can_create_inquiry": bool(u.can_create_inquiry),
            "can_view_all_inquiry": bool(u.can_view_all_inquiry),
            "can_accept_quote": bool(u.can_accept_quote),
            "can_manage_staff": bool(u.can_manage_staff),
            "is_self": u.id == current_user.id,
            "is_owner": u.role in ("merchant_owner", "recycler_owner")
        })
        result.append(item)

    return {
        "list": result
    }


@app.post("/api/account/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    old_password = (data.old_password or "").strip()
    new_password = (data.new_password or "").strip()

    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    if len(new_password) < 3:
        raise HTTPException(status_code=400, detail="新密码至少3位")

    if new_password == old_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码相同")

    current_user.password_hash = hash_password(new_password)
    db.commit()

    return {
        "message": "密码修改成功，请重新登录"
    }


@app.get("/api/account/me")
def get_account_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return {
        "userInfo": build_user_info(db, current_user)
    }


@app.get("/api/admin/accounts")
def get_all_accounts(
    status: str = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin)
):
    q = db.query(User)
    if status:
        q = q.filter(User.status == status)
    users = q.order_by(User.id.desc()).all()
    return {"list": [serialize_account(db, user) for user in users]}


@app.get("/api/admin/accounts/pending")
def get_pending_accounts(
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin)
):
    pending_users = db.query(User).filter(
        User.status == "pending", User.role.in_(["merchant_owner", "recycler_owner"])
    ).order_by(User.id.desc()).all()

    approved_count = db.query(User).filter(User.status == "approved").count()
    rejected_count = db.query(User).filter(User.status == "rejected").count()

    return {
        "list": [serialize_account(db, user) for user in pending_users],
        "stats": {
            "pending": len(pending_users),
            "approved": approved_count,
            "rejected": rejected_count
        }
    }


@app.get("/api/admin/trades")
def get_admin_trades_api(
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin)
):
    trade_list = get_admin_trades(db)

    return {
        "list": trade_list,
        "total": len(trade_list)
    }


@app.post("/api/admin/accounts/{account_id}/approve")
def approve_account(
    account_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin)
):
    user = db.query(User).filter(User.id == account_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")

    if user.status != "pending":
        raise HTTPException(status_code=400, detail="该账号不在待审核状态")

    if user.company_type in ("merchant", "recycler"):
        cls = MerchantCompany if user.company_type == "merchant" else RecyclerCompany
        company = db.get(cls, user.company_id) if user.company_id else None
        expected_owner_role = "merchant_owner" if user.company_type == "merchant" else "recycler_owner"
        if not company or company.status != "active":
            raise HTTPException(400, "所属公司不存在或已清退，请先核对公司归属")
        owner = db.get(User, company.owner_user_id) if company.owner_user_id else None
        if user.role == expected_owner_role:
            if company.owner_user_id != user.id:
                raise HTTPException(400, "老板账号与公司归属不一致，请先核对")
        elif is_staff_role(user.role):
            if (not owner or owner.status != "approved" or owner.role != expected_owner_role or
                    owner.company_type != user.company_type or owner.company_id != company.id):
                raise HTTPException(400, "所属公司没有有效老板账号，请先核对公司归属")
        else:
            raise HTTPException(400, "账号角色与公司类型不匹配")
    elif user.role != "platform_admin" or user.company_type != "platform":
        raise HTTPException(400, "账号角色与公司类型不匹配")

    user.status = "approved"
    user.reject_reason = ""
    db.commit()
    db.refresh(user)

    return {
        "message": "审核通过",
        "account": serialize_account(db, user)
    }


@app.post("/api/admin/accounts/{account_id}/reject")
def reject_account(
    account_id: int,
    data: RejectAccountRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin)
):
    reason = data.reason.strip()

    if not reason:
        raise HTTPException(status_code=400, detail="请输入驳回原因")

    user = db.query(User).filter(User.id == account_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")

    if user.status != "pending":
        raise HTTPException(status_code=400, detail="该账号不在待审核状态")

    user.status = "rejected"
    user.reject_reason = reason
    db.commit()
    db.refresh(user)

    return {
        "message": "已驳回",
        "account": serialize_account(db, user)
    }


@app.post("/api/admin/accounts/{account_id}/disable")
def disable_account(
    account_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin)
):
    """平台管理员清退(停用)一个已注册账号。清退后无法登录。"""
    user = db.query(User).filter(User.id == account_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    if user.role == "platform_admin":
        raise HTTPException(status_code=400, detail="不能清退平台管理员账号")

    user.status = "disabled"
    user.session_version = (user.session_version or 0) + 1
    db.commit()
    db.refresh(user)
    return {"message": "已清退", "account": serialize_account(db, user)}


@app.post("/api/admin/company/{company_type}/{company_id}/disable")
def disable_company(
    company_type: str,
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin)
):
    """平台管理员清退整个公司：停用该公司全部账号(老板+员工)。"""
    users = db.query(User).filter(
        User.company_type == company_type,
        User.company_id == company_id
    ).all()
    if not users:
        raise HTTPException(status_code=404, detail="该公司无账号")

    count = 0
    for u in users:
        if u.role != "platform_admin":
            u.status = "disabled"
            u.session_version = (u.session_version or 0) + 1
            count += 1

    if company_type == "merchant":
        company = db.query(MerchantCompany).filter(MerchantCompany.id == company_id).first()
    else:
        company = db.query(RecyclerCompany).filter(RecyclerCompany.id == company_id).first()
    if company:
        company.status = "removed"

    db.commit()
    return {"message": f"已清退该公司 {count} 个账号", "disabled_count": count}


@app.post("/api/admin/accounts/{account_id}/enable")
def enable_account(
    account_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin)
):
    """恢复被清退/驳回的账号(重新允许登录)。"""
    user = db.query(User).filter(User.id == account_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    if user.role in ("merchant_owner", "recycler_owner"):
        expected_type = "merchant" if user.role == "merchant_owner" else "recycler"
        cls = MerchantCompany if expected_type == "merchant" else RecyclerCompany
        company = db.get(cls, user.company_id) if user.company_id else None
        if (user.company_type != expected_type or not company or
                company.status != "active" or company.owner_user_id != user.id):
            raise HTTPException(400, "老板与公司归属不一致或公司已清退，请先核对后再恢复")
    if is_staff_role(user.role):
        cls = MerchantCompany if user.company_type == "merchant" else RecyclerCompany
        company = db.get(cls, user.company_id) if user.company_id else None
        owner = db.get(User, company.owner_user_id) if company else None
        expected_role = "merchant_owner" if user.company_type == "merchant" else "recycler_owner"
        if (user.company_type not in ("merchant", "recycler") or not company or
                company.status != "active" or not owner or owner.status != "approved" or
                owner.role != expected_role or owner.company_type != user.company_type or
                owner.company_id != company.id):
            raise HTTPException(400, "请先建立并审核通过公司老板账号，再恢复员工或库管")
    user.status = "approved"
    user.reject_reason = ""
    db.commit()
    db.refresh(user)
    return {"message": "已恢复", "account": serialize_account(db, user)}


# -------------------------
# 设备发布 + 询价查看（MVP）
# -------------------------
@app.post("/api/devices")
def create_device(
    data: CreateDeviceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("merchant_owner", "merchant_staff"):
        raise HTTPException(status_code=403, detail="只有商家账号可以发布设备")

    if current_user.role == "merchant_staff" and not current_user.can_create_inquiry:
        raise HTTPException(status_code=403, detail="你没有发起询价权限")

    recycler_ids = normalize_recycler_ids(data.recyclerCompanyIds)

    if not recycler_ids:
        recycler_ids = get_default_recycler_ids(db)

    device = Device(
        merchant_id=current_user.id,
        device_type=data.device_type,
        brand=data.brand,
        model=data.model,
        condition=data.condition or "正常",
        fault_desc=data.fault_desc or "",
        images=dumps_json(data.images or []),
        storage=data.storage or "",
        color=data.color or "",
        channel=data.channel or "",
        warranty=data.warranty or "",
        detail_json=dumps_json(data.detail or {})
    )

    db.add(device)
    db.flush()

    inquiry = DeviceInquiry(
        device_id=device.id,
        merchant_id=current_user.id,
        merchant_company_id=current_user.company_id,
        status="pending_quote",
        recycler_company_ids=dumps_json(recycler_ids)
    )

    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    return {
        "message": "发布成功，已生成询价",
        "device": serialize_device(device),
        "inquiry": serialize_inquiry_item(db, inquiry, device)
    }


@app.get("/api/inquiries/my")
def get_my_inquiries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("merchant_owner", "merchant_staff"):
        raise HTTPException(status_code=403, detail="只有商家账号可以查看询价")

    inquiries = get_merchant_inquiries(db, current_user)
    result = []
    quote_map = {}
    if inquiries:
        quotes = db.query(Quote).filter(Quote.inquiry_id.in_([i.id for i in inquiries]),
                                      Quote.status.in_(["quoted", "accepted"])).order_by(Quote.price.desc(), Quote.id.asc()).all()
        for quote in quotes:
            bucket = quote_map.setdefault(quote.inquiry_id, [])
            if len(bucket) < 5:
                bucket.append(serialize_quote_for_merchant(db, quote, current_user))

    for inquiry in inquiries:
        device = db.query(Device).filter(Device.id == inquiry.device_id).first()

        if not device:
            continue

        item = serialize_inquiry_item(db, inquiry, device)
        item["quotes"] = quote_map.get(inquiry.id, [])
        result.append(item)

    return {
        "list": result
    }


@app.get("/api/inquiries/recycler")
def get_recycler_inquiries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("recycler_owner", "recycler_staff", "recycler_keeper"):
        raise HTTPException(status_code=403, detail="只有回收商账号可以查看询价")

    company_id = current_user.company_id

    if not company_id:
        raise HTTPException(status_code=400, detail="当前账号未绑定回收商公司")

    company = db.query(RecyclerCompany).filter(RecyclerCompany.id == company_id).first()
    if not company or company.status != "active":
        raise HTTPException(403, "回收商公司不可用")
    inquiries = db.query(DeviceInquiry).filter(DeviceInquiry.create_time >= company.create_time).order_by(DeviceInquiry.id.desc()).all()

    # 已成交询价 → 只对中标回收商可见：建 inquiry_id → 中标回收商公司 映射
    order_recycler_map = {
        o.inquiry_id: o.recycler_company_id
        for o in db.query(Order).all()
    }

    result = []

    for inquiry in inquiries:
        recycler_ids = loads_json(inquiry.recycler_company_ids)

        if not is_visible_to_recycler_company(recycler_ids, company_id):
            continue

        # 该询价已被某回收商成交：其他回收商不再可见，仅中标回收商可见
        awarded_company_id = order_recycler_map.get(inquiry.id)
        if awarded_company_id is not None and int(awarded_company_id) != int(company_id):
            continue

        device = db.query(Device).filter(Device.id == inquiry.device_id).first()

        if not device:
            continue

        result.append(serialize_inquiry_item(db, inquiry, device, include_merchant=True))

    return {
        "list": result
    }


# -------------------------
# 报价（MVP）
# -------------------------
@app.post("/api/quotes")
def create_api_quote(
    data: CreateApiQuoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.execute(text("BEGIN IMMEDIATE"))
    if current_user.role not in ("recycler_owner", "recycler_staff"):
        raise HTTPException(status_code=403, detail="只有回收商账号可以报价")

    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="当前账号未绑定回收商公司")

    if not math.isfinite(data.price) or data.price <= 0:
        raise HTTPException(status_code=400, detail="报价金额必须大于 0")

    inquiry = get_device_inquiry(db, data.inquiry_id)

    if not inquiry:
        raise HTTPException(status_code=404, detail="询价单不存在")

    company = db.query(RecyclerCompany).filter(RecyclerCompany.id == current_user.company_id).first()
    if not company or company.status != "active" or inquiry.create_time < company.create_time:
        raise HTTPException(403, "当前公司无权对历史询价报价")
    if inquiry_has_ended(db, inquiry):
        raise HTTPException(400, "该询价已成交或报价时间已结束")
    available = get_available(db, current_user.company_id)
    if available < 5000:
        raise HTTPException(400, "回收商可用余额少于5000元，不能报价")
    if data.price > available:
        raise HTTPException(400, "报价超过回收商可用余额")

    recycler_ids = loads_json(inquiry.recycler_company_ids)

    if recycler_ids and not is_visible_to_recycler_company(
        recycler_ids,
        current_user.company_id
    ):
        raise HTTPException(status_code=403, detail="当前回收商公司无权对该询价报价")

    valid_days = data.valid_days if data.valid_days and data.valid_days > 0 else 3
    company_name = get_recycler_company_name(db, current_user.company_id)

    existing = db.query(Quote).filter(
        Quote.inquiry_id == inquiry.id,
        Quote.quote_user_id == current_user.id,
        Quote.recycler_company_id == current_user.company_id
    ).first()

    if existing:
        existing.price = data.price
        existing.valid_days = valid_days
        existing.valid_hours = valid_days * 24
        existing.remark = data.remark or ""
        existing.status = "quoted"
        existing.create_time = datetime.now()
        quote = existing
    else:
        quote = Quote(
            inquiry_id=inquiry.id,
            device_id=inquiry.device_id,
            merchant_id=inquiry.merchant_id,
            recycler_company_id=current_user.company_id,
            recycler_company_name=company_name,
            quote_user_id=current_user.id,
            quote_user_name=current_user.username,
            quote_user_role=current_user.role,
            price=data.price,
            valid_days=valid_days,
            valid_hours=valid_days * 24,
            remark=data.remark or "",
            status="quoted"
        )
        db.add(quote)

    if inquiry.status == "pending_quote":
        inquiry.status = "quoted"

    db.commit()
    db.refresh(quote)

    return {
        "message": "报价成功",
        "quote": serialize_quote_for_recycler(db, quote)
    }


@app.get("/api/quotes/lookup")
def lookup_company_quotes(
    number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("recycler_owner", "recycler_staff", "recycler_keeper"):
        raise HTTPException(403, "只有回收商账号可以查询报价")
    key = number.strip().upper()
    if not key or len(key) > 100:
        raise HTTPException(400, "请输入完整订单号或询价单号")
    order = db.query(Order).filter(Order.order_no == key).first()
    inquiry_id = order.inquiry_id if order else None
    if inquiry_id is None:
        raw_id = key[2:] if key.startswith("XJ") else key
        if not raw_id.isascii() or not raw_id.isdigit() or len(raw_id) > 12:
            return {"item": None}
        inquiry_id = int(raw_id)
    quotes = db.query(Quote).filter(
        Quote.inquiry_id == inquiry_id,
        Quote.recycler_company_id == current_user.company_id
    ).order_by(Quote.id.desc()).all()
    inquiry = db.query(DeviceInquiry).filter(DeviceInquiry.id == inquiry_id).first()
    if not quotes or not inquiry:
        return {"item": None}
    device = db.query(Device).filter(Device.id == inquiry.device_id).first()
    if not device:
        return {"item": None}
    order = db.query(Order).filter(Order.inquiry_id == inquiry_id).first()
    item = serialize_inquiry_item(db, inquiry, device, include_merchant=True)
    item["quotes"] = [serialize_quote_for_recycler(db, q, include_inquiry=False) for q in quotes]
    item["orderNo"] = order.order_no if order and order.recycler_company_id == current_user.company_id else ""
    item["selectedQuoteId"] = order.quote_id if order and order.recycler_company_id == current_user.company_id else None
    # 对其他公司的成交仅保留状态，不披露公司编号或订单号。
    item["selectedRecyclerCompanyId"] = current_user.company_id if order and order.recycler_company_id == current_user.company_id else None
    return {"item": item}


@app.get("/api/quotes/my")
def get_my_api_quotes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("recycler_owner", "recycler_staff", "recycler_keeper"):
        raise HTTPException(status_code=403, detail="只有回收商账号可以查看报价")

    query = db.query(Quote).filter(Quote.recycler_company_id == current_user.company_id)
    if current_user.role == "recycler_staff":
        query = query.filter(Quote.quote_user_id == current_user.id)
    quotes = query.order_by(Quote.id.desc()).all()

    return {
        "list": [serialize_quote_for_recycler(db, quote) for quote in quotes]
    }


@app.get("/api/quotes/by-inquiry/{inquiry_id}")
def get_quotes_by_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("merchant_owner", "merchant_staff"):
        raise HTTPException(status_code=403, detail="只有商家账号可以查看报价")

    inquiry = get_device_inquiry(db, inquiry_id)

    if not inquiry:
        raise HTTPException(status_code=404, detail="询价单不存在")

    if not merchant_can_access_inquiry(db, current_user, inquiry):
        raise HTTPException(status_code=403, detail="无权查看该询价的报价")

    quotes = db.query(Quote).filter(
        Quote.inquiry_id == inquiry_id
        , Quote.status.in_(["quoted", "accepted"])
    ).order_by(Quote.price.desc(), Quote.id.asc()).limit(5).all()

    return {
        "list": [serialize_quote_for_merchant(db, quote, current_user) for quote in quotes]
    }


# -------------------------
# 确认报价 + 订单（MVP）
# -------------------------
@app.post("/api/quotes/{quote_id}/accept")
def accept_api_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.execute(text("BEGIN IMMEDIATE"))
    if current_user.role not in ("merchant_owner", "merchant_staff"):
        raise HTTPException(status_code=403, detail="只有商家账号可以确认报价")

    quote = db.query(Quote).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if quote.status != "quoted":
        raise HTTPException(status_code=400, detail="该报价不可重复确认")

    inquiry = get_device_inquiry(db, quote.inquiry_id)

    if not inquiry:
        raise HTTPException(status_code=404, detail="询价单不存在")

    if not merchant_can_access_inquiry(db, current_user, inquiry):
        raise HTTPException(status_code=403, detail="无权确认该询价的报价")

    if current_user.role == "merchant_staff" and not current_user.can_accept_quote:
        raise HTTPException(403, "你没有确认报价权限")

    if inquiry.status == "confirmed":
        raise HTTPException(status_code=400, detail="该询价已确认，不能重复操作")

    existing_order = db.query(Order).filter(Order.inquiry_id == inquiry.id).first()

    if existing_order:
        raise HTTPException(status_code=400, detail="该询价已生成订单，不能重复确认")

    quote.status = "accepted"

    other_quotes = db.query(Quote).filter(
        Quote.inquiry_id == inquiry.id,
        Quote.id != quote.id,
        Quote.status == "quoted"
    ).all()

    for other in other_quotes:
        other.status = "expired"

    inquiry.status = "confirmed"

    merchant_user = db.query(User).filter(User.id == inquiry.merchant_id).first()
    merchant_company_id = inquiry.merchant_company_id or (merchant_user.company_id if merchant_user else None)

    # ── 读取抽成比例（快照用，找员工自己 + 公司老板） ──
    staff_cr = db.query(CommissionRate).filter(
        CommissionRate.user_id == inquiry.merchant_id
    ).first()
    staff_rate = ((staff_cr.rate if staff_cr else 0) or 0) if merchant_user and merchant_user.role == "merchant_staff" else 0

    owner_rate = 0.0
    if merchant_company_id:
        mc = db.query(MerchantCompany).filter(MerchantCompany.id == merchant_company_id).first()
        if mc:
            owner_cr = db.query(CommissionRate).filter(
                CommissionRate.user_id == mc.owner_user_id
            ).first()
            owner_rate = (owner_cr.rate if owner_cr else 0) or 0

    if owner_rate + staff_rate > 0.98:
        raise HTTPException(400, "老板及员工收益比例之和不能超过扣除平台费后的金额比例")
    snap = build_amount_snapshot(quote.price, owner_rate, staff_rate)

    order = Order(
        order_no=generate_order_no(),
        inquiry_id=inquiry.id,
        quote_id=quote.id,
        device_id=inquiry.device_id,
        merchant_id=inquiry.merchant_id,
        recycler_id=quote.quote_user_id,
        merchant_company_id=merchant_company_id,
        settlement_mode="ship" if (db.get(MerchantCompany, merchant_company_id) and float(db.get(MerchantCompany, merchant_company_id).deposit_amount or 0)>0) else "receive",
        recycler_company_id=quote.recycler_company_id,
        price=quote.price,
        accepted_price=quote.price,
        status="confirmed",
        **snap,
    )

    db.add(order)
    db.flush()  # 先 flush 获取 order.id

    if get_available(db, quote.recycler_company_id) < 5000:
        raise HTTPException(400, "回收商可用余额少于5000元，不能成交")
    frozen = freeze_fund(db, quote.recycler_company_id, quote.price,
                         order_id=order.id, order_no=order.order_no, merchant_id=order.merchant_id,
                         operator=current_user.username)
    if not frozen.get("ok"):
        raise HTTPException(400, frozen.get("msg", "回收商余额不足"))
    order.fund_status = "frozen"
    order.fund_frozen_amount = quote.price
    db.commit()
    db.refresh(order)

    device = db.query(Device).filter(Device.id == inquiry.device_id).first()

    return {
        "message": "确认报价成功，订单已生成",
        "order": serialize_order(db, order, quote, device, viewer=current_user)
    }


@app.get("/api/orders/my")
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = get_orders_for_user(db, current_user)

    return {
        "list": [serialize_order(db, order, viewer=current_user) for order in orders]
    }


@app.get("/api/orders/{order_id}")
def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if current_user.role == "platform_admin":
        pass
    elif current_user.role in ("merchant_owner", "merchant_staff"):
        if not merchant_can_access_order(db, current_user, order):
            raise HTTPException(status_code=403, detail="无权查看该订单")
    elif current_user.role in ("recycler_owner", "recycler_staff", "recycler_keeper"):
        if not recycler_can_access_order(db, current_user, order):
            raise HTTPException(status_code=403, detail="无权查看该订单")
    else:
        raise HTTPException(status_code=403, detail="无权查看该订单")

    return serialize_order(db, order, viewer=current_user)


@app.post("/api/orders/{order_id}/ship")
def ship_api_order(
    order_id: int,
    data: ShipOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.execute(text("BEGIN IMMEDIATE"))
    if current_user.role not in ("merchant_owner", "merchant_staff"):
        raise HTTPException(status_code=403, detail="只有商家账号可以发货")

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if not merchant_can_access_order(db, current_user, order):
        raise HTTPException(status_code=403, detail="无权操作该订单")

    if order.status != "confirmed":
        if order.status == "shipped":
            raise HTTPException(status_code=400, detail="该订单已发货，不能重复发货")
        raise HTTPException(status_code=400, detail="只有待发货订单可以发货")

    express_company = data.express_company.strip()
    tracking_no = data.tracking_no.strip()

    if not express_company:
        raise HTTPException(status_code=400, detail="请输入快递公司")

    if not tracking_no:
        raise HTTPException(status_code=400, detail="请输入快递单号")

    if not data.shipping_images or any(not isinstance(image, str) or not image.strip() for image in data.shipping_images):
        raise HTTPException(status_code=400, detail="请上传有效发货凭证")

    from datetime import datetime

    now = datetime.now()
    order.express_company = express_company
    order.tracking_no = tracking_no
    order.shipping_images = dumps_json(data.shipping_images or [])
    order.ship_time = now
    order.status = "shipped"
    order.update_time = now

    company = db.query(MerchantCompany).filter(MerchantCompany.id == order.merchant_company_id).first()
    deposit = float(company.deposit_amount or 0) if company else 0
    outstanding = db.query(Order).filter(
        Order.merchant_company_id == order.merchant_company_id,
        Order.id != order.id, Order.fund_status == "deducted",
        Order.receive_time.is_(None), Order.status.notin_(["closed", "cancelled"])
    ).all()
    occupied = sum(float(o.merchant_base_amount or 0) for o in outstanding)
    if order.settlement_mode != "receive" and deposit > 0 and occupied + float(order.merchant_base_amount or 0) <= deposit:
        settle_order_funds(db, order, current_user.username)

    db.commit()
    db.refresh(order)

    return {
        "message": "发货成功",
        "order": serialize_order(db, order, viewer=current_user)
    }


@app.post("/api/orders/{order_id}/receive")
def receive_api_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.execute(text("BEGIN IMMEDIATE"))
    if current_user.role not in ("recycler_owner", "recycler_keeper"):
        raise HTTPException(status_code=403, detail="只有回收商老板或库管可以签收")

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if not recycler_can_access_order(db, current_user, order):
        raise HTTPException(status_code=403, detail="无权操作该订单")

    if order.status != "shipped":
        if order.status == "received":
            raise HTTPException(status_code=400, detail="该订单已签收，不能重复签收")
        raise HTTPException(status_code=400, detail="只有已发货订单可以签收")

    from datetime import datetime

    now = datetime.now()
    settle_order_funds(db, order, current_user.username)
    order.receive_time = now
    # 回收商确认签收 → 订单直接结束（完成）
    order.status = "completed"
    order.merchant_confirm_time = now
    order.update_time = now

    db.commit()
    db.refresh(order)

    return {
        "message": "签收成功，订单已完成",
        "order": serialize_order(db, order, viewer=current_user)
    }


@app.post("/api/orders/{order_id}/inspect")
def inspect_api_order(
    order_id: int,
    data: InspectOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.execute(text("BEGIN IMMEDIATE"))
    if current_user.role not in ("recycler_owner", "recycler_staff", "recycler_keeper"):
        raise HTTPException(status_code=403, detail="只有回收商账号可以验机")

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if not recycler_can_access_order(db, current_user, order):
        raise HTTPException(status_code=403, detail="无权操作该订单")

    if order.status != "received":
        if order.status == "inspection_done":
            raise HTTPException(status_code=400, detail="该订单已验机，不能重复验机")
        raise HTTPException(status_code=400, detail="只有已签收订单可以验机")

    inspection_type = data.inspection_type.strip()
    allowed_types = ("pass", "adjust", "reject")

    if inspection_type not in allowed_types:
        raise HTTPException(status_code=400, detail="验机类型无效")

    inspection_reason = (data.inspection_reason or "").strip()

    if inspection_type == "adjust":
        if data.inspection_price is None or data.inspection_price <= 0:
            raise HTTPException(status_code=400, detail="调价时必须填写大于0的调价金额")
        inspection_price = float(data.inspection_price)
    else:
        inspection_price = None

    if inspection_type == "reject" and not inspection_reason:
        raise HTTPException(status_code=400, detail="退货时必须填写原因")

    from datetime import datetime

    now = datetime.now()
    order.inspection_type = inspection_type
    order.inspection_price = inspection_price
    order.inspection_reason = inspection_reason
    order.inspection_time = now
    order.status = "inspection_done"
    order.update_time = now

    db.commit()
    db.refresh(order)

    return {
        "message": "验机结果已提交",
        "order": serialize_order(db, order, viewer=current_user)
    }


@app.post("/api/orders/{order_id}/confirm")
def confirm_api_order(
    order_id: int,
    data: ConfirmOrderRequest = ConfirmOrderRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.execute(text("BEGIN IMMEDIATE"))
    if current_user.role not in ("merchant_owner", "merchant_staff"):
        raise HTTPException(status_code=403, detail="只有商家账号可以确认验机结果")

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if not merchant_can_access_order(db, current_user, order):
        raise HTTPException(status_code=403, detail="无权操作该订单")

    if current_user.role == "merchant_staff" and not current_user.can_accept_quote:
        raise HTTPException(status_code=403, detail="你没有确认成交权限")

    if order.status != "inspection_done":
        if order.status == "completed":
            raise HTTPException(status_code=400, detail="该订单已完成，不能重复确认")
        raise HTTPException(status_code=400, detail="只有验机完成订单可以确认")

    from datetime import datetime

    now = datetime.now()
    settle_order_funds(db, order, current_user.username)
    order.status = "completed"
    order.merchant_confirm_time = now
    order.update_time = now

    db.commit()
    db.refresh(order)

    return {
        "message": "订单已完成",
        "order": serialize_order(db, order, viewer=current_user)
    }


@app.post("/api/orders/{order_id}/appeal")
def appeal_api_order(
    order_id: int,
    data: AppealOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.execute(text("BEGIN IMMEDIATE"))
    if current_user.role not in ("merchant_owner", "merchant_staff"):
        raise HTTPException(status_code=403, detail="只有商家账号可以发起申诉")

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if not merchant_can_access_order(db, current_user, order):
        raise HTTPException(status_code=403, detail="无权操作该订单")

    # 申诉可在交易进行中的任意阶段发起（确认报价后~验机完成），由平台介入处理；
    # 订单完成/关闭/取消后不可再申诉
    if order.status == "appealing":
        raise HTTPException(status_code=400, detail="该订单已申诉，不能重复申诉")
    if order.status not in ("confirmed", "shipped", "received", "inspection_done"):
        raise HTTPException(status_code=400, detail="订单已结束，无法发起申诉")

    appeal_reason = data.appeal_reason.strip()

    if not appeal_reason:
        raise HTTPException(status_code=400, detail="请填写申诉原因")

    from datetime import datetime

    now = datetime.now()
    order.status = "appealing"
    order.appeal_reason = appeal_reason
    order.appeal_time = now
    order.update_time = now

    db.commit()
    db.refresh(order)

    return {
        "message": "申诉已提交，等待平台处理",
        "order": serialize_order(db, order, viewer=current_user)
    }


@app.post("/api/admin/orders/{order_id}/close")
def close_admin_order(
    order_id: int,
    data: CloseOrderRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin)
):
    db.execute(text("BEGIN IMMEDIATE"))
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status == "completed":
        raise HTTPException(status_code=400, detail="已完成订单不能关闭")

    if order.status == "closed":
        raise HTTPException(status_code=400, detail="该订单已关闭，不能重复关闭")

    allowed_statuses = ("appealing", "confirmed", "shipped", "received", "inspection_done")

    if order.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="当前订单状态不允许关闭")

    close_reason = data.close_reason.strip()

    if not close_reason:
        raise HTTPException(status_code=400, detail="请填写关闭原因")

    from datetime import datetime

    now = datetime.now()
    order.status = "closed"
    order.close_reason = close_reason
    order.close_time = now
    order.update_time = now

    # ── 幂等释放（已扣款时 no-op） ──
    release_if_frozen(db, order, operator="平台管理员")

    db.commit()
    db.refresh(order)

    return {
        "message": "订单已关闭",
        "order": serialize_order(db, order, viewer=current_user)
    }


# -------------------------
# 用户相关
# -------------------------
@app.get("/users")
def get_users(db: Session = Depends(get_db), _: User = Depends(require_platform_admin)):
    return [serialize_account(db, user) for user in db.query(User).order_by(User.id.asc()).all()]


@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "platform_admin" and current_user.id != user_id:
        raise HTTPException(403, "无权查看该账号")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return serialize_account(db, user)


# -------------------------
# 商家员工权限
# -------------------------
@app.put("/merchant/staff/{staff_id}/permissions")
def update_staff_permissions(
    staff_id: int,
    data: UpdateStaffPermissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "merchant_owner":
        raise HTTPException(403, "只有公司老板可修改员工权限")
    staff = db.query(User).filter(User.id == staff_id).first()

    if not staff:
        raise HTTPException(status_code=404, detail="员工不存在")

    if staff.company_type != "merchant" or staff.company_id != current_user.company_id:
        raise HTTPException(403, "只能管理本公司的员工")
    if staff.role != "merchant_staff":
        raise HTTPException(status_code=400, detail="该用户不是商家员工")

    staff.can_create_inquiry = data.can_create_inquiry
    staff.can_view_all_inquiry = data.can_view_all_inquiry
    staff.can_accept_quote = data.can_accept_quote
    staff.can_manage_staff = data.can_manage_staff

    db.commit()
    db.refresh(staff)

    return {
        "message": "员工权限已更新",
        "staff": serialize_account(db, staff)
    }


# -------------------------
# 商家公司
# -------------------------
@app.post("/merchant/company")
def create_merchant_company(
    data: CreateMerchantCompanyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.execute(text("BEGIN IMMEDIATE"))
    if current_user.role != "platform_admin" and (
            current_user.role != "merchant_owner" or current_user.id != data.owner_user_id):
        raise HTTPException(403, "只能为本人开通公司")
    company_name = unique_company_name(db, data.company_name)
    owner = db.query(User).filter(User.id == data.owner_user_id).first()

    if not owner:
        raise HTTPException(status_code=404, detail="主账号不存在")

    if owner.role != "merchant_owner" or owner.company_type != "merchant":
        raise HTTPException(status_code=400, detail="只有商家主账号可以开通公司")

    if owner.company_id or db.query(MerchantCompany.id).filter(MerchantCompany.owner_user_id == owner.id).first():
        raise HTTPException(400, "老板已有公司归属，不能重复开通或改绑公司")

    company = MerchantCompany(
        company_name=company_name,
        owner_user_id=owner.id,
        contact_name=data.contact_name,
        contact_phone=data.contact_phone,
        address=data.address,
        join_code=f"M{int(time.time())}",
        status="active"
    )

    db.add(company)
    db.flush()
    owner.company_id = company.id
    db.commit()
    db.refresh(company)

    return {
        "message": "商家公司开通成功",
        "company": company
    }


@app.get("/merchant/company/{company_id}/staff")
def get_merchant_staff(company_id: int, db: Session = Depends(get_db)):
    raise HTTPException(410, "旧查询接口已停用，请使用带登录校验的 /api 接口")
    return db.query(User).filter(
        User.company_id == company_id,
        User.company_type == "merchant"
    ).order_by(User.id.asc()).all()


# -------------------------
# 回收商公司
# -------------------------
@app.get("/recycler/companies")
def get_recycler_companies(db: Session = Depends(get_db)):
    return db.query(RecyclerCompany).order_by(RecyclerCompany.id.asc()).all()


# -------------------------
# 创建询价单
# -------------------------
@app.post("/inquiries")
def create_inquiry(
    data: CreateInquiryRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == data.created_by_user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.company_type != "merchant":
        raise HTTPException(status_code=403, detail="只有商家账号可以发起询价")

    if not user.can_create_inquiry:
        raise HTTPException(status_code=403, detail="你没有发起询价权限")

    inquiry = Inquiry(
        no=f"XJ{int(time.time())}",
        merchant_company_id=data.merchant_company_id,
        merchant_company_name=data.merchant_company_name,
        created_by_user_id=data.created_by_user_id,
        created_by_user_name=data.created_by_user_name,

        device_type=data.device_type,
        brand=data.brand,
        model=data.model,

        storage=data.storage,
        color=data.color,
        channel=data.channel,
        warranty=data.warranty,

        device_detail_json=data.device_detail_json,
        photos_json=data.photos_json,

        status="waiting_quote"
    )

    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    return {
        "message": "询价单创建成功",
        "inquiry": inquiry
    }


# -------------------------
# 查询询价单
# -------------------------
@app.get("/inquiries")
def get_inquiries(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 商家老板：看本公司全部询价
    if user.role == "merchant_owner":
        return db.query(Inquiry).filter(
            Inquiry.merchant_company_id == user.company_id
        ).order_by(Inquiry.id.desc()).all()

    # 商家员工：根据权限判断看全部还是只看自己创建的
    if user.role == "merchant_staff":
        if user.can_view_all_inquiry:
            return db.query(Inquiry).filter(
                Inquiry.merchant_company_id == user.company_id
            ).order_by(Inquiry.id.desc()).all()

        return db.query(Inquiry).filter(
            Inquiry.created_by_user_id == user.id
        ).order_by(Inquiry.id.desc()).all()

    # 回收商老板：目前先看全部询价，后续再按回收商公司分配过滤
    if user.role == "recycler_owner":
        return db.query(Inquiry).order_by(Inquiry.id.desc()).all()

    # 回收商员工：目前先看全部，后续做分配表后改成只看分配给自己的
    if user.role == "recycler_staff":
        return db.query(Inquiry).order_by(Inquiry.id.desc()).all()

    # 平台管理员：看全部
    if user.role == "platform_admin":
        return db.query(Inquiry).order_by(Inquiry.id.desc()).all()

    return []


# -------------------------
# 回收商报价
# -------------------------
@app.post("/quotes")
def create_quote(
    data: CreateQuoteRequest,
    db: Session = Depends(get_db)
):
    raise HTTPException(410, "旧交易接口已停用，请使用 /api/quotes 接口")
    inquiry = db.query(Inquiry).filter(Inquiry.id == data.inquiry_id).first()

    if not inquiry:
        raise HTTPException(status_code=404, detail="询价单不存在")

    user = db.query(User).filter(User.id == data.quote_user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="报价用户不存在")

    if user.company_type != "recycler":
        raise HTTPException(status_code=403, detail="只有回收商账号可以报价")

    quote = Quote(
        inquiry_id=data.inquiry_id,
        recycler_company_id=data.recycler_company_id,
        recycler_company_name=data.recycler_company_name,
        quote_user_id=data.quote_user_id,
        quote_user_name=data.quote_user_name,
        quote_user_role=data.quote_user_role,
        price=data.price,
        valid_hours=data.valid_hours,
        remark=data.remark,
        status="sent"
    )

    inquiry.status = "quoted"

    db.add(quote)
    db.commit()
    db.refresh(quote)

    return {
        "message": "报价成功",
        "quote": quote
    }


# -------------------------
# 查询某个询价单的报价
# -------------------------
@app.get("/quotes")
def get_quotes(
    inquiry_id: int,
    db: Session = Depends(get_db)
):
    raise HTTPException(410, "旧查询接口已停用，请使用带登录校验的 /api 接口")
    return db.query(Quote).filter(
        Quote.inquiry_id == inquiry_id
    ).order_by(Quote.id.desc()).all()


# -------------------------
# 商家接受报价
# -------------------------
@app.post("/quotes/accept")
def accept_quote(
    data: AcceptQuoteRequest,
    db: Session = Depends(get_db)
):
    raise HTTPException(410, "旧交易接口已停用，请使用 /api/quotes 接口")
    user = db.query(User).filter(User.id == data.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.company_type != "merchant":
        raise HTTPException(status_code=403, detail="只有商家账号可以同意卖出")

    if user.role == "merchant_staff" and not user.can_accept_quote:
        raise HTTPException(
            status_code=403,
            detail="你没有同意卖出的权限，请联系主账号授权"
        )

    inquiry = db.query(Inquiry).filter(Inquiry.id == data.inquiry_id).first()
    quote = db.query(Quote).filter(Quote.id == data.quote_id).first()

    if not inquiry:
        raise HTTPException(status_code=404, detail="询价单不存在")

    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if inquiry.merchant_company_id != user.company_id:
        raise HTTPException(status_code=403, detail="不能操作其他公司的询价单")

    inquiry.status = "accepted"
    quote.status = "accepted"

    order = Order(
        order_no=f"DD{int(time.time())}",
        inquiry_id=inquiry.id,
        quote_id=quote.id,
        merchant_company_id=inquiry.merchant_company_id,
        recycler_company_id=quote.recycler_company_id,
        accepted_price=quote.price,
        status="waiting_ship"
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "message": "已同意卖出，订单已生成",
        "order": order
    }


# -------------------------
# 查询订单
# -------------------------
@app.get("/orders")
def get_orders(
    user_id: int,
    db: Session = Depends(get_db)
):
    raise HTTPException(410, "旧查询接口已停用，请使用带登录校验的 /api 接口")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.company_type == "merchant":
        return db.query(Order).filter(
            Order.merchant_company_id == user.company_id
        ).order_by(Order.id.desc()).all()

    if user.company_type == "recycler":
        return db.query(Order).filter(
            Order.recycler_company_id == user.company_id
        ).order_by(Order.id.desc()).all()

    return db.query(Order).order_by(Order.id.desc()).all()


# ═══════════════════════════════════════════════════════════════════
# 资金池
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/fund/pool/{company_id}")
def get_fund_pool(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询回收商资金池。本公司三角色 + 平台可访问。"""
    if current_user.role == "platform_admin":
        pass
    elif current_user.role in ("recycler_owner", "recycler_keeper", "recycler_staff"):
        if current_user.company_id != company_id:
            raise HTTPException(status_code=403, detail="无权查看其他公司资金池")
    else:
        raise HTTPException(status_code=403, detail="无权访问资金池")

    rc = db.query(RecyclerCompany).filter(RecyclerCompany.id == company_id).first()
    info = get_pool_info(db, company_id)
    info["company_name"] = rc.company_name if rc else ""
    return info


@app.get("/api/admin/fund/pools")
def get_all_fund_pools(
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin),
):
    """平台查全部资金池。"""
    companies = db.query(RecyclerCompany).order_by(RecyclerCompany.id.asc()).all()
    result = []
    for rc in companies:
        info = get_pool_info(db, rc.id)
        info["company_name"] = rc.company_name
        result.append(info)
    return {"list": result}


@app.post("/api/admin/fund/pools/{company_id}/set")
def set_fund_balance(
    company_id: int,
    data: SetFundBalanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    db.execute(text("BEGIN IMMEDIATE"))
    """平台直接设置余额（测试/人工调整用）。"""
    from datetime import datetime
    pool = _get_or_create_pool(db, company_id)
    if not math.isfinite(data.balance) or data.balance < (pool.frozen_amount or 0):
        raise HTTPException(400, "总余额不能小于冻结金额")
    old_balance = pool.balance or 0
    pool.balance = data.balance
    db.add(FundFlow(
        type="recharge" if data.balance >= old_balance else "manual_deduct",
        company_id=company_id,
        amount=abs(round(data.balance - old_balance, 2)),
        operator=current_user.username,
        remark=f"平台手动调整余额 {old_balance} → {data.balance}",
        create_time=datetime.now(),
    ))
    db.commit()
    return get_pool_info(db, company_id)


# ═══════════════════════════════════════════════════════════════════
# 资金流水
# ═══════════════════════════════════════════════════════════════════

def _serialize_flow(f: FundFlow) -> dict:
    from account_utils import format_datetime
    return {
        "id": f.id,
        "type": f.type,
        "company_id": f.company_id,
        "company_type": f.company_type or "recycler",
        "order_no": f.order_no or "",
        "order_id": f.order_id,
        "merchant_id": f.merchant_id,
        "operator": f.operator or "",
        "amount": f.amount,
        "remark": f.remark or "",
        "status": f.status or "success",
        "create_time": format_datetime(f.create_time),
    }


@app.get("/api/fund/flows")
def get_fund_flows(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """回收商查本公司流水。"""
    if current_user.role == "platform_admin":
        pass
    elif current_user.role in ("recycler_owner", "recycler_keeper", "recycler_staff"):
        if current_user.company_id != company_id:
            raise HTTPException(status_code=403, detail="无权查看其他公司流水")
    else:
        raise HTTPException(status_code=403, detail="无权访问资金流水")

    flows = db.query(FundFlow).filter(
        FundFlow.company_id == company_id, FundFlow.company_type == "recycler"
    ).order_by(FundFlow.id.desc()).all()
    return {"list": [_serialize_flow(f) for f in flows]}


@app.get("/api/admin/fund/flows")
def get_admin_fund_flows(
    company_id: int = None,
    type: str = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin),
):
    """平台查全量流水，支持按 company_id / type 筛选。"""
    q = db.query(FundFlow)
    if company_id:
        q = q.filter(FundFlow.company_id == company_id)
    if type:
        q = q.filter(FundFlow.type == type)
    flows = q.order_by(FundFlow.id.desc()).all()
    rows=[]
    for flow in flows:
        item=_serialize_flow(flow)
        model=MerchantCompany if flow.company_type=="merchant" else RecyclerCompany
        company=db.get(model,flow.company_id)
        item["company_name"]=company.company_name if company else ""
        rows.append(item)
    return {"list": rows, "total": len(rows)}


# ═══════════════════════════════════════════════════════════════════
# 充值申请
# ═══════════════════════════════════════════════════════════════════

def _serialize_recharge(r: RechargeApply) -> dict:
    from account_utils import format_datetime
    return {
        "id": r.id,
        "company_id": r.company_id,
        "company_name": r.company_name or "",
        "amount": r.amount,
        "proof_image": r.proof_image or "",
        "apply_user_id": r.apply_user_id,
        "status": r.status,
        "reject_reason": r.reject_reason or "",
        "create_time": format_datetime(r.create_time),
        "review_time": format_datetime(r.review_time),
    }


@app.post("/api/recharge/apply")
def create_recharge_apply(
    data: RechargeApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """回收商老板/库管发起充值申请。"""
    if current_user.role not in ("recycler_owner", "recycler_keeper"):
        raise HTTPException(status_code=403, detail="只有回收商老板/库管可以申请充值")
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="充值金额必须大于 0")

    rc = db.query(RecyclerCompany).filter(RecyclerCompany.id == data.company_id).first()
    apply = RechargeApply(
        company_id=data.company_id,
        company_name=rc.company_name if rc else "",
        amount=data.amount,
        proof_image=data.proof_image,
        apply_user_id=current_user.id,
        status="pending",
    )
    db.add(apply)
    db.commit()
    db.refresh(apply)
    return {"message": "充值申请已提交", "apply": _serialize_recharge(apply)}


@app.get("/api/recharge/applies")
def get_recharge_applies(
    company_id: int = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """回收商看本公司申请；平台看全部。"""
    if current_user.role == "platform_admin":
        pass
    elif current_user.role in ("recycler_owner", "recycler_keeper", "recycler_staff"):
        company_id = current_user.company_id  # 强制只看本公司
    else:
        raise HTTPException(status_code=403, detail="无权查看充值申请")

    q = db.query(RechargeApply)
    if company_id:
        q = q.filter(RechargeApply.company_id == company_id)
    if status:
        q = q.filter(RechargeApply.status == status)
    items = q.order_by(RechargeApply.id.desc()).all()
    return {"list": [_serialize_recharge(r) for r in items]}


@app.post("/api/admin/recharge/{apply_id}/approve")
def approve_recharge(
    apply_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """平台审核通过：余额入账 + 记流水。"""
    from datetime import datetime
    apply = db.query(RechargeApply).filter(RechargeApply.id == apply_id).first()
    if not apply:
        raise HTTPException(status_code=404, detail="申请不存在")
    if apply.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已处理")

    pool = _get_or_create_pool(db, apply.company_id)
    pool.balance = round((pool.balance or 0) + apply.amount, 2)
    apply.status = "approved"
    apply.review_time = datetime.now()

    record_recharge_flow(
        db,
        company_id=apply.company_id,
        amount=apply.amount,
        operator=current_user.username,
    )
    db.commit()
    return {"message": "充值已通过，余额已入账", "apply": _serialize_recharge(apply)}


@app.post("/api/admin/recharge/{apply_id}/reject")
def reject_recharge(
    apply_id: int,
    data: RejectReasonRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin),
):
    from datetime import datetime
    apply = db.query(RechargeApply).filter(RechargeApply.id == apply_id).first()
    if not apply:
        raise HTTPException(status_code=404, detail="申请不存在")
    if apply.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已处理")

    apply.status = "rejected"
    apply.reject_reason = data.reason
    apply.review_time = datetime.now()
    db.commit()
    return {"message": "已驳回", "apply": _serialize_recharge(apply)}


# ═══════════════════════════════════════════════════════════════════
# 抽成比例
# ═══════════════════════════════════════════════════════════════════

def _serialize_commission(cr: CommissionRate, user: User = None) -> dict:
    from account_utils import format_datetime
    d = {
        "id": cr.id,
        "user_id": cr.user_id,
        "company_id": cr.company_id,
        "role": cr.role or "",
        "rate": cr.rate or 0,
        "update_time": format_datetime(cr.update_time),
    }
    if user:
        d["username"] = user.username
        d["phone"] = user.phone
    return d


@app.get("/api/commission/rate")
def get_commission_rate(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询某用户抽成比例。本人 / 商家老板（同公司）/ 平台 可查。"""
    if current_user.role != "platform_admin":
        if current_user.id != user_id:
            # 商家老板可查本公司员工
            if current_user.role == "merchant_owner":
                target = db.query(User).filter(User.id == user_id).first()
                if not target or target.company_id != current_user.company_id:
                    raise HTTPException(status_code=403, detail="无权查看该用户比例")
            else:
                raise HTTPException(status_code=403, detail="无权查看该用户比例")

    cr = db.query(CommissionRate).filter(CommissionRate.user_id == user_id).first()
    if not cr:
        return {"user_id": user_id, "rate": 0, "is_set": False}
    result = _serialize_commission(cr)
    result["is_set"] = True
    return result


@app.post("/api/commission/rate")
def set_commission_rate(
    data: SetCommissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    设置抽成比例。
    - 员工只能设自己；老板可设自己及本公司员工；平台全权。
    """
    if current_user.role == "platform_admin":
        pass
    elif current_user.role == "merchant_owner":
        if data.user_id != current_user.id:
            raise HTTPException(403, "老板只能设置自己的比例，员工比例由员工独立设置")
    elif current_user.role == "merchant_staff":
        if data.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="员工只能设置自己的比例")
    else:
        raise HTTPException(status_code=403, detail="无权设置抽成比例")

    if not (0 <= data.rate <= 1):
        raise HTTPException(status_code=400, detail="比例需在 0~1 之间（如 0.05 表示 5%）")

    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    cr = db.query(CommissionRate).filter(CommissionRate.user_id == data.user_id).first()
    if cr:
        cr.rate = data.rate
    else:
        cr = CommissionRate(
            user_id=data.user_id,
            company_id=target_user.company_id,
            role=target_user.role,
            rate=data.rate,
        )
        db.add(cr)
    db.commit()
    db.refresh(cr)
    return {"message": "抽成比例已更新", "commission": _serialize_commission(cr, target_user)}


@app.get("/api/commission/rates")
def get_company_commission_rates(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """商家老板查全公司抽成比例（merchantCommissionRateMap）。"""
    if current_user.role == "platform_admin":
        pass
    elif current_user.role == "merchant_owner":
        if current_user.company_id != company_id:
            raise HTTPException(status_code=403, detail="无权查看其他公司比例")
    else:
        raise HTTPException(status_code=403, detail="无权访问")

    users = db.query(User).filter(
        User.company_id == company_id,
        User.company_type == "merchant",
        User.status == "approved",
    ).all()

    result = []
    for u in users:
        cr = db.query(CommissionRate).filter(CommissionRate.user_id == u.id).first()
        result.append({
            "user_id": u.id,
            "username": u.username,
            "phone": u.phone,
            "role": u.role,
            "rate": cr.rate if cr else 0,
        })
    return {"list": result}


# ═══════════════════════════════════════════════════════════════════
# 取消申请
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/orders/{order_id}/cancel-apply")
def cancel_apply(
    order_id: int,
    data: CancelApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """商家或回收商发起取消申请。"""
    db.execute(text("BEGIN IMMEDIATE"))
    if current_user.role not in (
        "merchant_owner", "merchant_staff",
        "recycler_owner", "recycler_keeper", "recycler_staff",
    ):
        raise HTTPException(status_code=403, detail="无权发起取消申请")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 权限：商家只能申请本公司订单；回收商同理
    if current_user.role in ("merchant_owner", "merchant_staff"):
        from trade_utils import merchant_can_access_order
        if not merchant_can_access_order(db, current_user, order):
            raise HTTPException(status_code=403, detail="无权操作该订单")
    else:
        from trade_utils import recycler_can_access_order
        if not recycler_can_access_order(db, current_user, order):
            raise HTTPException(status_code=403, detail="无权操作该订单")

    # 仅在回收商收货前可取消（已确认报价 confirmed / 已发货 shipped）；
    # 回收商收货后订单进入验机/售后阶段，只能发起申诉，不能取消
    if order.status not in ("confirmed", "shipped"):
        raise HTTPException(status_code=400, detail="回收商已收货，订单进入验机/售后阶段，只能联系平台申诉，不能取消")
    if order.cancel_apply_status == "pending":
        raise HTTPException(status_code=400, detail="已有待审核的取消申请")

    from datetime import datetime
    order.cancel_apply_status = "pending"
    order.cancel_apply_reason = data.reason
    order.cancel_apply_time = datetime.now()
    order.cancel_reject_reason = None
    db.commit()
    return {"message": "取消申请已提交，等待平台审核"}


@app.post("/api/admin/orders/{order_id}/cancel-approve")
def cancel_approve(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    db.execute(text("BEGIN IMMEDIATE"))
    """平台审核通过取消申请。"""
    from datetime import datetime
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.cancel_apply_status != "pending":
        raise HTTPException(status_code=400, detail="没有待审核的取消申请")

    if order.status not in ("confirmed", "shipped"):
        raise HTTPException(status_code=400, detail="订单状态已变化，不能通过取消申请，请核对订单或联系平台处理")

    order.cancel_apply_status = "approved"
    order.status = "closed"
    order.close_reason = f"取消申请通过：{order.cancel_apply_reason or ''}"
    order.close_time = datetime.now()
    order.update_time = datetime.now()

    release_if_frozen(db, order, operator=current_user.username)
    db.commit()
    return {"message": "取消申请已通过，订单已关闭"}


@app.post("/api/admin/orders/{order_id}/cancel-reject")
def cancel_reject(
    order_id: int,
    data: RejectReasonRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin),
):
    """平台驳回取消申请。"""
    db.execute(text("BEGIN IMMEDIATE"))
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.cancel_apply_status != "pending":
        raise HTTPException(status_code=400, detail="没有待审核的取消申请")

    order.cancel_apply_status = "rejected"
    order.cancel_reject_reason = data.reason
    db.commit()
    return {"message": "取消申请已驳回"}

@app.post("/api/company/staff/{account_id}/{action}")
def manage_company_staff(account_id: int, action: str, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    if current_user.role not in ("merchant_owner", "recycler_owner"):
        raise HTTPException(403, "只有公司老板可审核员工")
    target = db.query(User).filter(User.id == account_id).first()
    if not target or target.company_id != current_user.company_id or target.company_type != current_user.company_type or not is_staff_role(target.role):
        raise HTTPException(403, "只能管理本公司的员工")
    states = {"approve": "approved", "reject": "rejected", "disable": "disabled", "enable": "approved"}
    if action not in states:
        raise HTTPException(400, "操作无效")
    if action in ("approve", "reject") and target.status != "pending":
        raise HTTPException(400, "该员工不处于待审核状态")
    target.status = states[action]
    if action in ("disable", "reject"):
        target.session_version = (target.session_version or 0) + 1
    if action == "approve" and target.role == "merchant_staff":
        target.can_accept_quote = True
    db.commit()
    return {"message": "员工账号已更新"}


@app.get("/api/admin/merchant/deposits")
def list_merchant_deposits(db: Session = Depends(get_db), current_user: User = Depends(require_platform_admin)):
    return {"list": [merchant_deposit_info(db, c) for c in db.query(MerchantCompany).all()]}


@app.post("/api/admin/merchant/{company_id}/deposit")
def set_merchant_deposit(company_id: int, data: SetFundBalanceRequest,
                         db: Session = Depends(get_db), current_user: User = Depends(require_platform_admin)):
    db.execute(text("BEGIN IMMEDIATE"))
    if not math.isfinite(data.balance) or data.balance < 0:
        raise HTTPException(400, "保证金额度必须为非负金额")
    company = db.query(MerchantCompany).filter(MerchantCompany.id == company_id).first()
    if not company:
        raise HTTPException(404, "商家公司不存在")
    old=float(company.deposit_amount or 0)
    if data.balance < merchant_occupied_credit(db, company_id):
        raise HTTPException(400, "退款后额度不能小于未签收订单占用额度")
    company.deposit_amount = data.balance
    delta=round(data.balance-old,2)
    if delta:
        db.add(FundFlow(company_type="merchant",company_id=company_id,type="merchant_recharge" if delta>0 else "merchant_refund",amount=abs(delta),operator=current_user.username,remark="平台调整商家额度"))
    db.commit()
    return {"message": "保证金额度已更新"}


def settle_order_funds(db, order, operator):
    if order.fund_status == "deducted":
        return
    amount = order.recycler_quote_amount or order.accepted_price or 0
    if order.fund_status != "frozen":
        result = freeze_fund(db, order.recycler_company_id, amount, order_no=order.order_no,
                             order_id=order.id, merchant_id=order.merchant_id, operator=operator)
        if not result.get("ok"):
            raise HTTPException(400, result.get("msg", "回收商余额不足"))
        order.fund_status = "frozen"
        order.fund_frozen_amount = amount
    result = deduct_fund(db, order.recycler_company_id, order.fund_frozen_amount,
                         order_no=order.order_no, order_id=order.id,
                         merchant_id=order.merchant_id, operator=operator)
    if not result.get("ok"):
        raise HTTPException(400, "资金扣款失败，请核对回收商资金池")
    order.fund_status = "deducted"
    order.fund_deducted_amount = order.fund_frozen_amount


@app.post("/api/company/staff")
def add_company_staff(data: RegisterAccountRequest, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    if current_user.role not in ("merchant_owner", "recycler_owner"):
        raise HTTPException(403, "只有公司老板可以新增员工")
    roles = ("merchant_staff",) if current_user.company_type == "merchant" else ("recycler_staff", "recycler_keeper")
    if data.role not in roles:
        raise HTTPException(400, "员工角色不属于当前公司")
    data.company_type = current_user.company_type
    data.company_id = current_user.company_id
    data.new_company_name = None
    register_account(data, db)
    target = db.query(User).filter(User.phone == data.phone.strip()).first()
    target.status = "approved"
    target.can_accept_quote = target.role == "merchant_staff"
    db.commit()
    return {"message": "员工已新增并通过老板审核"}


# 手工额度账本；不连接支付或银行。
from pydantic import BaseModel
class BalanceAdjustmentRequest(BaseModel):
    company_type: str
    company_id: int
    action: str
    amount: float
    request_id: str

class ShippingContactRequest(BaseModel):
    contact_name: str
    contact_phone: str
    address: str

def merchant_occupied_credit(db, company_id):
    orders=db.query(Order).filter(Order.merchant_company_id==company_id,Order.fund_status=="deducted",Order.receive_time.is_(None),Order.status.notin_(["closed","cancelled"])).all()
    return sum(float(o.merchant_base_amount or 0) for o in orders)

@app.post("/api/admin/balance/adjust")
def adjust_company_balance(data: BalanceAdjustmentRequest, db: Session=Depends(get_db), user: User=Depends(require_platform_admin)):
    if data.company_type not in ("merchant","recycler") or data.action not in ("recharge","deduct","refund"):
        raise HTTPException(400,"账户类型或操作不正确")
    if (data.company_type=="merchant" and data.action=="deduct") or (data.company_type=="recycler" and data.action=="refund"):
        raise HTTPException(400,"操作与账户类型不符")
    if not math.isfinite(data.amount) or data.amount<=0 or not math.isclose(data.amount,round(data.amount,2),abs_tol=1e-8):
        raise HTTPException(400,"金额必须为正数，最多两位小数")
    if not data.request_id.strip() or len(data.request_id)>100:
        raise HTTPException(400,"操作编号不正确")
    db.execute(text("BEGIN IMMEDIATE"))
    key="manual:"+data.request_id
    existing=db.query(FundFlow).filter(FundFlow.operation_key==key).first()
    expected_type=("merchant_recharge" if data.action=="recharge" else "merchant_refund") if data.company_type=="merchant" else ("recharge" if data.action=="recharge" else "manual_deduct")
    if existing:
        if existing.company_id!=data.company_id or existing.company_type!=data.company_type or existing.type!=expected_type or existing.amount!=data.amount:
            raise HTTPException(409,"操作编号已用于其他登记")
        return {"message":"已登记","flow":_serialize_flow(existing)}
    model=MerchantCompany if data.company_type=="merchant" else RecyclerCompany
    company=db.get(model,data.company_id)
    if not company: raise HTTPException(404,"公司不存在")
    sign=1 if data.action=="recharge" else -1
    amount=round(data.amount,2)
    if data.company_type=="merchant":
        new=round(float(company.deposit_amount or 0)+sign*amount,2)
        if new<merchant_occupied_credit(db,data.company_id) or new<0:
            raise HTTPException(400,"退款金额超过未占用的商家额度")
        company.deposit_amount=new
    else:
        pool=_get_or_create_pool(db,data.company_id)
        new=round(float(pool.balance or 0)+sign*amount,2)
        if new<float(pool.frozen_amount or 0):
            raise HTTPException(400,"扣除金额超过回收商可用额度")
        pool.balance=new
    flow=FundFlow(company_type=data.company_type,company_id=data.company_id,type=expected_type,amount=amount,operation_key=key,operator=user.username,remark="平台手工登记额度")
    db.add(flow);db.commit();db.refresh(flow)
    return {"message":"已登记","balance":new,"flow":_serialize_flow(flow)}

@app.get("/api/recycler/shipping-contact")
def get_shipping_contact(db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    if user.company_type!="recycler": raise HTTPException(403,"仅回收商查看本公司收货资料")
    company=db.get(RecyclerCompany,user.company_id)
    if not company: raise HTTPException(404,"公司不存在")
    return {key:getattr(company,key) or "" for key in ("contact_name","contact_phone","address")}

@app.post("/api/recycler/shipping-contact")
def set_shipping_contact(data: ShippingContactRequest,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    company=db.get(RecyclerCompany,user.company_id) if user.company_type=="recycler" else None
    if user.role!="recycler_owner" or not company or company.owner_user_id!=user.id:
        raise HTTPException(403,"仅本公司老板可修改收货资料")
    values={key:getattr(data,key).strip() for key in ("contact_name","contact_phone","address")}
    if any(not value or len(value)>300 for value in values.values()):
        raise HTTPException(400,"请填写完整的收件人、电话和地址")
    for key,value in values.items(): setattr(company,key,value)
    db.commit()
    return values


# 保证金申请只登记意向，到账必须由平台核实；未缴纳不会改变账号状态。
class MerchantDepositRequest(BaseModel):
    amount: float
    remark: str = ""

class DepositReviewRequest(BaseModel):
    action: str
    remark: str = ""

class DepositFollowupRequest(BaseModel):
    note: str

def merchant_deposit_info(db, company):
    import calendar
    created = company.create_time
    due = None
    if created:
        year = created.year + (created.month == 12)
        month = created.month % 12 + 1
        due = created.replace(year=year, month=month, day=min(created.day, calendar.monthrange(year, month)[1]))
    pending = db.query(MerchantDepositApply).filter_by(company_id=company.id, status="pending").first()
    return {"id":company.id,"company_name":company.company_name,"deposit_amount":company.deposit_amount or 0,
        "status":company.status,"registered_at":created.isoformat(sep=" ",timespec="seconds") if created else None,
        "settlement_mode":"ship" if float(company.deposit_amount or 0)>0 else "receive",
        "deposit_overdue":bool(due and datetime.now()>=due and float(company.deposit_amount or 0)<=0),
        "reminder_due_at":due.isoformat(sep=" ",timespec="seconds") if due else None,
        "followup":company.deposit_followup or "","followup_by":company.deposit_followup_by,
        "followup_time":str(company.deposit_followup_time) if company.deposit_followup_time else None,
        "pending_application": {"id":pending.id,"amount":pending.amount,"remark":pending.remark,"created_at":str(pending.create_time)} if pending else None}

@app.get("/api/merchant/deposit")
def my_merchant_deposit(db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    if current_user.role not in ("merchant_owner","merchant_staff"):
        raise HTTPException(403,"仅商家可查看")
    company=db.get(MerchantCompany,current_user.company_id)
    if not company: raise HTTPException(404,"公司不存在")
    info=merchant_deposit_info(db,company)
    # 跟进及逾期提醒仅平台可见。
    return {k:info[k] for k in ("id","company_name","deposit_amount","settlement_mode","pending_application")}

@app.post("/api/merchant/deposit/apply")
def apply_merchant_deposit(data:MerchantDepositRequest, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    db.execute(text("BEGIN IMMEDIATE"))
    company=db.get(MerchantCompany,current_user.company_id)
    if current_user.role!="merchant_owner" or not company or company.owner_user_id!=current_user.id:
        raise HTTPException(403,"仅本公司老板可申请")
    if not math.isfinite(data.amount) or data.amount<=0 or not math.isclose(data.amount,round(data.amount,2),rel_tol=0,abs_tol=1e-8):
        raise HTTPException(400,"保证金金额必须为正数且最多两位小数")
    if len(data.remark)>1000: raise HTTPException(400,"备注过长")
    if db.query(MerchantDepositApply).filter_by(company_id=company.id,status="pending").first():
        raise HTTPException(409,"已有保证金申请待核实，请勿重复提交")
    application=MerchantDepositApply(company_id=company.id,applicant_id=current_user.id,amount=round(data.amount,2),remark=data.remark.strip())
    db.add(application);db.commit()
    return {"message":"已提交平台核实，确认前仍按原模式结算"}

@app.post("/api/admin/merchant/deposit-applies/{application_id}/review")
def review_merchant_deposit(application_id:int, data:DepositReviewRequest, db:Session=Depends(get_db), current_user:User=Depends(require_platform_admin)):
    db.execute(text("BEGIN IMMEDIATE"))
    application=db.get(MerchantDepositApply,application_id)
    if not application: raise HTTPException(404,"申请不存在")
    if application.status!="pending": raise HTTPException(409,"申请已处理，请刷新")
    if data.action not in ("approve","reject"): raise HTTPException(400,"操作无效")
    if len(data.remark)>1000: raise HTTPException(400,"备注过长")
    company=db.get(MerchantCompany,application.company_id)
    if not company: raise HTTPException(404,"公司不存在")
    if data.action=="approve":
        if company.status!="active": raise HTTPException(400,"公司已停用，不能确认")
        company.deposit_amount=round(float(company.deposit_amount or 0)+application.amount,2)
        db.add(FundFlow(company_type="merchant",company_id=company.id,type="merchant_recharge",amount=application.amount,operator=current_user.username,operation_key=f"deposit-apply:{application.id}",remark="核实保证金到账："+data.remark.strip()))
    application.status="approved" if data.action=="approve" else "rejected"
    application.reviewer_id=current_user.id;application.review_time=datetime.now();application.review_remark=data.remark.strip()
    db.commit()
    return {"message":"保证金已核实，公司新成交订单发货即结算" if data.action=="approve" else "申请已驳回"}

@app.post("/api/admin/merchant/{company_id}/deposit-followup")
def followup_merchant_deposit(company_id:int,data:DepositFollowupRequest,db:Session=Depends(get_db),current_user:User=Depends(require_platform_admin)):
    company=db.get(MerchantCompany,company_id)
    if not company: raise HTTPException(404,"公司不存在")
    if len(data.note)>3000: raise HTTPException(400,"跟进记录最多3000字")
    company.deposit_followup=data.note.strip();company.deposit_followup_by=current_user.username;company.deposit_followup_time=datetime.now()
    db.commit()
    return {"message":"跟进记录已保存"}
