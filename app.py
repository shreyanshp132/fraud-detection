from fastapi import FastAPI,Path, HTTPException
from pydantic import BaseModel,Field
from typing import Annotated 
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
@app.post('/predict')
def payload(payload:TransactionPayload):
    payment=payload.model_dump()
    device_id=payment['device_id']
    if device_id in device_counts:
        device_counts[device_id]+=1
    else:
        device_counts[device_id]=1
    payment['device_attempt_count']=device_counts[device_id]
    print(payment)
    return {
        'status':'successful',
         'message':'transaction received'
    }

