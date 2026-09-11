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
@app.post('/predict')
def payload(payload:TransactionPayload):
    payment=payload.model_dump()
    print(payment)
    return {
        'status':'successful',
         'message':'transaction received'
    }
