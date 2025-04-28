from pylinac import WinstonLutz
import pandas as pd
import os

# Caminho do diretório com imagens do teste
caminho_imagens = "G:/ONCORAD/Física Médica/Controles de Qualidade/1 Testes Mensais/WinstonLutz/2025/2025-02"
caminho_excel = "G:/ONCORAD/Física Médica/Controles de Qualidade/1 Testes Mensais/WinstonLutz/NAO_DELETAR_wl_results.xlsx"

# Carregar e analisar
wl = WinstonLutz(caminho_imagens)
wl.analyze(bb_size_mm=8)

data = wl.results_data(as_dict=True)

print(wl.bb_shift_instructions())
print(wl.results_data(as_dict=True)["bb_shift_vector"])
print(wl.results())

# 3. Build the summary
summary_data = {k: v for k, v in data.items() if k not in ["image_details", "keyed_image_details"]}

# Separate and add the BB shift vector
bb_shift = summary_data.pop("bb_shift_vector", None)
if bb_shift:
    summary_data["bb_shift_x_mm"] = round(bb_shift.get("x", 0), 2)
    summary_data["bb_shift_y_mm"] = round(bb_shift.get("y", 0), 2)
    summary_data["bb_shift_z_mm"] = round(bb_shift.get("z", 0), 2)

# Cria o DataFrame com uma linha
df = pd.DataFrame([summary_data])

print(df)

# Salvar ou adicionar ao Excel existente
if os.path.exists(caminho_excel):
    with pd.ExcelWriter(caminho_excel, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        sheet = writer.sheets["resultados"]
        startrow = sheet.max_row
        df.to_excel(writer, sheet_name="resultados", index=False, header=False, startrow=startrow)
else:
    df.to_excel(caminho_excel, sheet_name="resultados", index=False)

print(f"Resultados salvos/adicionados em: {caminho_excel}")
