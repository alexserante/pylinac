import cv2
import numpy as np
import matplotlib.pyplot as plt

# Carregar a imagem
image_path = r'C:\Users\a.serante\Desktop\github\pylinac\laser_CK\LASER_160_2024-07-014.tif'
image = cv2.imread(image_path)

# Converter a imagem para tons de cinza
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Aplicar um blur para reduzir o ruído
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# Detectar bordas usando Canny
edges = cv2.Canny(blurred, 50, 150)

# Encontrar contornos
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Identificar o maior contorno (assumindo que a marca da caneta é a maior)
largest_contour = max(contours, key=cv2.contourArea)

# Calcular o centro do contorno
M = cv2.moments(largest_contour)
if M["m00"] != 0:
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
else:
    cX, cY = 0, 0

# Desenhar o centro e o contorno na imagem original
cv2.drawContours(image, [largest_contour], -1, (0, 255, 0), 2)
cv2.circle(image, (cX, cY), 7, (255, 0, 0), -1)
cv2.putText(image, "Center", (cX - 20, cY - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

print(cX, cY)

# Exibir a imagem com o contorno e o centro marcado
plt.figure(figsize=(10, 10))
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.show()
