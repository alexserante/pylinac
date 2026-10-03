"""
STARSHOT ANALYZER
=================

Interface Tkinter para análise de Starshot usando o pylinac como engine.

O pylinac faz TODA a análise (detecção das linhas, ajuste, círculo de wobble,
PASS/FAIL). Esta aplicação cuida apenas de: entrada de imagens, configuração de
parâmetros, visualização, apresentação de resultados e exportação.

Dependências: pylinac, matplotlib, numpy (tkinter vem com o Python no Windows).
Compatível com pylinac 3.x — os parâmetros do analyze() são descobertos em tempo
de execução, de modo que parâmetros que não existem na versão instalada
simplesmente não aparecem na interface.
"""

from __future__ import annotations

import csv
import inspect
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import (  # noqa: E402
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)
from matplotlib.figure import Figure  # noqa: E402

import pylinac  # noqa: E402
from pylinac import Starshot  # noqa: E402


# --------------------------------------------------------------------------- #
#                                CONSTANTES                                    #
# --------------------------------------------------------------------------- #
IMAGE_FILETYPES = [
    ("Imagens de Starshot", "*.dcm *.tif *.tiff *.png *.jpg *.jpeg"),
    ("DICOM", "*.dcm"),
    ("TIFF", "*.tif *.tiff"),
    ("PNG/JPEG", "*.png *.jpg *.jpeg"),
    ("Todos os arquivos", "*.*"),
]
ZIP_FILETYPES = [("Arquivo ZIP", "*.zip"), ("Todos os arquivos", "*.*")]

TEST_TYPES = [
    "Gantry Starshot",
    "Collimator Starshot",
    "Couch Starshot",
    "MLC Starshot",
    "Other",
]

# Parâmetros do analyze() que a GUI sabe exibir. Só são mostrados os que
# existirem na assinatura da versão instalada do pylinac.
PARAM_SPECS: list[dict[str, Any]] = [
    {
        "key": "tolerance",
        "label": "Tolerance",
        "unit": "mm",
        "kind": "float",
        "tip": "Critério PASS/FAIL. O teste passa se o diâmetro do círculo de "
               "wobble for menor que esta tolerância.",
    },
    {
        "key": "radius",
        "label": "Radius",
        "unit": "fração",
        "kind": "float",
        "tip": "Posição radial relativa (fração da distância entre o ponto "
               "inicial e a borda mais próxima da imagem) onde é extraído o "
               "perfil circular que detecta as linhas de radiação.",
    },
    {
        "key": "min_peak_height",
        "label": "Min peak height",
        "unit": "fração",
        "kind": "float",
        "tip": "Altura mínima relativa para um pico do perfil circular ser "
               "considerado um spoke. Valores menores detectam spokes fracos "
               "(ex.: gantry), mas podem detectar ruído. Ajuste este valor "
               "quando a detecção automática das linhas falhar.",
    },
    {
        "key": "max_wobble_diameter",
        "label": "Max wobble diameter",
        "unit": "mm",
        "kind": "float",
        "tip": "Diâmetro máximo de wobble considerado 'razoável' pelo pylinac. "
               "Usado apenas durante a busca recursiva; não é o critério "
               "PASS/FAIL. Só existe em versões recentes do pylinac.",
    },
    {
        "key": "fwhm",
        "label": "FWHM",
        "unit": "",
        "kind": "bool",
        "tip": "Se marcado, o centro de cada spoke é o centro da FWHM do perfil "
               "da linha de radiação. Se desmarcado, é usada a posição do valor "
               "máximo.",
    },
    {
        "key": "recursive",
        "label": "Recursive (recomendado)",
        "unit": "",
        "kind": "bool",
        "tip": "Se marcado, o pylinac ajusta internamente min_peak_height e "
               "radius até encontrar um wobble razoável. É a configuração "
               "recomendada pela documentação do pylinac.",
    },
    {
        "key": "invert",
        "label": "Invert image",
        "unit": "",
        "kind": "bool",
        "tip": "Força a inversão dos valores da imagem. Use quando a detecção "
               "automática de polaridade estiver errada (picos caindo nos vales "
               "da imagem).",
    },
]

# Usado apenas se a introspecção da assinatura falhar (ex.: método decorado
# sem functools.wraps).
FALLBACK_DEFAULTS = {
    "radius": 0.85,
    "min_peak_height": 0.25,
    "tolerance": 1.0,
    "fwhm": True,
    "recursive": True,
    "invert": False,
}


# --------------------------------------------------------------------------- #
#                      CAMADA DE ANÁLISE (sem dependência de GUI)              #
# --------------------------------------------------------------------------- #
def analyze_defaults() -> dict[str, Any]:
    """Defaults reais de ``Starshot.analyze`` na versão instalada do pylinac."""
    try:
        params = inspect.signature(Starshot.analyze).parameters
        defaults = {
            name: p.default
            for name, p in params.items()
            if name != "self" and p.default is not inspect.Parameter.empty
        }
        if defaults:
            return defaults
    except (TypeError, ValueError):
        pass
    return dict(FALLBACK_DEFAULTS)


