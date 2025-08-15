import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
import traceback
import tempfile
import numpy as np
import pydicom
from pylinac import FieldProfileAnalysis, Centering, Edge, Normalization
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


def analyze_field():
    global fa, tmp_cropped_path

    if not file_path:
        message_console("Selecione um arquivo primeiro.")
        return

    # optional auto-crop
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

    fa = FieldProfileAnalysis(path_for_analysis)
    try:
        fa.analyze(
            x_width=xw, y_width=yw,
            normalization=Normalization.BEAM_CENTER,
            centering=Centering.BEAM_CENTER,   # robust for small fields
            edge_type=Edge.INFLECTION_DERIVATIVE,
            invert=True,                       # set True only if beam is dark overall
            ground=True,
            metrics=(
                SymmetryPointDifferenceMetric(),
                FlatnessDifferenceMetric(),
                PenumbraLeftMetric(),
                PenumbraRightMetric(),
                CAXToLeftEdgeMetric(),
                CAXToRightEdgeMetric(),
            ),
        )
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Erro na análise", str(e))
        message_console("Falha na análise.")
        return

    print(fa.results())
    fa.plot_analyzed_images(show_grid=True, mirror="beam")
    message_console("Análise concluída!")


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

frm_select = tk.LabelFrame(master=frm_left, text="Diretório", font="VERDANA")
frm_select.grid(row=0, column=0, padx=10, pady=5)

tk.Button(frm_select, text="Selecionar arquivo", font="VERDANA",
          command=open_files_path).grid(row=0, column=0, columnspan=2, padx=10, pady=5)

# Auto-crop controls
frm_crop = tk.LabelFrame(master=frm_left, text="Auto-crop", font="VERDANA")
frm_crop.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

var_autocrop = tk.BooleanVar(value=True)
tk.Checkbutton(frm_crop, text="Ativar auto-crop ao redor do feixe", variable=var_autocrop).grid(row=0, column=0, sticky="w", padx=8, pady=4)

tk.Label(frm_crop, text="Tamanho da caixa (px):").grid(row=1, column=0, sticky="w", padx=8)
entry_box_px = tk.Entry(frm_crop, width=8)
entry_box_px.insert(0, "300")
entry_box_px.grid(row=1, column=1, sticky="w", padx=4)

tk.Button(frm_select, text="Mostrar histograma", font="VERDANA",
          command=show_histogram).grid(row=2, column=0, columnspan=2, padx=10, pady=5)

frm_console = tk.LabelFrame(master=window, width=800, height=50, text="Console")
frm_console.grid(row=2, column=0, columnspan=3, sticky="nw", padx=5, pady=20)

window.mainloop()

# (Optional) clean temp file on exit if you want:
# if tmp_cropped_path and os.path.exists(tmp_cropped_path):
#     os.remove(tmp_cropped_path)
