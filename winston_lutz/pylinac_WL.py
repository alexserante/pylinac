import pandas as pd
import matplotlib.pyplot as plt

# Caminho do diretório com imagens do teste
txt_path = "G:/ONCORAD/Física Médica/Controles de Qualidade/1 Testes Mensais/WinstonLutz/NAO_DELETAR_wl_results.txt"

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

y_axis = "mean_2d_cax_to_bb_mm"

# Exemplo: plotar coluna A vs B
plt.plot(df["images_date"], df[y_axis])
plt.xlabel("images_date")
plt.ylabel(y_axis)
plt.title(y_axis)
plt.grid()
plt.show()
