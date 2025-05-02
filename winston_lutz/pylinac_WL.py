import pandas as pd
import matplotlib.pyplot as plt

# Caminho do diretório com imagens do teste
txt_path = "G:/ONCORAD/Física Médica/Controles de Qualidade/1 Testes Mensais/WinstonLutz/NAO_DELETAR_wl_results.txt"

df = pd.read_csv(txt_path, sep="\t")

# Exemplo: plotar coluna A vs B
plt.plot(df["images_date"], df["max_2d_cax_to_epid_mm"])
plt.xlabel("images_date")
plt.ylabel("max_2d_cax_to_epid_mm")
plt.title("max_2d_cax_to_epid_mm")
plt.grid()
plt.show()
