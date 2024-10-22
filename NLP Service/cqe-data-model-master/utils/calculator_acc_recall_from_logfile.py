"""
author: dungca4@fpt.com
"""

import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score, recall_score

ehe = input("gimme file name with .csv: ")
# Đọc dữ liệu từ tệp CSV
data = pd.read_csv(ehe)

# Giả sử cột 'actual' chứa nhãn thực tế và cột 'predicted' chứa nhãn dự đoán
expected = data["expected"]
prediction = data["prediction"]

# Tạo confusion matrixs
cm = confusion_matrix(expected, prediction)

# Đánh nhãn cho cột và hàng
labels = np.unique(np.concatenate((expected, prediction)))
confusion_matrix_df = pd.DataFrame(cm, index=labels, columns=labels)

print("Confusion Matrix:")
print(confusion_matrix_df)

# Tính accuracy
accuracy = accuracy_score(expected, prediction)
print("Accuracy:", accuracy)

# Tính recall
recall = recall_score(expected, prediction, average="macro", zero_division=1)
print("Recall:", recall)
