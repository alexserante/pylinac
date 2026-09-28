import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter.filedialog import askopenfilename
import traceback
import tempfile
import numpy as np
import pydicom
from pylinac import FieldAnalysis, Centering, Edge, Normalization, Protocol, Interpolation
from pylinac.metrics.profile import (
    PenumbraLeftMetric, PenumbraRightMetric,
    SymmetryPointDifferenceMetric, FlatnessDifferenceMetric,
    CAXToLeftEdgeMetric, CAXToRightEdgeMetric
)


fa = None
file_path = None
tmp_cropped_path = None

# -------------------- helpers --------------------


def message_console(text_console):
    tk.Label(master=frm_console, text=text_console).grid(sticky="w")


def detect_beam_is_dark(img):
    """Heuristic: compare center vs corner medians."""
    h, w = img.shape
    r5, c5 = max(1, h // 20), max(1, w // 20)
    center = np.median(img[h // 2 - r5:h // 2 + r5 + 1, w // 2 - c5:w // 2 + c5 + 1])
    corner = np.median(img[0:r5, 0:c5])
    return center < corner  # dark beam on bright background?


def get_beam_center(img):
    """Return (yc, xc) index of beam peak (bright or dark)."""
    h, w = img.shape
    yc = h / 2
    xc = w / 2
    return int(yc), int(xc)


def crop_bounds_around_center(shape, yc, xc, box_px):
    h, w = shape
    half = box_px // 2
    y0 = max(0, yc - half)
    y1 = min(h, yc + half)
    x0 = max(0, xc - half)
    x1 = min(w, xc + half)
    return y0, y1, x0, x1


def shift_ipp_for_crop(ds, y0, x0):
    """Shift ImagePositionPatient using IOP & PixelSpacing (handles orientation)."""
    if ("PixelSpacing" not in ds or "ImagePositionPatient" not in ds or "ImageOrientationPatient" not in ds):
        return  # nothing to do safely

    ps_row, ps_col = map(float, ds.PixelSpacing)  # mm
    ipp = np.array(list(map(float, ds.ImagePositionPatient)), dtype=float)
    iop = list(map(float, ds.ImageOrientationPatient))
    # row and col direction cosines (3-vectors)
    row_cos = np.array(iop[0:3], dtype=float)
    col_cos = np.array(iop[3:6], dtype=float)
    # NOTE: y index steps along rows; x index steps along cols
    delta = y0 * ps_row * row_cos + x0 * ps_col * col_cos
    new_ipp = ipp + delta
    ds.ImagePositionPatient = [str(v) for v in new_ipp]


def crop_dicom_to_temp(input_path, box_size_px=None, box_size_mm=None):
    """Auto-crop around beam center. Returns path to temp cropped DICOM."""
    ds = pydicom.dcmread(input_path)
    img = ds.pixel_array

    # resolve box size in pixels
    if box_size_px is None and box_size_mm is None:
        box_size_px = 300  # default

    if box_size_px is None and box_size_mm is not None:
        # convert mm -> px using row spacing (approx square pixels for EPID)
        if "PixelSpacing" in ds:
            ps_row = float(ds.PixelSpacing[0])
            box_size_px = max(20, int(round(box_size_mm / ps_row)))
        else:
            box_size_px = 300

    box_size_px = int(max(20, box_size_px))  # keep reasonable minimum

    # find center and crop bounds
    yc, xc = get_beam_center(img)
    y0, y1, x0, x1 = crop_bounds_around_center(img.shape, yc, xc, box_size_px)

    cropped = img[y0:y1, x0:x1]

    # write cropped DICOM (update geometry)
    ds_out = ds.copy()
    ds_out.PixelData = cropped.tobytes()
    ds_out.Rows, ds_out.Columns = cropped.shape

    # shift IPP correctly using orientation
    shift_ipp_for_crop(ds_out, y0, x0)

    # save to temp file
    tf = tempfile.NamedTemporaryFile(prefix="pylinac_crop_", suffix=".dcm", delete=False)
    tf.close()
    ds_out.save_as(tf.name)

    return tf.name


def min_band_ratio_from_dicom(dcm_path, target_ratio=0.02, min_pixels=3):
    try:
        ds = pydicom.dcmread(dcm_path, stop_before_pixels=True)
        rows, cols = int(ds.Rows), int(ds.Columns)
    except Exception:
        rows = cols = 512
    rx = max(target_ratio, min_pixels / max(1, cols))
    ry = max(target_ratio, min_pixels / max(1, rows))
    return rx, ry

# -------------------- actions --------------------


def open_files_path():
    global file_path
    file_path = askopenfilename(title='Selecione o arquivo de imagem')
    if not file_path:
        message_console("Nenhum arquivo selecionado!")
        return
    message_console("Arquivo selecionado: " + file_path)
    analyze_field()


def parse_float(var, name):
    try:
        return float(var.get().replace(",", "."))
    except ValueError:
        raise ValueError(f"O parâmetro '{name}' deve ser numérico.")


def check_ratio(value, name):
    if not 0 <= value <= 1:
        raise ValueError(f"O parâmetro '{name}' deve estar entre 0.0 e 1.0.")


def get_enum(enum_class, value):
    if value == "NONE":
        return None
    return getattr(enum_class, value)


def get_analysis_params():
    protocol = get_enum(Protocol, var_protocol.get())
    centering = get_enum(Centering, var_centering.get())
    interpolation = get_enum(Interpolation, var_interpolation.get())
    normalization = get_enum(Normalization, var_normalization.get())
    edge_method = get_enum(Edge, var_edge.get())

    vert_position = parse_float(var_vert_position, "vert_position")
    horiz_position = parse_float(var_horiz_position, "horiz_position")
    vert_width = parse_float(var_vert_width, "vert_width")
    horiz_width = parse_float(var_horiz_width, "horiz_width")
    in_field_ratio = parse_float(var_in_field_ratio, "in_field_ratio")
    slope_exclusion_ratio = parse_float(var_slope_exclusion_ratio, "slope_exclusion_ratio")
    penumbra_low = parse_float(var_penumbra_low, "penumbra_low")
    penumbra_high = parse_float(var_penumbra_high, "penumbra_high")
    interpolation_resolution_mm = parse_float(var_interp_res, "interpolation_resolution_mm")
    edge_smoothing_ratio = parse_float(var_edge_smoothing_ratio, "edge_smoothing_ratio")
    hill_window_ratio = parse_float(var_hill_window_ratio, "hill_window_ratio")

    for value, name in [
        (vert_position, "vert_position"),
        (horiz_position, "horiz_position"),
        (vert_width, "vert_width"),
        (horiz_width, "horiz_width"),
        (in_field_ratio, "in_field_ratio"),
        (slope_exclusion_ratio, "slope_exclusion_ratio"),
        (edge_smoothing_ratio, "edge_smoothing_ratio"),
        (hill_window_ratio, "hill_window_ratio"),
    ]:
        check_ratio(value, name)

    if not 0 <= penumbra_low < penumbra_high <= 100:
        raise ValueError("A penumbra deve obedecer: 0 <= menor < maior <= 100.")

    if interpolation_resolution_mm <= 0:
        raise ValueError("interpolation_resolution_mm deve ser maior que zero.")

    return {
        "protocol": protocol,
        "centering": centering,
        "vert_position": vert_position,
        "horiz_position": horiz_position,
        "vert_width": vert_width,
        "horiz_width": horiz_width,
        "in_field_ratio": in_field_ratio,
        "slope_exclusion_ratio": slope_exclusion_ratio,
        "invert": var_invert.get(),
        "is_FFF": var_is_fff.get(),
        "penumbra": (penumbra_low, penumbra_high),
        "interpolation": interpolation,
        "interpolation_resolution_mm": interpolation_resolution_mm,
        "ground": var_ground.get(),
        "normalization_method": normalization,
        "edge_detection_method": edge_method,
        "edge_smoothing_ratio": edge_smoothing_ratio,
        "hill_window_ratio": hill_window_ratio,
    }


def analyze_field():
    global fa, tmp_cropped_path

    if not file_path:
        message_console("Selecione um arquivo primeiro.")
        return

    # optional auto-crop
    # 20x20 -> 1000
    # 15x15 -> 800
    # 10x10 -> 500
    # 5x5 -> 250
    path_for_analysis = file_path
    try:
        if var_autocrop.get():
            box_px = int(entry_box_px.get()) if entry_box_px.get().strip() else 300
            path_for_analysis = crop_dicom_to_temp(file_path, box_size_px=box_px)
            tmp_cropped_path = path_for_analysis
            message_console(f"Auto-crop aplicado (caixa {box_px}px).")
    except Exception as e:
        traceback.print_exc()
        messagebox.showwarning("Auto-crop", f"Falha no auto-crop: {e}\nProsseguindo com imagem original.")
        path_for_analysis = file_path

    # ensure averaging band has pixels
    xw, yw = min_band_ratio_from_dicom(path_for_analysis, target_ratio=0.02, min_pixels=3)



    fa = FieldAnalysis(path_for_analysis)
    fa = FieldAnalysis(path_for_analysis)
    
    try:
        params = get_analysis_params()
    
        fa.analyze(**params)
        
        show_results_text(fa.results())
    
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Erro na análise", str(e))
        message_console("Falha na análise.")
        return

    print(fa.results())
    fa.plot_analyzed_image()
    message_console("Análise concluída!")


def show_results_text(text):
    txt_results.delete("1.0", tk.END)
    txt_results.insert(tk.END, text)
    

def show_histogram():
    if fa is None:
        message_console("Análise não realizada ainda.")
        return
    try:
        fa.plot_histogram()
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Erro no histograma", str(e))


# -------------------- UI --------------------
window = tk.Tk()

frm_left = tk.Frame(master=window)
frm_left.grid(row=0, column=0, sticky="n")

frm_right = tk.Frame(master=window)
frm_right.grid(row=0, column=1, sticky="ns", padx=2, pady=2)

frm_select = tk.LabelFrame(master=frm_left, text="Diretório", font="VERDANA")
frm_select.grid(row=0, column=0, padx=2, pady=2)

tk.Button(frm_select, text="Selecionar arquivo", font="VERDANA",
          command=open_files_path).grid(row=0, column=0, columnspan=2, padx=10, pady=5)

# Auto-crop controls
frm_crop = tk.LabelFrame(master=frm_left, text="Crop image", font="VERDANA")
frm_crop.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

var_autocrop = tk.BooleanVar(value=False)
tk.Checkbutton(frm_crop, text="Ativar crop", variable=var_autocrop).grid(row=0, column=0, sticky="w", padx=8, pady=4)

tk.Label(frm_crop, text="Tamanho da caixa (px):").grid(row=1, column=0, sticky="w", padx=1)
entry_box_px = tk.Entry(frm_crop, width=8)
entry_box_px.insert(0, "300")
entry_box_px.grid(row=1, column=1, sticky="w", padx=1)

tk.Label(
    frm_crop,
    text=(" # 20x20cm² -> 1000 (no crop)\n"
         " # 15x15 cm²-> 800\n"
   " # 10x10cm² -> 500\n"
   " # 5x5cm² -> 280"
   ),
    fg="gray",
    justify="left"
).grid(
    row=0,
    column=3,
    rowspan=2,
    sticky="w",
    padx=(12, 8)
)

frm_params = tk.LabelFrame(master=frm_left, text="Parâmetros da análise", font="VERDANA")
frm_params.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

# Dropdown variables
var_protocol = tk.StringVar(value="VARIAN")
var_centering = tk.StringVar(value="BEAM_CENTER")
var_interpolation = tk.StringVar(value="LINEAR")
var_normalization = tk.StringVar(value="BEAM_CENTER")
var_edge = tk.StringVar(value="FWHM")

# Numeric variables
var_vert_position = tk.StringVar(value="0.5")
var_horiz_position = tk.StringVar(value="0.5")
var_vert_width = tk.StringVar(value="0.05")
var_horiz_width = tk.StringVar(value="0.05")
var_in_field_ratio = tk.StringVar(value="0.8")
var_slope_exclusion_ratio = tk.StringVar(value="0.2")
var_penumbra_low = tk.StringVar(value="20")
var_penumbra_high = tk.StringVar(value="80")
var_interp_res = tk.StringVar(value="0.5")
var_edge_smoothing_ratio = tk.StringVar(value="0.003")
var_hill_window_ratio = tk.StringVar(value="0.15")

# Boolean variables
var_invert = tk.BooleanVar(value=True)
var_is_fff = tk.BooleanVar(value=False)
var_ground = tk.BooleanVar(value=True)

def add_dropdown(parent, label, variable, values, row):
    tk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=3)
    cb = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=28)
    cb.grid(row=row, column=1, sticky="w", padx=8, pady=3)
    return cb

def add_entry(parent, label, variable, row):
    tk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=3)
    entry = tk.Entry(parent, textvariable=variable, width=12)
    entry.grid(row=row, column=1, sticky="w", padx=8, pady=3)
    return entry