def create_starshot_instance(source: dict[str, Any]) -> Starshot:
    """Instancia um Starshot a partir da descrição da fonte de imagem.

    ``source`` tem as chaves: ``kind`` ('single' | 'multiple' | 'zip' | 'demo'),
    ``paths`` (lista de Path) e ``load_kwargs`` (dpi/sid quando informados).
    Uma instância NOVA é criada a cada análise porque analyze() modifica a
    imagem em memória (ground, inversão), o que contaminaria reanálises.
    """
    kind = source["kind"]
    kwargs = dict(source.get("load_kwargs", {}))

    if kind == "demo":
        return Starshot.from_demo_image()
    if kind == "zip":
        return Starshot.from_zip(str(source["paths"][0]), **kwargs)
    if kind == "multiple":
        return Starshot.from_multiple_images([str(p) for p in source["paths"]], **kwargs)
    return Starshot(str(source["paths"][0]), **kwargs)


def run_starshot_analysis(star: Starshot, params: dict[str, Any]) -> None:
    """Executa a análise do pylinac. Nenhum cálculo próprio é feito aqui."""
    star.analyze(**params)


def extract_starshot_results(star: Starshot) -> dict[str, Any]:
    """Extrai os resultados pela API pública (results_data), não por parsing.

    Campos ausentes em versões antigas do pylinac (p.ex. ``angles``) retornam
    None em vez de serem recalculados por conta própria.
    """
    data = star.results_data(as_dict=True)
    results: dict[str, Any] = {
        "passed": data.get("passed"),
        "tolerance_mm": data.get("tolerance_mm"),
        "circle_diameter_mm": data.get("circle_diameter_mm"),
        "circle_radius_mm": data.get("circle_radius_mm"),
        "circle_center_x_y": data.get("circle_center_x_y"),
        "angles": data.get("angles"),  # só existe em versões recentes
        "num_lines": None,
        "num_peaks": None,
        "results_text": star.results(),
    }
    # Atributos públicos documentados da classe Starshot
    try:
        results["num_lines"] = len(star.lines)
    except (AttributeError, TypeError):
        pass
    try:
        results["num_peaks"] = len(star.circle_profile.peaks)
    except (AttributeError, TypeError):
        pass
    return results


# --------------------------------------------------------------------------- #
#                                  TOOLTIP                                     #
# --------------------------------------------------------------------------- #
class Tooltip:
    """Tooltip simples para widgets ttk."""

    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 400):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id: str | None = None
        self._window: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self) -> None:
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        if self._window is not None:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self._window = tk.Toplevel(self.widget)
        self._window.wm_overrideredirect(True)
        self._window.wm_geometry(f"+{x}+{y}")
        tk.Label(self._window, text=self.text, justify="left", background="#ffffe0",
                 relief="solid", borderwidth=1, wraplength=320,
                 font=("Segoe UI", 8)).pack(ipadx=4, ipady=2)

    def _hide(self, _event=None) -> None:
        self._cancel()
        if self._window is not None:
            self._window.destroy()
            self._window = None


