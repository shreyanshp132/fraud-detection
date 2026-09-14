import pandas as pd
import numpy as np
np.random.seed(42)
n_sample=1000
data={
    'amount':np.random.uniform(10.0, 3000.0, n_sample),
    'merchant_mcc':np.random.choice([5732,5411,5812], n_sample),
    'device_attempts_count':np.random.randint(1, 20, n_sample),
    'ip_attempt_count':np.random.randint(1, 20, n_sample),
    'card_total_amount':np.random.uniform(10.0, 10000.0, n_sample)
}
df=pd.DataFrame(data)
df['is_fraud']=np.where((df['amount']>2000)&(df['device_attempts_count']>10),1,0)
x=df.drop(columns=['is_fraud'])
y=df['is_fraud']

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
x_train, x_test, y_train, y_test=train_test_split(x,y, test_size=0.2, random_state=42, stratify=y)
rf=RandomForestClassifier(n_estimators=100,random_state=42)
rf.fit(x_train,y_train)
y_predict=rf.predict(x_test)
print(f"Accuracy: {accuracy_score(y_test, y_predict):.4f}")
print(classification_report(y_test, y_predict))

import joblib
joblib.dump(rf,'fraud_detection.pkl')