add_dropdown(frm_params, "Protocol:", var_protocol, ["VARIAN", "ELEKTA"], 0)

add_dropdown(
    frm_params,
    "Centering:",
    var_centering,
    ["BEAM_CENTER", "GEOMETRIC_CENTER", "MANUAL"],
    1
)

add_entry(frm_params, "Vert position:", var_vert_position, 2)
add_entry(frm_params, "Horiz position:", var_horiz_position, 3)

add_entry(frm_params, "Vert width:", var_vert_width, 4)
add_entry(frm_params, "Horiz width:", var_horiz_width, 5)

add_entry(frm_params, "In-field ratio:", var_in_field_ratio, 6)
add_entry(frm_params, "Slope exclusion ratio:", var_slope_exclusion_ratio, 7)

add_entry(frm_params, "Penumbra lower (%):", var_penumbra_low, 8)
add_entry(frm_params, "Penumbra upper (%):", var_penumbra_high, 9)

add_dropdown(
    frm_params,
    "Interpolation:",
    var_interpolation,
    ["LINEAR", "SPLINE"],
    10
)

add_entry(frm_params, "Interpolation resolution (mm):", var_interp_res, 11)

add_dropdown(
    frm_params,
    "Normalization:",
    var_normalization,
    ["BEAM_CENTER", "GEOMETRIC_CENTER", "MAX"],
    12
)