# --------------------------------------------------------------------------- #
#                                APLICAÇÃO                                     #
# --------------------------------------------------------------------------- #
class StarshotAnalyzerApp:
    """GUI de análise de Starshot com o pylinac como engine."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Starshot Analyzer - pylinac")
        self.root.geometry("1250x820")
        self.root.minsize(1050, 700)

        self.defaults = analyze_defaults()
        self.source: dict[str, Any] | None = None   # fonte de imagem atual
        self.preview_star: Starshot | None = None   # instância só para exibir/infos
        self.star: Starshot | None = None           # instância analisada
        self.results: dict[str, Any] | None = None
        self.used_params: dict[str, Any] | None = None
        self.start_marker = None

        self.param_vars: dict[str, tk.Variable] = {}
        self.header_vars: dict[str, tk.Variable] = {}

        self.create_widgets()
        self.reset_parameters()
        self.set_status("Ready")
        self.log(f"pylinac {pylinac.__version__} carregado.")

    # ------------------------------------------------------------------ #
    #                              WIDGETS                                #
    # ------------------------------------------------------------------ #
    def create_widgets(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        left = ttk.Frame(self.root)
        left.grid(row=0, column=0, sticky="ns", padx=(8, 4), pady=8)
        left.columnconfigure(0, weight=1)

        self._build_file_section(left)
        self._build_calibration_section(left)
        self._build_parameters_section(left)
        self._build_start_point_section(left)
        self._build_header_section(left)

        self.btn_analyze = ttk.Button(left, text="ANALYZE", command=self.analyze)
        self.btn_analyze.grid(row=90, column=0, sticky="ew", pady=(8, 2))

        right = ttk.Frame(self.root)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self._build_notebook(right)
        self._build_results_section(right)

        self._build_statusbar()

    def _build_file_section(self, parent: ttk.Frame) -> None:
        frm = ttk.LabelFrame(parent, text="Imagem")
        frm.grid(row=0, column=0, sticky="ew", pady=3)
        ttk.Button(frm, text="Load Starshot", command=self.load_image).grid(
            row=0, column=0, sticky="ew", padx=4, pady=2)
        ttk.Button(frm, text="Load Multiple Images", command=self.load_multiple_images).grid(
            row=1, column=0, sticky="ew", padx=4, pady=2)
        ttk.Button(frm, text="Load ZIP", command=self.load_zip).grid(
            row=2, column=0, sticky="ew", padx=4, pady=2)
        ttk.Button(frm, text="Load pylinac Demo", command=self.load_demo).grid(
            row=3, column=0, sticky="ew", padx=4, pady=(2, 4))

        self.lbl_image_info = ttk.Label(frm, text="Nenhuma imagem carregada.",
                                        justify="left", foreground="gray",
                                        wraplength=250)
        self.lbl_image_info.grid(row=4, column=0, sticky="w", padx=4, pady=(0, 4))

    def _build_calibration_section(self, parent: ttk.Frame) -> None:
        frm = ttk.LabelFrame(parent, text="Image Calibration")
        frm.grid(row=1, column=0, sticky="ew", pady=3)

        self.calib_mode = tk.StringVar(value="Auto / DICOM")
        cb = ttk.Combobox(frm, textvariable=self.calib_mode, state="readonly", width=16,
                          values=["Auto / DICOM", "Manual"])
        cb.grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=2)
        cb.bind("<<ComboboxSelected>>", lambda _e: self._toggle_calibration())

        ttk.Label(frm, text="DPI").grid(row=1, column=0, sticky="w", padx=4)
        self.var_dpi = tk.StringVar()
        self.ent_dpi = ttk.Entry(frm, textvariable=self.var_dpi, width=10)
        self.ent_dpi.grid(row=1, column=1, sticky="w", padx=4, pady=2)
        Tooltip(self.ent_dpi, "Resolução da imagem em pontos por polegada. "
                              "Necessária para filmes digitalizados (TIFF/PNG/JPG); "
                              "em DICOM de EPID vem do cabeçalho.")

        ttk.Label(frm, text="SID (mm)").grid(row=2, column=0, sticky="w", padx=4)
        self.var_sid = tk.StringVar()
        self.ent_sid = ttk.Entry(frm, textvariable=self.var_sid, width=10)
        self.ent_sid.grid(row=2, column=1, sticky="w", padx=4, pady=(2, 4))
        Tooltip(self.ent_sid, "Distância fonte-imagem em mm no momento da "
                              "irradiação. O pylinac a usa para escalar os "
                              "resultados ao plano do isocentro.")
        self._toggle_calibration()

    def _build_parameters_section(self, parent: ttk.Frame) -> None:
        frm = ttk.LabelFrame(parent, text="Analysis Parameters")
        frm.grid(row=2, column=0, sticky="ew", pady=3)

        ttk.Label(frm, text="Preset").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        self.var_preset = tk.StringVar(value="Default pylinac")
        cb = ttk.Combobox(frm, textvariable=self.var_preset, state="readonly", width=16,
                          values=["Default pylinac", "Custom"])
        cb.grid(row=0, column=1, columnspan=2, sticky="w", padx=4, pady=2)
        cb.bind("<<ComboboxSelected>>", lambda _e: self._apply_preset())

        row = 1
        for spec in PARAM_SPECS:
            key = spec["key"]
            if key not in self.defaults:          # não existe nesta versão
                continue
            default = self.defaults[key]
            if spec["kind"] == "bool":
                var = tk.BooleanVar(value=bool(default))
                widget = ttk.Checkbutton(frm, text=spec["label"], variable=var,
                                         command=lambda: self.var_preset.set("Custom"))
                widget.grid(row=row, column=0, columnspan=3, sticky="w", padx=4, pady=2)
            else:
                ttk.Label(frm, text=spec["label"]).grid(row=row, column=0, sticky="w",
                                                        padx=4, pady=2)
                var = tk.StringVar(value=str(default))
                widget = ttk.Spinbox(frm, textvariable=var, width=8, increment=0.05,
                                     from_=0.0, to=1000.0,
                                     command=lambda: self.var_preset.set("Custom"))
                widget.grid(row=row, column=1, sticky="w", padx=4, pady=2)
                if spec["unit"]:
                    ttk.Label(frm, text=spec["unit"], foreground="gray").grid(
                        row=row, column=2, sticky="w")
            Tooltip(widget, spec["tip"])
            self.param_vars[key] = var
            row += 1

        ttk.Button(frm, text="Reset parameters", command=self.reset_parameters).grid(
            row=row, column=0, columnspan=3, sticky="ew", padx=4, pady=(4, 4))

    def _build_start_point_section(self, parent: ttk.Frame) -> None:
        frm = ttk.LabelFrame(parent, text="Start Point")
        frm.grid(row=3, column=0, sticky="ew", pady=3)

        self.var_manual_start = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(frm, text="Definir centro inicial manualmente",
                              variable=self.var_manual_start,
                              command=self._toggle_start_point)
        chk.grid(row=0, column=0, columnspan=4, sticky="w", padx=4, pady=2)
        Tooltip(chk, "Se desmarcado, start_point=None e o pylinac procura "
                     "automaticamente um ponto inicial razoável no terço "
                     "central da imagem.")

        ttk.Label(frm, text="X").grid(row=1, column=0, sticky="e", padx=(4, 0))
        self.var_start_x = tk.StringVar()
        self.ent_start_x = ttk.Entry(frm, textvariable=self.var_start_x, width=7)
        self.ent_start_x.grid(row=1, column=1, sticky="w", padx=2)
        ttk.Label(frm, text="Y").grid(row=1, column=2, sticky="e")
        self.var_start_y = tk.StringVar()
        self.ent_start_y = ttk.Entry(frm, textvariable=self.var_start_y, width=7)
        self.ent_start_y.grid(row=1, column=3, sticky="w", padx=2)
        ttk.Label(frm, text="pixels", foreground="gray").grid(
            row=2, column=0, columnspan=4, sticky="w", padx=4)

        self.var_pick_mode = tk.BooleanVar(value=False)
        self.chk_pick = ttk.Checkbutton(frm, text="Selecionar centro na imagem",
                                        variable=self.var_pick_mode,
                                        command=self._toggle_pick_mode)
        self.chk_pick.grid(row=3, column=0, columnspan=4, sticky="w", padx=4, pady=2)
        Tooltip(self.chk_pick, "Com esta opção ativa, clique na aba 'Original "
                               "Image' para definir o ponto inicial.")

        ttk.Button(frm, text="Restaurar centro automático",
                   command=self.reset_start_point).grid(
            row=4, column=0, columnspan=4, sticky="ew", padx=4, pady=(2, 4))
        self._toggle_start_point()

    def _build_header_section(self, parent: ttk.Frame) -> None:
        frm = ttk.LabelFrame(parent, text="Cabeçalho clínico (opcional)")
        frm.grid(row=4, column=0, sticky="ew", pady=3)

        fields = [("machine", "Machine"), ("physicist", "Physicist"), ("date", "Date")]
        for i, (key, label) in enumerate(fields):
            ttk.Label(frm, text=label).grid(row=i, column=0, sticky="w", padx=4, pady=1)
            var = tk.StringVar()
            ttk.Entry(frm, textvariable=var, width=20).grid(row=i, column=1, sticky="w",
                                                            padx=4, pady=1)
            self.header_vars[key] = var
        self.header_vars["date"].set(datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(frm, text="Test type").grid(row=3, column=0, sticky="w", padx=4, pady=1)
        self.header_vars["test_type"] = tk.StringVar(value=TEST_TYPES[0])
        ttk.Combobox(frm, textvariable=self.header_vars["test_type"], state="readonly",
                     width=18, values=TEST_TYPES).grid(row=3, column=1, sticky="w",
                                                       padx=4, pady=1)

        ttk.Label(frm, text="Comments").grid(row=4, column=0, sticky="nw", padx=4, pady=1)
        self.txt_comments = tk.Text(frm, width=22, height=3, font=("Segoe UI", 8))
        self.txt_comments.grid(row=4, column=1, sticky="w", padx=4, pady=(1, 4))

    def _build_notebook(self, parent: ttk.Frame) -> None:
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # --- aba Original ---
        tab_orig = ttk.Frame(self.notebook)
        self.notebook.add(tab_orig, text="Original Image")
        tab_orig.rowconfigure(0, weight=1)
        tab_orig.columnconfigure(0, weight=1)
        self.fig_orig = Figure(figsize=(6, 5), layout="tight")
        self.ax_orig = self.fig_orig.add_subplot(111)
        self.ax_orig.axis("off")
        self.canvas_orig = FigureCanvasTkAgg(self.fig_orig, master=tab_orig)
        self.canvas_orig.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        toolbar_frame = ttk.Frame(tab_orig)
        toolbar_frame.grid(row=1, column=0, sticky="ew")
        NavigationToolbar2Tk(self.canvas_orig, toolbar_frame)
        self.canvas_orig.mpl_connect("button_press_event", self.on_image_click)

        # --- aba Analisada ---
        tab_analyzed = ttk.Frame(self.notebook)
        self.notebook.add(tab_analyzed, text="Analyzed Image")
        tab_analyzed.rowconfigure(0, weight=1)
        tab_analyzed.columnconfigure(0, weight=1)
        self.fig_analyzed = Figure(figsize=(9, 5), layout="tight")
        self.canvas_analyzed = FigureCanvasTkAgg(self.fig_analyzed, master=tab_analyzed)
        self.canvas_analyzed.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        toolbar_frame2 = ttk.Frame(tab_analyzed)
        toolbar_frame2.grid(row=1, column=0, sticky="ew")
        NavigationToolbar2Tk(self.canvas_analyzed, toolbar_frame2)

        # --- aba Log ---
        tab_log = ttk.Frame(self.notebook)
        self.notebook.add(tab_log, text="Log")
        tab_log.rowconfigure(0, weight=1)
        tab_log.columnconfigure(0, weight=1)
        self.txt_log = ScrolledText(tab_log, state="disabled", font=("Consolas", 9))
        self.txt_log.grid(row=0, column=0, sticky="nsew")

    def _build_results_section(self, parent: ttk.Frame) -> None:
        frm = ttk.LabelFrame(parent, text="Results")
        frm.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        frm.columnconfigure(1, weight=1)

        self.lbl_passfail = tk.Label(frm, text="—", font=("Segoe UI", 20, "bold"),
                                     width=6, background="#e0e0e0")
        self.lbl_passfail.grid(row=0, column=0, rowspan=2, padx=8, pady=6)

        self.txt_results = tk.Text(frm, height=7, width=60, state="disabled",
                                   font=("Consolas", 9))
        self.txt_results.grid(row=0, column=1, rowspan=2, sticky="ew", padx=4, pady=4)

        btns = ttk.Frame(frm)
        btns.grid(row=0, column=2, rowspan=2, padx=4)
        ttk.Button(btns, text="Save Figure", command=self.save_figure).grid(
            row=0, column=0, sticky="ew", pady=1)
        ttk.Button(btns, text="Export PDF", command=self.export_pdf).grid(
            row=1, column=0, sticky="ew", pady=1)
        ttk.Button(btns, text="Export CSV", command=self.export_results).grid(
            row=2, column=0, sticky="ew", pady=1)
        ttk.Button(btns, text="Copy angles", command=self.copy_angles).grid(
            row=3, column=0, sticky="ew", pady=1)

    def _build_statusbar(self) -> None:
        bar = ttk.Frame(self.root)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.columnconfigure(0, weight=1)
        self.var_status = tk.StringVar(value="Ready")
        ttk.Label(bar, textvariable=self.var_status, relief="sunken",
                  anchor="w").grid(row=0, column=0, sticky="ew")
        ttk.Label(bar, text=f"pylinac {pylinac.__version__}", relief="sunken",
                  anchor="e", foreground="gray").grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------ #
    #                            AUXILIARES                               #
    # ------------------------------------------------------------------ #
    def set_status(self, text: str) -> None:
        self.var_status.set(text)

    def log(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f"[{stamp}] {text}\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _toggle_calibration(self) -> None:
        state = "normal" if self.calib_mode.get() == "Manual" else "disabled"
        self.ent_dpi.configure(state=state)
        self.ent_sid.configure(state=state)

    def _toggle_start_point(self) -> None:
        state = "normal" if self.var_manual_start.get() else "disabled"
        self.ent_start_x.configure(state=state)
        self.ent_start_y.configure(state=state)
        self.chk_pick.configure(state=state)
        if not self.var_manual_start.get():
            self.var_pick_mode.set(False)

    def _toggle_pick_mode(self) -> None:
        if self.var_pick_mode.get():
            self.notebook.select(0)
            self.set_status("Clique na imagem para definir o start point.")

    def _apply_preset(self) -> None:
        if self.var_preset.get() == "Default pylinac":
            self.reset_parameters(keep_preset=True)

    def reset_parameters(self, keep_preset: bool = False) -> None:
        """Preenche os campos com os defaults reais da versão do pylinac."""
        for key, var in self.param_vars.items():
            default = self.defaults[key]
            var.set(bool(default) if isinstance(var, tk.BooleanVar) else str(default))
        if not keep_preset:
            self.var_preset.set("Default pylinac")
        self.log("Parâmetros restaurados para os defaults do pylinac.")

    def reset_start_point(self) -> None:
        self.var_manual_start.set(False)
        self.var_pick_mode.set(False)
        self.var_start_x.set("")
        self.var_start_y.set("")
        self._toggle_start_point()
        self._draw_start_marker(None)
        self.set_status("Start point automático (start_point=None).")

    # ------------------------------------------------------------------ #
    #                         CARREGAMENTO DE IMAGEM                      #
    # ------------------------------------------------------------------ #
    def _load_kwargs(self) -> dict[str, float]:
        """dpi/sid manuais; só são passados quando o usuário os informa."""
        if self.calib_mode.get() != "Manual":
            return {}
        kwargs: dict[str, float] = {}
        for key, var, label in (("dpi", self.var_dpi, "DPI"), ("sid", self.var_sid, "SID")):
            raw = var.get().strip().replace(",", ".")
            if raw:
                try:
                    kwargs[key] = float(raw)
                except ValueError:
                    raise ValueError(f"O campo {label} precisa ser numérico.")
        return kwargs

    def load_image(self) -> None:
        path = filedialog.askopenfilename(title="Selecione a imagem de Starshot",
                                          filetypes=IMAGE_FILETYPES)
        if path:
            self._set_source({"kind": "single", "paths": [Path(path)]})

    def load_multiple_images(self) -> None:
        paths = filedialog.askopenfilenames(title="Selecione as imagens (serão superpostas)",
                                            filetypes=IMAGE_FILETYPES)
        if not paths:
            return
        if len(paths) == 1:
            self._set_source({"kind": "single", "paths": [Path(paths[0])]})
        else:
            self._set_source({"kind": "multiple", "paths": [Path(p) for p in paths]})

    def load_zip(self) -> None:
        path = filedialog.askopenfilename(title="Selecione o ZIP com as imagens",
                                          filetypes=ZIP_FILETYPES)
        if path:
            self._set_source({"kind": "zip", "paths": [Path(path)]})

    def load_demo(self) -> None:
        self._set_source({"kind": "demo", "paths": []})

    def _set_source(self, source: dict[str, Any]) -> None:
        """Carrega a fonte, monta uma instância de preview e mostra a imagem."""
        try:
            source["load_kwargs"] = self._load_kwargs()
        except ValueError as e:
            messagebox.showerror("Calibração inválida", str(e))
            return

        self.set_status("Loading image...")
        self.root.update_idletasks()
        try:
            preview = create_starshot_instance(source)
        except ValueError as e:
            self.set_status("Ready")
            self._handle_scale_error(e)
            return
        except Exception as e:  # arquivo corrompido, formato não suportado etc.
            self.set_status("Ready")
            self.log(f"ERRO ao carregar: {type(e).__name__}: {e}")
            messagebox.showerror("Erro ao carregar a imagem",
                                 f"{type(e).__name__}: {e}")
            return

        self.source = source
        self.preview_star = preview
        self.star = None
        self.results = None
        self._clear_results()
        self.display_original_image()
        self._update_image_info()
        self.log(f"Imagem carregada ({source['kind']}): "
                 f"{', '.join(p.name for p in source['paths']) or 'demo'}")
        self.set_status("Image loaded")

    def _handle_scale_error(self, error: Exception) -> None:
        msg = str(error)
        if "DPI" in msg or "Source-to-Image" in msg or "sid" in msg.lower():
            self.log(f"ERRO de escala: {msg}")
            messagebox.showerror(
                "Calibração espacial ausente",
                "A imagem não contém informação de escala espacial suficiente.\n\n"
                "Informe DPI/SID manualmente em 'Image Calibration' ou use uma "
                "imagem DICOM calibrada.\n\nMensagem do pylinac:\n" + msg)
        else:
            self.log(f"ERRO: {msg}")
            messagebox.showerror("Erro", msg)

    def _update_image_info(self) -> None:
        star = self.preview_star
        if star is None:
            self.lbl_image_info.configure(text="Nenhuma imagem carregada.")
            return
        src = self.source or {}
        names = ", ".join(p.name for p in src.get("paths", [])) or "demo image"
        img = star.image
        info = [
            f"Arquivo: {names}",
            f"Tipo: {type(img).__name__}",
            f"Dimensão: {img.array.shape[1]} x {img.array.shape[0]} px",
            f"Nº de imagens: {max(len(src.get('paths', [])), 1)}",
        ]
        for label, attr in (("DPI", "dpi"), ("dpmm", "dpmm"), ("SID", "sid")):
            try:  # algumas propriedades levantam exceção quando a tag falta
                value = getattr(img, attr, None)
            except Exception:  # noqa: BLE001
                value = None
            if value is not None:
                info.append(f"{label}: {value:.3f}" if isinstance(value, float)
                            else f"{label}: {value}")
        self.lbl_image_info.configure(text="\n".join(info), foreground="black")

    # ------------------------------------------------------------------ #
    #                            VISUALIZAÇÃO                             #
    # ------------------------------------------------------------------ #
    def display_original_image(self) -> None:
        """Mostra a imagem carregada, sem overlays, na aba Original."""
        if self.preview_star is None:
            return
        self.ax_orig.clear()
        self.ax_orig.imshow(self.preview_star.image.array, cmap="gray")
        self.ax_orig.set_title("Imagem original (clique define o start point)",
                               fontsize=9)
        self.ax_orig.axis("off")
        self.start_marker = None
        self.canvas_orig.draw_idle()
        self.notebook.select(0)

    def on_image_click(self, event) -> None:
        """Captura o clique para definir o start_point em pixels."""
        if not self.var_pick_mode.get() or event.inaxes is not self.ax_orig:
            return
        if event.xdata is None or event.ydata is None:
            return
        x, y = int(round(event.xdata)), int(round(event.ydata))
        self.var_manual_start.set(True)
        self.var_start_x.set(str(x))
        self.var_start_y.set(str(y))
        self._toggle_start_point()
        self._draw_start_marker((x, y))
        self.set_status(f"Start point manual: ({x}, {y})")
        self.log(f"Start point selecionado na imagem: ({x}, {y})")

    def _draw_start_marker(self, point: tuple[int, int] | None) -> None:
        if self.start_marker is not None:
            try:
                self.start_marker.remove()
            except (ValueError, AttributeError):
                pass
            self.start_marker = None
        if point is not None:
            self.start_marker, = self.ax_orig.plot(point[0], point[1], "r+",
                                                   markersize=14, markeredgewidth=2)
        self.canvas_orig.draw_idle()

    def display_analysis(self) -> None:
        """Desenha as figuras do pylinac dentro da GUI (sem janela externa)."""
        if self.star is None:
            return
        self.fig_analyzed.clear()
        ax_whole = self.fig_analyzed.add_subplot(121)
        ax_wobble = self.fig_analyzed.add_subplot(122)
        # plot_analyzed_subimage aceita 'ax' e é API pública: nada é redesenhado
        # manualmente, o pylinac é quem desenha linhas, círculo e wobble.
        self.star.plot_analyzed_subimage(subimage="whole", ax=ax_whole, show=False)
        ax_whole.set_title("Analyzed Image", fontsize=9)
        self.star.plot_analyzed_subimage(subimage="wobble", ax=ax_wobble, show=False)
        ax_wobble.set_title("Wobble Circle", fontsize=9)
        self.canvas_analyzed.draw_idle()
        self.notebook.select(1)

    # ------------------------------------------------------------------ #
    #                              ANÁLISE                                #
    # ------------------------------------------------------------------ #
    def validate_parameters(self) -> dict[str, Any]:
        """Valida os campos e devolve os kwargs do analyze()."""
        params: dict[str, Any] = {}
        for spec in PARAM_SPECS:
            key = spec["key"]
            if key not in self.param_vars:
                continue
            var = self.param_vars[key]
            if spec["kind"] == "bool":
                params[key] = bool(var.get())
                continue
            raw = str(var.get()).strip().replace(",", ".")
            try:
                value = float(raw)
            except ValueError:
                raise ValueError(f"'{spec['label']}' precisa ser numérico (valor: '{raw}').")
            params[key] = value

        if params.get("tolerance", 1) <= 0:
            raise ValueError("Tolerance deve ser maior que zero.")
        if "radius" in params and not 0.05 <= params["radius"] <= 0.95:
            raise ValueError("Radius deve estar entre 0.05 e 0.95.")
        if "min_peak_height" in params and not 0.05 <= params["min_peak_height"] <= 0.95:
            raise ValueError("Min peak height deve estar entre 0.05 e 0.95.")
        if "max_wobble_diameter" in params and params["max_wobble_diameter"] <= 0:
            raise ValueError("Max wobble diameter deve ser maior que zero.")

        if self.var_manual_start.get():
            try:
                x = int(float(self.var_start_x.get().strip().replace(",", ".")))
                y = int(float(self.var_start_y.get().strip().replace(",", ".")))
            except ValueError:
                raise ValueError("Start point: X e Y precisam ser numéricos.")
            if self.preview_star is not None:
                rows, cols = self.preview_star.image.array.shape[:2]
                if not (0 <= x < cols and 0 <= y < rows):
                    raise ValueError(f"Start point fora da imagem (0-{cols-1}, 0-{rows-1}).")
            params["start_point"] = (x, y)
        else:
            params["start_point"] = None
        return params

    def analyze(self) -> None:
        if self.source is None:
            messagebox.showwarning("Starshot",
                                   "Carregue uma imagem de Starshot antes de analisar.")
            return
        try:
            params = self.validate_parameters()
            source = dict(self.source)
            source["load_kwargs"] = self._load_kwargs()
        except ValueError as e:
            messagebox.showerror("Parâmetro inválido", str(e))
            return

        self.used_params = params
        self.btn_analyze.state(["disabled"])
        self.set_status("Analyzing Starshot...")
        self.log("analyze(" + ", ".join(f"{k}={v}" for k, v in params.items()) + ")")

        # A análise roda em thread separada; widgets só são tocados na thread
        # principal, via root.after().
        threading.Thread(target=self._analysis_worker, args=(source, params),
                         daemon=True).start()

    def _analysis_worker(self, source: dict[str, Any], params: dict[str, Any]) -> None:
        try:
            # Instância NOVA a cada análise: analyze() altera a imagem
            # (ground/inversão) e reaproveitar o objeto contamina a reanálise.
            star = create_starshot_instance(source)
            run_starshot_analysis(star, params)
        except Exception as e:  # noqa: BLE001 - erro é mostrado ao usuário
            details = traceback.format_exc()
            self.root.after(0, self._on_analysis_error, e, details)
        else:
            self.root.after(0, self._on_analysis_done, star)

    def _on_analysis_done(self, star: Starshot) -> None:
        self.star = star
        self.btn_analyze.state(["!disabled"])
        try:
            self.results = extract_starshot_results(star)
            self.update_results()
            self.display_analysis()
        except Exception as e:  # noqa: BLE001
            self.log(f"ERRO ao apresentar resultados: {type(e).__name__}: {e}")
            messagebox.showerror("Erro", f"{type(e).__name__}: {e}")
            self.set_status("Analysis failed")
            return
        self.set_status("Analysis completed")
        self.log("Análise concluída: " +
                 f"{self.results['circle_diameter_mm']:.3f} mm "
                 f"({'PASS' if self.results['passed'] else 'FAIL'})")

    def _on_analysis_error(self, error: Exception, details: str) -> None:
        self.star = None
        self.results = None
        self.btn_analyze.state(["!disabled"])
        self.set_status("Analysis failed")
        self._clear_results()
        self.log(f"ERRO: {type(error).__name__}: {error}")
        self.log(details.strip())

        if isinstance(error, ValueError) and (
                "DPI" in str(error) or "Source-to-Image" in str(error)):
            self._handle_scale_error(error)
            return

        msg = ("A análise de Starshot falhou.\n\n"
               "Tente:\n"
               "• habilitar Recursive Search\n"
               "• diminuir o Minimum Peak Height\n"
               "• ajustar o Radius\n"
               "• verificar a inversão da imagem\n"
               "• selecionar o centro aproximado da estrela manualmente\n\n"
               "Detalhes técnicos (veja também a aba Log):\n"
               f"{type(error).__name__}: {error}")
        messagebox.showerror("Analysis failed", msg)

    # ------------------------------------------------------------------ #
    #                             RESULTADOS                              #
    # ------------------------------------------------------------------ #
    def _clear_results(self) -> None:
        self.lbl_passfail.configure(text="—", background="#e0e0e0", foreground="black")
        self.txt_results.configure(state="normal")
        self.txt_results.delete("1.0", "end")
        self.txt_results.configure(state="disabled")
        self.fig_analyzed.clear()
        self.canvas_analyzed.draw_idle()

    def update_results(self) -> None:
        r = self.results
        if r is None:
            return
        passed = bool(r["passed"])
        self.lbl_passfail.configure(text="PASS" if passed else "FAIL",
                                    background="#2e7d32" if passed else "#c62828",
                                    foreground="white")

        cx, cy = r["circle_center_x_y"]
        lines = [
            f"Wobble diameter : {r['circle_diameter_mm']:.3f} mm",
            f"Wobble radius   : {r['circle_radius_mm']:.3f} mm",
            f"Tolerance       : {r['tolerance_mm']:.3f} mm",
            f"Wobble center   : X = {cx:.1f} px | Y = {cy:.1f} px",
        ]
        if r["num_lines"] is not None:
            lines.append(f"Radiation lines : {r['num_lines']}"
                         + (f"  (spokes/picos detectados: {r['num_peaks']})"
                            if r["num_peaks"] is not None else ""))
        if r["angles"]:
            lines.append("Angles (deg)    : " +
                         ", ".join(f"{a:.1f}" for a in r["angles"]))
        else:
            lines.append("Angles (deg)    : não disponíveis nesta versão do pylinac")

        self.txt_results.configure(state="normal")
        self.txt_results.delete("1.0", "end")
        self.txt_results.insert("1.0", "\n".join(lines))
        self.txt_results.configure(state="disabled")

    def copy_angles(self) -> None:
        if not self.results or not self.results.get("angles"):
            messagebox.showinfo("Angles",
                                "Os ângulos não estão disponíveis (analise uma "
                                "imagem ou atualize o pylinac para uma versão "
                                "que exponha 'angles' em results_data()).")
            return
        text = "\n".join(f"{a:.2f}" for a in self.results["angles"])
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.set_status("Ângulos copiados para a área de transferência.")

    # ------------------------------------------------------------------ #
    #                             EXPORTAÇÃO                              #
    # ------------------------------------------------------------------ #
    def _metadata(self) -> dict[str, str]:
        return {
            "Machine": self.header_vars["machine"].get(),
            "Test type": self.header_vars["test_type"].get(),
            "Date": self.header_vars["date"].get(),
            "Physicist": self.header_vars["physicist"].get(),
            "pylinac": pylinac.__version__,
        }

    def _source_name(self) -> str:
        if not self.source:
            return ""
        paths = self.source.get("paths", [])
        return "; ".join(p.name for p in paths) or "demo image"

    def save_figure(self) -> None:
        if self.star is None:
            messagebox.showwarning("Starshot", "Faça uma análise primeiro.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG", "*.png"),
                                                       ("PDF", "*.pdf"),
                                                       ("TIFF", "*.tif")])
        if not path:
            return
        self.fig_analyzed.savefig(path, dpi=200, bbox_inches="tight")
        self.log(f"Figura salva: {path}")
        self.set_status("Figura salva.")

    def export_pdf(self) -> None:
        if self.star is None:
            messagebox.showwarning("Starshot", "Faça uma análise primeiro.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        notes = self.txt_comments.get("1.0", "end").strip() or None
        try:
            # Relatório oficial do pylinac; nada é recriado manualmente.
            self.star.publish_pdf(path, notes=notes, metadata=self._metadata())
        except Exception as e:  # noqa: BLE001
            self.log(f"ERRO ao exportar PDF: {type(e).__name__}: {e}")
            messagebox.showerror("Export PDF", f"{type(e).__name__}: {e}")
            return
        self.log(f"PDF exportado: {path}")
        self.set_status("PDF exported")

    def export_results(self) -> None:
        if self.results is None:
            messagebox.showwarning("Starshot", "Faça uma análise primeiro.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv"),
                                                       ("Texto", "*.txt")])
        if not path:
            return

        r = self.results
        p = self.used_params or {}
        start = p.get("start_point") or (None, None)
        row = {
            "filename": self._source_name(),
            "analysis_datetime": datetime.now().isoformat(timespec="seconds"),
            "pylinac_version": pylinac.__version__,
            "machine": self.header_vars["machine"].get(),
            "test_type": self.header_vars["test_type"].get(),
            "test_date": self.header_vars["date"].get(),
            "physicist": self.header_vars["physicist"].get(),
            "comments": self.txt_comments.get("1.0", "end").strip(),
            "tolerance_mm": r["tolerance_mm"],
            "wobble_diameter_mm": r["circle_diameter_mm"],
            "wobble_radius_mm": r["circle_radius_mm"],
            "center_x": r["circle_center_x_y"][0],
            "center_y": r["circle_center_x_y"][1],
            "passed": r["passed"],
            "num_radiation_lines": r["num_lines"],
            "angles_deg": ";".join(f"{a:.2f}" for a in (r["angles"] or [])),
            "radius_parameter": p.get("radius"),
            "min_peak_height": p.get("min_peak_height"),
            "max_wobble_diameter": p.get("max_wobble_diameter"),
            "fwhm": p.get("fwhm"),
            "recursive": p.get("recursive"),
            "invert": p.get("invert"),
            "start_point_x": start[0],
            "start_point_y": start[1],
            "dpi_manual": self.var_dpi.get() if self.calib_mode.get() == "Manual" else "",
            "sid_manual": self.var_sid.get() if self.calib_mode.get() == "Manual" else "",
        }

        try:
            if path.lower().endswith(".txt"):
                Path(path).write_text(
                    "\n".join(f"{k}: {v}" for k, v in row.items()), encoding="utf-8")
            else:
                file = Path(path)
                write_header = not file.exists() or file.stat().st_size == 0
                with file.open("a", newline="", encoding="utf-8-sig") as fh:
                    writer = csv.DictWriter(fh, fieldnames=list(row))
                    if write_header:
                        writer.writeheader()
                    writer.writerow(row)
        except OSError as e:
            self.log(f"ERRO ao exportar resultados: {e}")
            messagebox.showerror("Export", str(e))
            return
        self.log(f"Resultados exportados: {path}")
        self.set_status("Results exported")


# --------------------------------------------------------------------------- #
#                                  MAIN                                        #
# --------------------------------------------------------------------------- #
def main() -> None:
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")  # Windows; cai no default em outros SOs
    except tk.TclError:
        pass
    StarshotAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()