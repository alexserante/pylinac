import pandas as pd
import matplotlib.pyplot as plt

# Caminho do diretório com imagens do teste
# Substitua com o caminho correto do arquivo
txt_path = "R:/ONCORAD/Física Médica/Controles de Qualidade/1 Testes Mensais/WinstonLutz/NAO_DELETAR_wl_results.txt"

# Carregar os dados
df = pd.read_csv(txt_path, sep="\t")

'''images_date
pylinac_version
date_of_analysis
warnings
max_2d_cax_to_bb_mm
median_2d_cax_to_bb_mm
mean_2d_cax_to_bb_mm
max_2d_cax_to_epid_mm
median_2d_cax_to_epid_mm
mean_2d_cax_to_epid_mm
gantry_3d_iso_diameter_mm
coll_2d_iso_diameter_mm
couch_2d_iso_diameter_mm
gantry_coll_3d_iso_diameter_mm
num_total_images
num_gantry_images
num_coll_images
num_couch_images
num_gantry_coll_images
max_gantry_rms_deviation_mm
max_epid_rms_deviation_mm
max_coll_rms_deviation_mm
max_couch_rms_deviation_mm
bb_shift_x_mm
bb_shift_y_mm
bb_shift_z_mm'''

# Lista de dados para plotar e seus respectivos títulos
plots = [
    (["max_2d_cax_to_bb_mm", "median_2d_cax_to_bb_mm", "mean_2d_cax_to_bb_mm"],
     "Resultados de CAX"),

    (["gantry_3d_iso_diameter_mm", "max_gantry_rms_deviation_mm"],
     "Resultados de Gantry"),

    (["coll_2d_iso_diameter_mm", "max_coll_rms_deviation_mm"],
     "Resultados de Collimador"),

    (["couch_2d_iso_diameter_mm", "max_couch_rms_deviation_mm"],
     "Resultados de Couch"),
]

# Criando a figura com 5 subgráficos
fig, axs = plt.subplots(4, 1, figsize=(10, 20))

# Iterando sobre cada conjunto de dados e títulos
for i, (cols, title) in enumerate(plots):
    axs[i].plot(df["images_date"], df[cols], marker='o', linestyle='-')
    axs[i].set_xlabel("images_date")
    axs[i].set_ylabel("Valor")
    axs[i].set_title(title)
    axs[i].legend(cols, loc="upper left", bbox_to_anchor=(1.05, 1))
    axs[i].grid()

    axs[i].tick_params(axis='x', rotation=45)

    if i != 3:
        axs[i].tick_params(labelbottom=False)  # Remove os rótulos do eixo X nos gráficos acima

# Ajustando o layout para evitar sobreposição
plt.tight_layout(pad=6.0)
plt.show()
