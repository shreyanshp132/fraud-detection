from fastapi import FastAPI,Path, HTTPException
from pydantic import BaseModel,Field
from typing import Annotated 
import joblib
app=FastAPI()
class TransactionPayload(BaseModel):
    transaction_id: Annotated[str,Field(...,)]
    selected_cards:Annotated[str,Field(...,)]
    amount:Annotated[float,Field(...,)]
    device_id:Annotated[str,Field(...,)]
    merchant_mcc:Annotated[int,Field(...,)]
    ip_address:Annotated[str,Field(...,)]
    timestamp:Annotated[str,Field(...,)]

device_counts={}
ip_counts={}
cards_amount={}
model = joblib.load('fraud_detection.pkl')
@app.post('/predict')
def payload(payload:TransactionPayload):
    payment=payload.model_dump()
    device_id=payment['device_id']
    if device_id in device_counts:
        device_counts[device_id]+=1
    else:
        device_counts[device_id]=1

    ip_address=payment['ip_address']
    if ip_address in ip_counts:
        ip_counts[ip_address]+=1
    else:
        ip_counts[ip_address]=1

    cards=payment['selected_cards']
    Amount=payment['amount']
    if cards in cards_amount:
        cards_amount[cards]+=Amount
    else:
        cards_amount[cards]=Amount

    payment['device_attempt_count']=device_counts[device_id]
    payment['ip_attempt_count'] = ip_counts[ip_address]
    payment['card_total_amount'] = cards_amount[cards]
    print(payment)

    features = [[
        payment['amount'], 
        payment['merchant_mcc'], 
        payment['device_attempt_count'], 
        payment['ip_attempt_count'], 
        payment['card_total_amount']
    ]]
    
    risk_score=float(model.predict_proba(features)[0][1])
    if risk_score<0.30:
        decision= "Approve"
    elif risk_score<=0.75:
        decision= 'Flag'
    else:
        decision= "Block"
    
    return {
        "transaction_id": payment['transaction_id'], 
        "risk_score": round(risk_score,4),
        "decision": decision
    }

    

