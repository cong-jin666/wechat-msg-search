import os
import cv2
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Model

# 加载预训练的ResNet50模型，去掉最后的分类层
base_model = ResNet50(weights='imagenet')
model = Model(inputs=base_model.input, outputs=base_model.get_layer('avg_pool').output)

def extract_image_features(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    features = model.predict(x)
    return features.flatten()

def extract_text_features(descriptions):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(descriptions)
    return tfidf_matrix, vectorizer

def find_matching_images(query_description, image_dir, descriptions):
    # 提取查询描述的特征
    query_vector = vectorizer.transform([query_description])
    
    # 计算查询描述与所有描述的相似度
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    
    # 根据相似度排序
    sorted_indices = np.argsort(-similarities)
    
    # 获取最相似的图片路径
    matching_images = [os.path.join(image_dir, descriptions[i].split(':')[0]) for i in sorted_indices]
    return matching_images[:5]

# 示例数据集（假设每张图片的描述格式为 "image_name: description"）
data = [
    "image1.jpg: A beautiful sunset over the mountains",
    "image2.jpg: A serene lake with boats on it",
    "image3.jpg: A group of friends having a picnic",
    "image4.jpg: A laptop on the table"
    "image5.jpg: A majestic mountain range with snow-capped peaks",
    "image6.jpg: A serene beach with golden sand and clear blue water",
    "image7.jpg: A bustling city street filled with people and traffic",
    "image8.jpg: A quiet forest path leading to a hidden waterfall",
    "image9.jpg: A sunny beach during the daytime with warm sunshine",
    "image10.jpg: A cozy cabin in the mountains with a fireplace",
    "image11.jpg: A historic old town with cobblestone streets and narrow alleys",
    "image12.jpg: A lush garden with colorful flowers and green grass",
    "image13.jpg: A futuristic cityscape with flying cars and neon lights",
    "image14.jpg: A peaceful countryside scene with rolling hills and farmland"
    # 添加更多描述...
]

# 提取图片和描述
image_dir = 'pic/'
descriptions = [item.split(':')[1].strip() for item in data]
image_paths = [os.path.join(image_dir, item.split(':')[0].strip()) for item in data]

# 提取所有图片的特征
image_features = np.array([extract_image_features(img_path) for img_path in image_paths])

# 提取所有描述的文本特征
tfidf_matrix, vectorizer = extract_text_features(descriptions)

# 查询描述
query_description = "beach"

# 查找匹配的图片
matching_images = find_matching_images(query_description, image_dir, descriptions)
print("Matching images:", matching_images)
