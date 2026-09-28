"""
Análise de Picket Fence com pylinac (testado para pylinac==3.5.0).

Interface Tkinter com os parâmetros de análise ajustáveis:
    - crop da imagem, filtro, tipo de MLC, inversão
    - tolerância, tolerância de ação, ajuste de sag, nº de pickets (auto ou fixo)
    - parâmetros avançados de detecção
"""

import inspect
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
from tkinter.scrolledtext import ScrolledText

from pylinac.picketfence import PicketFence, MLC, Orientation


# --------------------------------------------------------------------------- #
#                               VALORES PADRÃO                                #
# --------------------------------------------------------------------------- #
DEFAULTS = {
    # construtor PicketFence
    "mlc": "AGILITY",
    "crop_mm": "5",
    "filter": "",               # vazio = sem filtro
    # analyze()
    "tolerance": "0.5",
    "action_tolerance": "0.25",  # vazio = sem tolerância de ação
    "sag_adjustment": "0",
    "num_pickets": "",
    "num_pickets_auto": True,
    "invert": False,
    "orientation": "Automática",
    "picket_spacing": "",        # vazio = automático
    "height_threshold": "0.5",
    "edge_threshold": "1.5",
    "required_prominence": "0.2",
    "leaf_analysis_width_ratio": "0.4",
    "fwxm": "50",
    "separate_leaves": False,
    "nominal_gap_mm": "3",
}

ORIENTATIONS = {
    "Automática": None,
    "Cima-Baixo": Orientation.UP_DOWN,
    "Esquerda-Direita": Orientation.LEFT_RIGHT,
}


class PicketFenceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Picket Fence - pylinac")
        self.resizable(False, False)

        self.file_path = None
        self.pf = None
        self.vars = {}

        self._build_file_frame()
        self._build_image_frame()
        self._build_analysis_frame()
        self._build_advanced_frame()
        self._build_buttons()
        self._build_console()

        self._toggle_num_pickets()
        self._toggle_nominal_gap()

    # ----------------------------------------------------------------- #
    #                          CONSTRUÇÃO DA GUI                         #
    # ----------------------------------------------------------------- #
    def _entry(self, parent, row, label, key, unit="", width=8):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        var = tk.StringVar(value=DEFAULTS[key])
        entry = ttk.Entry(parent, textvariable=var, width=width)
        entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        if unit:
            ttk.Label(parent, text=unit, foreground="gray").grid(row=row, column=2, sticky="w")
        self.vars[key] = var
        return entry

    def _check(self, parent, row, label, key, command=None):
        var = tk.BooleanVar(value=DEFAULTS[key])
        ttk.Checkbutton(parent, text=label, variable=var, command=command).grid(
            row=row, column=0, columnspan=3, sticky="w", padx=5, pady=2)
        self.vars[key] = var

    def _build_file_frame(self):
        frm = ttk.LabelFrame(self, text="Arquivo")
        frm.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        ttk.Button(frm, text="Selecionar arquivo", command=self.select_file).grid(
            row=0, column=0, padx=5, pady=5)
        self.lbl_file = ttk.Label(frm, text="Nenhum arquivo selecionado", foreground="gray",
                                  width=70)
        self.lbl_file.grid(row=0, column=1, sticky="w", padx=5)

    def _build_image_frame(self):
        frm = ttk.LabelFrame(self, text="Imagem / MLC")
        frm.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        ttk.Label(frm, text="Tipo de MLC").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.vars["mlc"] = tk.StringVar(value=DEFAULTS["mlc"])
        ttk.Combobox(frm, textvariable=self.vars["mlc"], state="readonly", width=18,
                     values=[m.name for m in MLC]).grid(row=0, column=1, columnspan=2,
                                                        sticky="w", padx=5, pady=2)

        self._entry(frm, 1, "Crop das bordas", "crop_mm", "mm")
        self._entry(frm, 2, "Filtro mediana", "filter", "px (vazio = sem)")
        self._check(frm, 3, "Inverter imagem", "invert")

        ttk.Label(frm, text="Orientação").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.vars["orientation"] = tk.StringVar(value=DEFAULTS["orientation"])
        ttk.Combobox(frm, textvariable=self.vars["orientation"], state="readonly", width=18,
                     values=list(ORIENTATIONS)).grid(row=4, column=1, columnspan=2,
                                                     sticky="w", padx=5, pady=2)

    def _build_analysis_frame(self):
        frm = ttk.LabelFrame(self, text="Análise")
        frm.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)

        self._entry(frm, 0, "Tolerância", "tolerance", "mm")
        self._entry(frm, 1, "Tolerância de ação", "action_tolerance", "mm (vazio = sem)")
        self._entry(frm, 2, "Ajuste de sag", "sag_adjustment", "mm")
        self.ent_num_pickets = self._entry(frm, 3, "Nº de pickets", "num_pickets")
        self._check(frm, 4, "Detectar nº de pickets automaticamente", "num_pickets_auto",
                    command=self._toggle_num_pickets)

    def _build_advanced_frame(self):
        frm = ttk.LabelFrame(self, text="Avançado (detecção)")
        frm.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        left = ttk.Frame(frm)
        left.grid(row=0, column=0, sticky="n")
        right = ttk.Frame(frm)
        right.grid(row=0, column=1, sticky="n", padx=20)

        self._entry(left, 0, "Espaçamento entre pickets", "picket_spacing", "mm (vazio = auto)")
        self._entry(left, 1, "Height threshold", "height_threshold", "0–1")
        self._entry(left, 2, "Edge threshold", "edge_threshold")
        self._entry(left, 3, "Required prominence", "required_prominence", "0–1")

        self._entry(right, 0, "Leaf analysis width ratio", "leaf_analysis_width_ratio", "0–1")
        self._entry(right, 1, "FWXM", "fwxm", "%")
        self._check(right, 2, "Analisar lâminas separadamente", "separate_leaves",
                    command=self._toggle_nominal_gap)
        self.ent_nominal_gap = self._entry(right, 3, "Gap nominal", "nominal_gap_mm", "mm")

    def _build_buttons(self):
        frm = ttk.Frame(self)
        frm.grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Button(frm, text="Analisar", command=self.analyze_pf).grid(row=0, column=0, padx=5)
        ttk.Button(frm, text="Mostrar histograma", command=self.show_histogram).grid(
            row=0, column=1, padx=5)
        ttk.Button(frm, text="Restaurar padrões", command=self.reset_defaults).grid(
            row=0, column=2, padx=5)

    def _build_console(self):
        frm = ttk.LabelFrame(self, text="Console")
        frm.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 10))
        self.console = ScrolledText(frm, width=95, height=14, state="disabled",
                                    font=("Consolas", 9))
        self.console.grid(row=0, column=0, padx=5, pady=5)

    # ----------------------------------------------------------------- #
    #                              AUXILIARES                            #
    # ----------------------------------------------------------------- #
    def log(self, text):
        self.console.configure(state="normal")
        self.console.insert("end", text + "\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def _toggle_num_pickets(self):
        state = "disabled" if self.vars["num_pickets_auto"].get() else "normal"
        self.ent_num_pickets.configure(state=state)

    def _toggle_nominal_gap(self):
        state = "normal" if self.vars["separate_leaves"].get() else "disabled"
        self.ent_nominal_gap.configure(state=state)

    def reset_defaults(self):
        for key, var in self.vars.items():
            var.set(DEFAULTS[key])
        self._toggle_num_pickets()
        self._toggle_nominal_gap()
        self.log("Parâmetros restaurados para os valores padrão.")

    def _read(self, key, cast=float, optional=False, label=None):
        """Lê um campo de texto; vazio vira None se optional=True."""
        raw = self.vars[key].get().strip().replace(",", ".")
        if raw == "":
            if optional:
                return None
            raise ValueError(f"O campo '{label or key}' é obrigatório.")
        try:
            return cast(raw)
        except ValueError:
            tipo = "inteiro" if cast is int else "numérico"
            raise ValueError(f"O campo '{label or key}' precisa ser {tipo} (valor: '{raw}').")

    def _collect_params(self):
        """Monta os kwargs do construtor e do analyze() a partir da interface."""
        init_kwargs = {
            "mlc": MLC[self.vars["mlc"].get()],
            "crop_mm": self._read("crop_mm", label="Crop das bordas"),
            "filter": self._read("filter", int, optional=True, label="Filtro mediana"),
        }

        num_pickets = None
        if not self.vars["num_pickets_auto"].get():
            num_pickets = self._read("num_pickets", int, label="Nº de pickets")

        analyze_kwargs = {
            "tolerance": self._read("tolerance", label="Tolerância"),
            "action_tolerance": self._read("action_tolerance", optional=True,
                                           label="Tolerância de ação"),
            "sag_adjustment": self._read("sag_adjustment", label="Ajuste de sag"),
            "num_pickets": num_pickets,
            "invert": self.vars["invert"].get(),
            "orientation": ORIENTATIONS[self.vars["orientation"].get()],
            "picket_spacing": self._read("picket_spacing", optional=True,
                                         label="Espaçamento entre pickets"),
            "height_threshold": self._read("height_threshold", label="Height threshold"),
            "edge_threshold": self._read("edge_threshold", label="Edge threshold"),
            "required_prominence": self._read("required_prominence",
                                              label="Required prominence"),
            "leaf_analysis_width_ratio": self._read("leaf_analysis_width_ratio",
                                                    label="Leaf analysis width ratio"),
            "fwxm": self._read("fwxm", label="FWXM"),
        }
        if self.vars["separate_leaves"].get():
            analyze_kwargs["separate_leaves"] = True
            analyze_kwargs["nominal_gap_mm"] = self._read("nominal_gap_mm", label="Gap nominal")

        # Checagens de coerência
        if analyze_kwargs["action_tolerance"] is not None and \
                analyze_kwargs["action_tolerance"] >= analyze_kwargs["tolerance"]:
            raise ValueError("A tolerância de ação deve ser menor que a tolerância.")
        if num_pickets is not None and num_pickets < 2:
            raise ValueError("O nº de pickets deve ser pelo menos 2.")

        return init_kwargs, self._filter_supported(analyze_kwargs)

    def _filter_supported(self, kwargs):
        """Remove parâmetros que a versão instalada do pylinac não aceita."""
        params = inspect.signature(PicketFence.analyze).parameters
        if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
            return kwargs
        unsupported = [k for k in kwargs if k not in params]
        for k in unsupported:
            self.log(f"Aviso: '{k}' não é suportado por esta versão do pylinac e foi ignorado.")
            kwargs.pop(k)
        return kwargs

    # ----------------------------------------------------------------- #
    #                                AÇÕES                               #
    # ----------------------------------------------------------------- #
    def select_file(self):
        path = askopenfilename(title="Selecione o arquivo de imagem")
        if not path:
            self.log("Nenhum arquivo selecionado!")
            return
        self.file_path = path
        self.pf = None
        self.lbl_file.configure(text=path, foreground="black")
        self.log(f"Arquivo selecionado: {path}")

    def analyze_pf(self):
        if not self.file_path:
            messagebox.showwarning("Picket Fence", "Selecione um arquivo primeiro.")
            return

        try:
            init_kwargs, analyze_kwargs = self._collect_params()
        except ValueError as e:
            messagebox.showerror("Parâmetro inválido", str(e))
            return

        self.log("-" * 60)
        self.log(f"MLC: {init_kwargs['mlc'].name} | crop: {init_kwargs['crop_mm']} mm | "
                 f"filtro: {init_kwargs['filter']}")
        self.log("analyze(" + ", ".join(f"{k}={v}" for k, v in analyze_kwargs.items()) + ")")

        try:
            self.pf = PicketFence(self.file_path, **init_kwargs)
            self.pf.analyze(**analyze_kwargs)
        except ValueError as e:
            self.pf = None
            msg = str(e)
            if "NaN" in msg:
                msg = ("Não foi possível detectar os pickets (menos de 2 encontrados).\n"
                       "Verifique a aquisição da imagem, a orientação, o crop, a inversão "
                       "ou informe o nº de pickets manualmente.")
            self.log(f"ERRO: {msg}")
            messagebox.showerror("Erro na análise", msg)
            return
        except Exception as e:
            self.pf = None
            self.log(f"ERRO ({type(e).__name__}): {e}")
            messagebox.showerror("Erro na análise", f"{type(e).__name__}: {e}")
            return

        self.log(self.pf.results())
        '''try:
            widths = self.pf.results_data(as_dict=True)["picket_widths"]
            self.log(f"Larguras dos pickets: {widths}")
        except (KeyError, TypeError):
            pass'''
        self.log("Análise concluída!")

        self.pf.plot_analyzed_image(show_text=True)

    def show_histogram(self):
        if self.pf is None:
            messagebox.showwarning("Picket Fence", "Faça uma análise primeiro.")
            return
        self.pf.plot_histogram()


if __name__ == "__main__":
    app = PicketFenceApp()
    app.mainloop()