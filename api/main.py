import hmac
import os
import uuid
from decimal import Decimal
import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://minipay:minipay_dev_only@localhost:5432/minipay")
API_KEY = os.getenv("API_KEY", "dev-api-key")
app = FastAPI(title="MiniPay API", version="1.0.0")

class CustomerInput(BaseModel):
    customer_ref: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)

class PaymentInput(BaseModel):
    customer_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)

def require_api_key(x_api_key: str | None = Header(default=None)):
    if not x_api_key or not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

def connect():
    try:
        return psycopg.connect(DATABASE_URL, connect_timeout=3)
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

@app.get("/health")
def health():
    with connect() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok", "database": "ok"}

@app.post("/api/customers", status_code=201, dependencies=[Depends(require_api_key)])
def create_customer(payload: CustomerInput):
    with connect() as conn:
        row = conn.execute(
            """INSERT INTO customers(customer_ref, name) VALUES (%s, %s)
               ON CONFLICT (customer_ref) DO NOTHING
               RETURNING id, customer_ref, name, created_at""",
            (payload.customer_ref, payload.name),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=409, detail="Customer reference already exists")
    return {"id": row[0], "customer_ref": row[1], "name": row[2], "created_at": row[3]}

@app.post("/api/payments", status_code=201, dependencies=[Depends(require_api_key)])
def create_payment(payload: PaymentInput, idempotency_key: str = Header(alias="Idempotency-Key", min_length=1)):
    with connect() as conn:
        if not conn.execute("SELECT 1 FROM customers WHERE id=%s", (payload.customer_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Customer not found")
        row = conn.execute(
            """INSERT INTO transactions
               (transaction_ref, customer_id, amount, status, created_at, idempotency_key)
               VALUES (%s, %s, %s, 'PROCESSING', CURRENT_TIMESTAMP, %s)
               ON CONFLICT (idempotency_key) DO NOTHING
               RETURNING id, transaction_ref, customer_id, amount, status, created_at""",
            ("TXN" + uuid.uuid4().hex[:12].upper(), payload.customer_id, payload.amount, idempotency_key),
        ).fetchone()
        if row is None:
            row = conn.execute(
                """SELECT id, transaction_ref, customer_id, amount, status, created_at
                   FROM transactions WHERE idempotency_key=%s""", (idempotency_key,)
            ).fetchone()
            if row[2] != payload.customer_id or Decimal(row[3]) != payload.amount:
                raise HTTPException(status_code=409, detail="Idempotency key was used for a different request")
    return _payment(row)

def _payment(row):
    return {"id": row[0], "transaction_ref": row[1], "customer_id": row[2],
            "amount": str(row[3]), "status": row[4], "created_at": row[5]}

@app.get("/api/payments/{transaction_ref}")
def get_payment(transaction_ref: str):
    with connect() as conn:
        row = conn.execute(
            """SELECT t.id, t.transaction_ref, t.customer_id, t.amount, t.status,
                      t.created_at, t.completed_at, t.failure_code, c.customer_ref, c.name
               FROM transactions t JOIN customers c ON c.id=t.customer_id
               WHERE t.transaction_ref=%s""", (transaction_ref,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Payment not found")
        callbacks = conn.execute(
            """SELECT attempt_no, http_status, callback_status, attempted_at
               FROM callbacks WHERE transaction_id=%s ORDER BY attempt_no""", (row[0],)
        ).fetchall()
    return {"id": row[0], "transaction_ref": row[1], "customer_id": row[2],
            "amount": str(row[3]), "status": row[4], "created_at": row[5],
            "completed_at": row[6], "failure_code": row[7],
            "customer": {"customer_ref": row[8], "name": row[9]},
            "callbacks": [{"attempt_no": cb[0], "http_status": cb[1],
                           "status": cb[2], "attempted_at": cb[3]} for cb in callbacks]}

@app.get("/api/customers/{customer_id}/payments")
def customer_payments(customer_id: int):
    with connect() as conn:
        if not conn.execute("SELECT 1 FROM customers WHERE id=%s", (customer_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Customer not found")
        rows = conn.execute(
            """SELECT id, transaction_ref, customer_id, amount, status, created_at
               FROM transactions WHERE customer_id=%s ORDER BY created_at DESC LIMIT 100""",
            (customer_id,),
        ).fetchall()
    return {"items": [_payment(row) for row in rows]}

@app.get("/")
def index():
    return {"service": "MiniPay", "docs": "/docs", "health": "/health"}
