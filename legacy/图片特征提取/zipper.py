from PIL import Image
import numpy as np

# 加载图像
image_path = 'jokerpoke.jpg'
image = Image.open(image_path)

# 将图像调整为256x256
image = image.resize((256, 256))

# 将图像转换为numpy数组
image_array = np.array(image)

# 检查数组的形状
print(image_array.shape)  # 应该是(256, 256, 3)
