import os
import joblib
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated
import pandas as pd
import shap
import json

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)

app = FastAPI()
model = joblib.load('fraud_detection.pkl')
explainer = shap.TreeExplainer(model)

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
        # 1. Open the connection INSIDE the function so it safely handles incoming traffic
        conn = psycopg2.connect(DATABASE_URL)
        
        with conn:
            with conn.cursor() as cursor:
                # --- State Updates ---
                cursor.execute("SELECT transaction_count FROM device_state WHERE device_id = %s;", (device_id,))
                row = cursor.fetchone()
                device_count = (row[0] + 1) if row else 1
                cursor.execute("""
                    INSERT INTO device_state (device_id, transaction_count)
                    VALUES (%s, %s)
                    ON CONFLICT (device_id) DO UPDATE SET transaction_count = EXCLUDED.transaction_count;
                """, (device_id, device_count))
                
                cursor.execute("SELECT transaction_count FROM ip_state WHERE ip_address = %s;", (ip_address,))
                row = cursor.fetchone()
                ip_count = (row[0] + 1) if row else 1
                cursor.execute("""
                    INSERT INTO ip_state (ip_address, transaction_count)
                    VALUES (%s, %s)
                    ON CONFLICT (ip_address) DO UPDATE SET transaction_count = EXCLUDED.transaction_count;
                """, (ip_address, ip_count))
                
                cursor.execute("SELECT total_amount FROM card_state WHERE card_id = %s;", (card_id,))
                row = cursor.fetchone()
                card_total = (row[0] + amount) if row else amount
                cursor.execute("""
                    INSERT INTO card_state (card_id, total_amount)
                    VALUES (%s, %s)
                    ON CONFLICT (card_id) DO UPDATE SET total_amount = EXCLUDED.total_amount;
                """, (card_id, card_total))
                
                # --- Machine Learning Prediction ---
                features = pd.DataFrame([{
                    'amount': amount,
                    'merchant_mcc': payment['merchant_mcc'],
                    'device_attempt_count': device_count,
                    'ip_attempt_count': ip_count,
                    'card_total_amount': card_total
                }])
                
                risk_score = float(model.predict_proba(features)[0][1])
                
                # --- SHAP Explainability Fix ---
                shap_array = explainer.shap_values(features)
                
                if isinstance(shap_array, list):
                    fraud_impacts = shap_array[1][0]
                else:
                    impacts = shap_array[0]
                    # If SHAP returned a 2D array, explicitly grab the Fraud class column
                    if hasattr(impacts, 'shape') and len(impacts.shape) > 1:
                        fraud_impacts = impacts[:, 1]
                    else:
                        fraud_impacts = impacts
                
                # Force conversion to standard Python floats so the sorting function doesn't crash
                fraud_impacts = [float(v) for v in fraud_impacts]
                
                feature_names = features.columns.tolist()
                feature_impacts = list(zip(feature_names, fraud_impacts))
                top_3 = sorted(feature_impacts, key=lambda x: abs(x[1]), reverse=True)[:3]
                shap_json = json.dumps([{"feature": f, "impact": round(v, 4)} for f, v in top_3])

                # --- Decision & Storage ---
                if risk_score < 0.30:
                    decision = "Approve"
                elif risk_score <= 0.75:
                    decision = "Flag"
                else:
                    decision = "Block"
                    
                cursor.execute(""" 
                    INSERT INTO predictions (transaction_id, risk_score, decision, shap_drivers)
                    VALUES (%s, %s, %s, %s);
                """, (payment['transaction_id'], risk_score, decision, shap_json))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 2. Always close the connection safely
        if 'conn' in locals():
            conn.close()

    return {
        "transaction_id": payment['transaction_id'],
        "risk_score": round(risk_score, 4),
        "decision": decision
    }     