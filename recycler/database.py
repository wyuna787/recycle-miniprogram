from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 数据库文件，会自动生成 recycle.db
import os
DATABASE_URL = os.environ.get("RECYCLE_DATABASE_URL", "sqlite:///./recycle.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db():
    with engine.connect() as conn:
        columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()
        }

        if "session_version" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN session_version INTEGER NOT NULL DEFAULT 0"))

        if "password_hash" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))

        if "apply_reason" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN apply_reason TEXT"))

        if "reject_reason" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN reject_reason TEXT"))

        conn.execute(text(
            "UPDATE users SET status = 'approved' WHERE status = 'active'"
        ))

        inquiry_columns = {row[1] for row in conn.execute(text("PRAGMA table_info(device_inquiries)")).fetchall()}
        if "merchant_company_id" not in inquiry_columns:
            conn.execute(text("ALTER TABLE device_inquiries ADD COLUMN merchant_company_id INTEGER"))
        # 只从订单归属补齐可确认的历史记录，不按发布人当前公司猜测旧询价。
        order_fields = {row[1] for row in conn.execute(text("PRAGMA table_info(orders)")).fetchall()}
        if "merchant_company_id" in order_fields and "inquiry_id" in order_fields:
            conn.execute(text("""
                UPDATE device_inquiries SET merchant_company_id = (
                    SELECT orders.merchant_company_id FROM orders
                    WHERE orders.inquiry_id = device_inquiries.id AND orders.merchant_company_id IS NOT NULL
                    ORDER BY orders.id LIMIT 1
                ) WHERE merchant_company_id IS NULL AND EXISTS (
                    SELECT 1 FROM orders WHERE orders.inquiry_id = device_inquiries.id
                    AND orders.merchant_company_id IS NOT NULL
                )
            """))

        quote_columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(quotes)")).fetchall()
        }

        if "device_id" not in quote_columns:
            conn.execute(text("ALTER TABLE quotes ADD COLUMN device_id INTEGER"))

        if "merchant_id" not in quote_columns:
            conn.execute(text("ALTER TABLE quotes ADD COLUMN merchant_id INTEGER"))

        if "valid_days" not in quote_columns:
            conn.execute(text("ALTER TABLE quotes ADD COLUMN valid_days INTEGER DEFAULT 3"))

        device_columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(devices)")).fetchall()
        }

        for col, ddl in (
            ("storage", "ALTER TABLE devices ADD COLUMN storage VARCHAR"),
            ("color", "ALTER TABLE devices ADD COLUMN color VARCHAR"),
            ("channel", "ALTER TABLE devices ADD COLUMN channel VARCHAR"),
            ("warranty", "ALTER TABLE devices ADD COLUMN warranty VARCHAR"),
            ("detail_json", "ALTER TABLE devices ADD COLUMN detail_json TEXT"),
        ):
            if col not in device_columns:
                conn.execute(text(ddl))

        order_columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(orders)")).fetchall()
        }

        if "device_id" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN device_id INTEGER"))

        if "merchant_id" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN merchant_id INTEGER"))

        if "recycler_id" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN recycler_id INTEGER"))

        if "price" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN price FLOAT"))

        if "update_time" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN update_time DATETIME"))

        if "express_company" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN express_company VARCHAR"))

        if "tracking_no" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN tracking_no VARCHAR"))

        if "shipping_images" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN shipping_images TEXT"))

        if "ship_time" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN ship_time DATETIME"))

        if "receive_time" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN receive_time DATETIME"))

        if "inspection_type" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN inspection_type VARCHAR"))

        if "inspection_price" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN inspection_price FLOAT"))

        if "inspection_reason" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN inspection_reason TEXT"))

        if "inspection_time" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN inspection_time DATETIME"))

        if "merchant_confirm_time" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN merchant_confirm_time DATETIME"))

        if "appeal_reason" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN appeal_reason TEXT"))

        if "appeal_time" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN appeal_time DATETIME"))

        if "close_reason" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN close_reason TEXT"))

        if "close_time" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN close_time DATETIME"))

        # ---- 财务快照字段 ----
        if "recycler_quote_amount" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN recycler_quote_amount FLOAT"))
        if "platform_fee_rate" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN platform_fee_rate FLOAT DEFAULT 0.02"))
        if "platform_fee_amount" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN platform_fee_amount FLOAT"))
        if "merchant_base_amount" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN merchant_base_amount FLOAT"))
        if "merchant_owner_rate" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN merchant_owner_rate FLOAT DEFAULT 0"))
        if "merchant_owner_commission" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN merchant_owner_commission FLOAT"))
        if "merchant_staff_rate" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN merchant_staff_rate FLOAT DEFAULT 0"))
        if "merchant_staff_commission" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN merchant_staff_commission FLOAT"))
        if "merchant_real_amount" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN merchant_real_amount FLOAT"))
        if "merchant_display_amount" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN merchant_display_amount INTEGER"))

        # ---- 资金状态机字段 ----
        if "fund_status" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN fund_status VARCHAR"))
        if "fund_frozen_amount" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN fund_frozen_amount FLOAT"))
        if "fund_deducted_amount" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN fund_deducted_amount FLOAT"))

        # ---- 取消申请字段 ----
        if "cancel_apply_status" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN cancel_apply_status VARCHAR"))
        if "cancel_apply_reason" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN cancel_apply_reason VARCHAR"))
        if "cancel_apply_time" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN cancel_apply_time DATETIME"))
        if "cancel_reject_reason" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN cancel_reject_reason VARCHAR"))

        merchant_columns = {r[1] for r in conn.execute(text("PRAGMA table_info(merchant_companies)"))}
        if "deposit_amount" not in merchant_columns:
            conn.execute(text("ALTER TABLE merchant_companies ADD COLUMN deposit_amount FLOAT DEFAULT 0"))
        for key, kind in (("deposit_followup","TEXT"),("deposit_followup_by","VARCHAR"),("deposit_followup_time","DATETIME")):
            if key not in merchant_columns:
                conn.execute(text(f"ALTER TABLE merchant_companies ADD COLUMN {key} {kind}"))
        if "settlement_mode" not in order_columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN settlement_mode VARCHAR"))
        recycler_columns={row[1] for row in conn.execute(text("PRAGMA table_info(recycler_companies)"))}
        for key in ("contact_name","contact_phone","address"):
            if key not in recycler_columns:
                conn.execute(text(f"ALTER TABLE recycler_companies ADD COLUMN {key} VARCHAR"))
        flow_columns={row[1] for row in conn.execute(text("PRAGMA table_info(fund_flows)"))}
        if "company_type" not in flow_columns:
            conn.execute(text("ALTER TABLE fund_flows ADD COLUMN company_type VARCHAR NOT NULL DEFAULT 'recycler'"))
        if "operation_key" not in flow_columns:
            conn.execute(text("ALTER TABLE fund_flows ADD COLUMN operation_key VARCHAR"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_fund_flow_operation_key ON fund_flows(operation_key)"))
        conn.commit()