add_dropdown(
    frm_params,
    "Edge detection:",
    var_edge,
    ["FWHM", "INFLECTION_DERIVATIVE", "INFLECTION_HILL"],
    13
)

add_entry(frm_params, "Edge smoothing ratio:", var_edge_smoothing_ratio, 14)
add_entry(frm_params, "Hill window ratio:", var_hill_window_ratio, 15)

tk.Checkbutton(frm_params, text="Invert", variable=var_invert).grid(
    row=16, column=0, sticky="w", padx=8, pady=3
)

tk.Checkbutton(frm_params, text="Feixe FFF", variable=var_is_fff).grid(
    row=16, column=1, sticky="w", padx=8, pady=3
)

tk.Checkbutton(frm_params, text="Ground", variable=var_ground).grid(
    row=17, column=0, sticky="w", padx=8, pady=3
)

tk.Button(
    frm_params,
    text="Analisar novamente",
    font="VERDANA",
    command=analyze_field
).grid(row=18, column=0, columnspan=2, padx=10, pady=8)

frm_results = tk.LabelFrame(
    master=frm_right,
    text="Resultados",
    font="VERDANA"
)

frm_results.grid(row=0, column=0, sticky="nsew")

scroll_results = tk.Scrollbar(frm_results)
scroll_results.grid(row=0, column=1, sticky="ns")

txt_results = tk.Text(
    frm_results,
    width=70,
    height=52,
    wrap="word",
    yscrollcommand=scroll_results.set,
    font=("Consolas", 9)
)

txt_results.grid(row=0, column=0, sticky="nsew")

scroll_results.config(command=txt_results.yview)

frm_console = tk.LabelFrame(master=window, width=800, height=50, text="Console")
frm_console.grid(row=2, column=0, columnspan=3, sticky="nw", padx=5, pady=5)

window.mainloop()

# (Optional) clean temp file on exit if you want:
# if tmp_cropped_path and os.path.exists(tmp_cropped_path):
#     os.remove(tmp_cropped_path)
