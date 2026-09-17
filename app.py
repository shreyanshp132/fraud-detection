import os
import joblib
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated
import pandas as pd

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)

app = FastAPI()
model = joblib.load('fraud_detection.pkl')

class TransactionPayload(BaseModel):
    transaction_id: Annotated[str, Field(...)]
    selected_cards: Annotated[str, Field(...)]
    amount: Annotated[float, Field(...)]
    device_id: Annotated[str, Field(...)]
    merchant_mcc: Annotated[int, Field(...)]
    ip_address: Annotated[str, Field(...)]
    timestamp: Annotated[str, Field(...)]

@app.post('/predict')
def payload(payload: TransactionPayload):
    payment = payload.model_dump()
    device_id = payment['device_id']
    ip_address = payment['ip_address']
    card_id = payment['selected_cards']
    amount = payment['amount']

    try:
        with conn:
            with conn.cursor() as cursor:
                # Device state
                cursor.execute("SELECT transaction_count FROM device_state WHERE device_id = %s;", (device_id,))
                row = cursor.fetchone()
                device_count = (row[0] + 1) if row else 1
                cursor.execute("""
                    INSERT INTO device_state (device_id, transaction_count)
                    VALUES (%s, %s)
                    ON CONFLICT (device_id)
                    DO UPDATE SET transaction_count = EXCLUDED.transaction_count;
                """, (device_id, device_count))

                # IP state
                cursor.execute("SELECT transaction_count FROM ip_state WHERE ip_address = %s;", (ip_address,))
                row = cursor.fetchone()
                ip_count = (row[0] + 1) if row else 1
                cursor.execute("""
                    INSERT INTO ip_state (ip_address, transaction_count)
                    VALUES (%s, %s)
                    ON CONFLICT (ip_address)
                    DO UPDATE SET transaction_count = EXCLUDED.transaction_count;
                """, (ip_address, ip_count))

                # Card state
                cursor.execute("SELECT total_amount FROM card_state WHERE card_id = %s;", (card_id,))
                row = cursor.fetchone()
                card_total = (row[0] + amount) if row else amount
                cursor.execute("""
                    INSERT INTO card_state (card_id, total_amount)
                    VALUES (%s, %s)
                    ON CONFLICT (card_id)
                    DO UPDATE SET total_amount = EXCLUDED.total_amount;
                """, (card_id, card_total))
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # Features calculated dynamically from the persistent DB state
    features = pd.DataFrame([{
        'amount': payment['amount'],
        'merchant_mcc': payment['merchant_mcc'],
        'device_attempt_count': device_count,
        'ip_attempt_count': ip_count,
        'card_total_amount': card_total
    }])

    risk_score = float(model.predict_proba(features)[0][1])

    if risk_score < 0.30:
        decision = "Approve"
    elif risk_score <= 0.75:
        decision = "Flag"
    else:
        decision = "Block"

    return {
        "transaction_id": payment['transaction_id'],
        "risk_score": round(risk_score, 4),
        "decision": decision
    }