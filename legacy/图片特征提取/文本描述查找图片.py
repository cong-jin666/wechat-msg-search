import os
from keras.applications.resnet50 import ResNet50, preprocess_input
from keras.preprocessing import image
from keras.models import Model
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from keras.applications.resnet_v2 import ResNet50V2
'''model = ResNet50V2(weights='imagenet', include_top=False)
output_layer = model.get_layer(name='input_1')  '''


from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Model

# 加载预训练的ResNet50模型，去掉最后的分类层
base_model = ResNet50(weights='imagenet')
model = Model(inputs=base_model.input, outputs=base_model.get_layer('avg_pool').output)

# 示例数据集（仅包含图片文件名）
data = [
    "image1.jpg", "image2.jpg", "image3.jpg", "image4.jpg", "image5.jpg",
    "image6.jpg", "image7.jpg", "image8.jpg", "image9.jpg", "image10.jpg"
]

# 图片目录路径
image_dir = 'pic/'

# 构建图片路径
image_paths = [os.path.join(image_dir, item) for item in data]

# 提取所有图片的特征
def extract_image_features(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    features = model.predict(x)
    return features.flatten()

image_features = np.array([extract_image_features(img_path) for img_path in image_paths])

# 查询描述
query_description = "A beautiful mountain range with snow-capped peaks"

# 提取文本特征
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform([query_description])
query_features = tfidf_matrix.toarray().flatten()

# 查找与查询描述最相似的图片
def find_matching_images(query_features, image_features, image_paths):
    similarities = cosine_similarity(query_features.reshape(1, -1), image_features).flatten()
    sorted_indices = np.argsort(-similarities)
    matching_images = [image_paths[i] for i in sorted_indices]
    return matching_images

matching_images = find_matching_images(query_features, image_features, image_paths)
print("Matching images:", matching_images)
