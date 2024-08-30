import cv2
import numpy as np
import matplotlib.pyplot as plt

# Carregar a imagem
image_path = r'C:\Users\a.serante\Desktop\github\pylinac\laser_CK\LASER_160_2024-07-014.tif'
image = cv2.imread(image_path)

# Converter a imagem para tons de cinza
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Aplicar um filtro Gaussiano para suavizar a imagem e reduzir o ruído
blurred = cv2.bilateralFilter(gray,9,75,75)

# Equalizar o histograma para melhorar o contraste
equalized = cv2.equalizeHist(blurred)

# Aplicar o filtro Laplaciano para realçar bordas
laplacian = cv2.Laplacian(equalized, cv2.CV_64F, ksize=5)
laplacian = np.uint8(np.absolute(laplacian))

# Detectar bordas usando o detector de Canny
edges = cv2.Canny(laplacian, 50, 150)

# Exibir a imagem original e a imagem processada lado a lado
plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.title('Imagem Original')
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

plt.subplot(1, 2, 2)
plt.title('Detecção de Bordas Melhorada')
plt.imshow(edges, cmap='gray')

plt.show()
