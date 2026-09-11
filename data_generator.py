import random
import time
import uuid
import requests
from datetime import datetime, timezone
card_ids=['card_001','card_002','card-003','card_004','card_005','card_006','card-007']
device_ids=['dev_01','dev_02','dev_03','dev_04']
mcc_codes=[5732,5411,5812]
ip_address=['2001:db8::1','fe80::1ff:fe23:4567:890a']
while True:
    transaction_id = str(uuid.uuid4())
    selected_cards=random.choice(card_ids)
    amount=random.uniform(10.0, 150.0)
    selected_device=random.choice(device_ids)
    selected_mcc=random.choice(mcc_codes)
    selected_ip=random.choice(ip_address)
    current_time=current_time = datetime.now(timezone.utc).isoformat()
    # print(amount)
    if random.random()<0.05:
        amount=2500

    transaction={
        'transaction_id': transaction_id,
        'selected_cards':selected_cards,
        'amount':amount,
        'merchant_mcc':selected_mcc,
        'device_id':selected_device,
        'ip_address':selected_ip,
        'timestamp':current_time        
    }
    response = requests.post('http://127.0.0.1:8000/predict', json=transaction)
    print(f"Server response: {response.status_code} | {response.text}")

    time.sleep(1)
