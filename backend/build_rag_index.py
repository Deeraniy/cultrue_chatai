import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle

# 1. 读取数据
csv_path = 'literature_texts.csv'
df = pd.read_csv(csv_path)
texts = df['text'].fillna('').tolist()
meta = df[['liter_id', 'liter_name']].to_dict(orient='records')

# 2. 加载embedding模型
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

# 3. 构建FAISS索引
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# 4. 保存索引和元数据
faiss.write_index(index, 'literature_faiss.index')
with open('literature_meta.pkl', 'wb') as f:
    pickle.dump(meta, f)

print('RAG知识库构建完成，向量库和元数据已保存。') 