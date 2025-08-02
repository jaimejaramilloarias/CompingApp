import tkinter as tk
from tkinter import messagebox, ttk, filedialog, colorchooser
import tkinter.font as tkfont
import os
from procesa_midi import procesa_midi, notas_midi_acorde, notas_naturales
from cifrado_utils import analizar_cifrado
import threading

# Colores y fuente para un aspecto moderno
BACKGROUND = "#000000"  # fondo general negro puro
PANEL_BG = "#2e2e2e"  # paneles y frames en gris oscuro
FOREGROUND = "#fafafa"  # texto principal
SECONDARY_FOREGROUND = "#bdbdbd"  # texto secundario
ACCENT = "#ff9800"  # color de acento
ENTRY_BACKGROUND = "#23252b"  # entradas de texto
COMBOBOX_BG = "#ffffff"  # color de fondo de los comboboxes
COMBOBOX_FG = "#000000"  # texto de los comboboxes en negro
FONT = ("Monaco", 18)

try:
    import mido
except Exception:  # pragma: no cover - mido no es esencial para las pruebas
    mido = None

class MidiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Comping MIDI Exporter")
        self.geometry("1100x650")
        self.configure(bg=BACKGROUND)

        # Apariencia
        self.bg_color = BACKGROUND
        self.panel_bg_color = PANEL_BG
        self.fg_color = FOREGROUND
        self.secondary_fg_color = SECONDARY_FOREGROUND
        self.accent_color = ACCENT
        self.entry_bg_color = ENTRY_BACKGROUND
        self.combobox_bg_color = COMBOBOX_BG
        self.combobox_fg_color = COMBOBOX_FG
        self.font_family = FONT[0]
        self.font_size = FONT[1]
        self.font = (self.font_family, self.font_size)
        self.header_font = (self.font_family, 36)
        self.secondary_labels = set()
        self.window_order = list(range(32))
        self.preview_thread = None
        self.stop_preview = None

        # Menú de apariencia
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        apariencia_menu = tk.Menu(self.menu_bar, tearoff=0)
        apariencia_menu.add_command(label="Personalizar", command=self.open_appearance_window)
        self.menu_bar.add_cascade(label="Apariencia", menu=apariencia_menu)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.style.configure(
            "TCombobox",
            fieldbackground=self.combobox_bg_color,
            background=self.combobox_bg_color,
            foreground=self.combobox_fg_color,
            arrowcolor=self.combobox_fg_color,
        )

        # Cabecera
        self.header_label = tk.Label(
            self,
            text="CompingApp - Jaramillo",
            bg=self.bg_color,
            fg=self.accent_color,
            font=self.header_font,
        )
        self.header_label.grid(row=0, column=0, columnspan=2, pady=(10, 20))
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Paneles
        self.left_panel = tk.Frame(self, bg=self.panel_bg_color)
        self.left_panel.grid(row=1, column=0, padx=20, pady=10, sticky="n")
        self.right_panel = tk.Frame(self, bg=self.panel_bg_color)
        self.right_panel.grid(row=1, column=1, padx=20, pady=10, sticky="n")

        # ---- Panel izquierdo ----
        self.cifrado_label = tk.Label(
            self.left_panel,
            text="Cifrado (usa | para separar compases):",
            bg=self.panel_bg_color,
            fg=self.fg_color,
            font=self.font,
        )
        self.cifrado_label.pack(pady=5)
        self.cifrado_entry = tk.Text(
            self.left_panel,
            width=45,
            height=5,
            bg=self.entry_bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            font=self.font,
        )
        self.cifrado_entry.pack(fill="x", padx=10)
        self.cifrado_entry.bind("<KeyRelease>", lambda e: self.update_chord_list())

        self.reference_midi_path = "reference_comping.mid"
        self.midi_label = tk.Label(
            self.left_panel,
            text=f"Archivo MIDI de referencia: {os.path.basename(self.reference_midi_path)}",
            bg=self.panel_bg_color,
            fg=self.secondary_fg_color,
            font=self.font,
        )
        self.midi_label.pack(pady=5)
        self.secondary_labels.add(self.midi_label)
        self.midi_btn = tk.Button(
            self.left_panel,
            text="Cargar MIDI",
            command=self.load_midi,
            bg=self.accent_color,
            fg=self.bg_color,
            activebackground=self.accent_color,
            activeforeground=self.bg_color,
            font=(self.font_family, self.font_size, "bold"),
            relief="flat",
            bd=0,
        )
        self.midi_btn.pack(pady=5, fill="x", padx=10)

        self.rotacion = 0
        # Rotaciones individuales por acorde (índice de corchea -> rotación)
        self.rotaciones_forzadas = {}
        # Desplazamientos de octava por acorde
        self.octavas_forzadas = {}
        self.chords = []
        # Inversiones base calculadas a partir de la nota más grave de cada acorde
        self.base_inversions = []
        self.rot_label = tk.Label(
            self.left_panel,
            text="Rotar: 0",
            bg=self.panel_bg_color,
            fg=self.fg_color,
            font=self.font,
        )
        self.rot_label.pack()
        self.rot_frame = tk.Frame(self.left_panel, bg=self.panel_bg_color)
        self.rot_frame.pack(pady=5)
        self.rot_minus = tk.Button(
            self.rot_frame,
            text="-",
            command=self.rotar_menos,
            bg=self.accent_color,
            fg=self.bg_color,
            activebackground=self.accent_color,
            activeforeground=self.bg_color,
            font=(self.font_family, self.font_size, "bold"),
            relief="flat",
            bd=0,
            width=4,
        )
        self.rot_minus.pack(side="left", padx=5)
        self.rot_plus = tk.Button(
            self.rot_frame,
            text="+",
            command=self.rotar_mas,
            bg=self.accent_color,
            fg=self.bg_color,
            activebackground=self.accent_color,
            activeforeground=self.bg_color,
            font=(self.font_family, self.font_size, "bold"),
            relief="flat",
            bd=0,
            width=4,
        )
        self.rot_plus.pack(side="left", padx=5)

        self.reset_btn = tk.Button(
            self.left_panel,
            text="Reestablecer",
            command=self.reset_rotaciones,
            bg=self.accent_color,
            fg=self.bg_color,
            activebackground=self.accent_color,
            activeforeground=self.bg_color,
            font=(self.font_family, self.font_size, "bold"),
            relief="flat",
            bd=0,
        )
        self.reset_btn.pack(pady=5, fill="x", padx=10)

        self.spread_var = tk.BooleanVar(value=False)
        self.spread_btn = tk.Checkbutton(
            self.left_panel,
            text="Spread",
            variable=self.spread_var,
            bg=self.panel_bg_color,
            fg=self.fg_color,
            selectcolor=self.accent_color,
            activebackground=self.panel_bg_color,
            activeforeground=self.fg_color,
            font=self.font,
        )
        self.spread_btn.pack(pady=5)

        self.variation_btn = tk.Button(
            self.left_panel,
            text="Generar variación",
            command=self.generar_variacion,
            bg=self.accent_color,
            fg=self.bg_color,
            activebackground=self.accent_color,
            activeforeground=self.bg_color,
            font=(self.font_family, self.font_size, "bold"),
            relief="flat",
            bd=0,
        )
        self.variation_btn.pack(pady=5, fill="x", padx=10)

        # ---- Panel derecho ----
        self.chord_label = tk.Label(
            self.right_panel,
            text="Acorde:",
            bg=self.panel_bg_color,
            fg=self.fg_color,
            font=self.font,
        )
        self.chord_label.pack(pady=5)
        self.chord_combo = ttk.Combobox(self.right_panel, state="readonly", font=self.font)
        self.chord_combo.bind("<<ComboboxSelected>>", self.on_chord_selected)
        self.chord_combo.pack(fill="x", padx=10)

        self.inv_label = tk.Label(
            self.right_panel,
            text="Inversión:",
            bg=self.panel_bg_color,
            fg=self.fg_color,
            font=self.font,
        )
        self.inv_label.pack(pady=5)
        self.inv_options = ["Fundamental", "1ª inversión", "2ª inversión", "3ª inversión"]
        self.inv_frame = tk.Frame(self.right_panel, bg=self.panel_bg_color)
        self.inv_frame.pack()
        self.inv_combo = ttk.Combobox(
            self.inv_frame,
            state="readonly",
            values=self.inv_options,
            font=self.font,
        )
        self.inv_combo.bind("<<ComboboxSelected>>", self.on_inv_selected)
        self.inv_combo.pack(side="left")
        self.oct_frame = tk.Frame(self.inv_frame, bg=self.panel_bg_color)
        self.oct_frame.pack(side="left", padx=5)
        self.oct_label = tk.Label(
            self.oct_frame,
            text="Octavar",
            bg=self.panel_bg_color,
            fg=self.fg_color,
            font=self.font,
        )
        self.oct_label.pack()
        self.oct_btns = tk.Frame(self.oct_frame, bg=self.panel_bg_color)
        self.oct_btns.pack()
        self.oct_minus = tk.Button(
            self.oct_btns,
            text="-",
            command=self.octavar_menos,
            bg=self.accent_color,
            fg=self.bg_color,
            activebackground=self.accent_color,
            activeforeground=self.bg_color,
            font=(self.font_family, self.font_size, "bold"),
            relief="flat",
            bd=0,
            width=4,
        )
        self.oct_minus.pack(side="left", padx=5)
        self.oct_plus = tk.Button(
            self.oct_btns,
            text="+",
            command=self.octavar_mas,
            bg=self.accent_color,
            fg=self.bg_color,
            activebackground=self.accent_color,
            activeforeground=self.bg_color,
            font=(self.font_family, self.font_size, "bold"),
            relief="flat",
            bd=0,
            width=4,
        )
        self.oct_plus.pack(side="left", padx=5)

        self.update_chord_list()

        self.port_label = tk.Label(
            self.right_panel,
            text="Puerto MIDI de salida:",
            bg=self.panel_bg_color,
            fg=self.fg_color,
            font=self.font,
        )
        self.port_label.pack(pady=5)
        self.port_combo = ttk.Combobox(self.right_panel, state="readonly", font=self.font)
        self.port_combo.pack(fill="x", padx=10)
        self.refresh_ports()

        self.preview_btn = tk.Button(
            self.right_panel,
            text="Previsualizar",
            command=self.preview_midi,
            bg=self.accent_color,
            fg=self.bg_color,
            activebackground=self.accent_color,
            activeforeground=self.bg_color,
            font=(self.font_family, self.font_size, "bold"),
            relief="flat",
            bd=0,
        )
        self.preview_btn.pack(pady=10, fill="x", padx=10)

        self.export_btn = tk.Button(
            self.right_panel,
            text="Exportar MIDI",
            command=self.export_midi,
            bg=self.accent_color,
            fg=self.bg_color,
            activebackground=self.accent_color,
            activeforeground=self.bg_color,
            font=(self.font_family, self.font_size, "bold"),
            relief="flat",
            bd=0,
        )
        self.export_btn.pack(pady=5, fill="x", padx=10)

        self.apply_styles()

    def _rotar_seleccion(self, delta):
        """Ajusta la rotación global de todos los acordes."""
        nueva = self.rotacion + delta
        if -3 <= nueva <= 3:
            self.rotacion = nueva
            self.rot_label.config(text=f"Rotar: {self.rotacion:+d}")
        self.update_inversion_display()

    def reset_rotaciones(self):
        self.rotacion = 0
        self.rotaciones_forzadas.clear()
        self.octavas_forzadas.clear()
        self.rot_label.config(text="Rotar: 0")
        self.update_inversion_display()

    def calcular_inversiones(self):
        """Calcula la inversión base de cada acorde según su nota más grave."""
        self.base_inversions = []
        prev_bajo = None
        cache = {}
        for acorde in self.chords:
            if acorde not in cache:
                cache[acorde] = analizar_cifrado(acorde)[0]
            fundamental, grados = cache[acorde]
            if prev_bajo is None:
                inv_escogida = 0
                notas = None
                for inv in range(4):
                    cand = notas_midi_acorde(
                        fundamental, grados, base_octava=4, prev_bajo=None, inversion=inv
                    )
                    notas = cand
                    if cand[0] >= 57:
                        inv_escogida = inv
                        break
                prev_bajo = notas[0]
                self.base_inversions.append(inv_escogida)
            else:
                notas = notas_midi_acorde(
                    fundamental, grados, base_octava=4, prev_bajo=prev_bajo
                )
                prev_bajo = notas[0]
                base = 48 + notas_naturales.get(fundamental, 0)
                diff = (notas[0] - base) % 12
                grados_mod = [g % 12 for g in grados]
                inv_idx = grados_mod.index(diff) if diff in grados_mod else 0
                self.base_inversions.append(inv_idx)

    def update_chord_list(self):
        text = self.cifrado_entry.get("1.0", tk.END)
        chords = [a.strip() for a in text.replace("|", " ").split() if a.strip()]
        self.chords = chords
        self.rotaciones_forzadas = {
            i: r for i, r in self.rotaciones_forzadas.items() if i < len(chords)
        }
        self.octavas_forzadas = {
            i: o for i, o in self.octavas_forzadas.items() if i < len(chords)
        }
        self.calcular_inversiones()
        display = [f"{i+1}: {c}" for i, c in enumerate(chords)]
        self.chord_combo["values"] = display
        if display:
            if self.chord_combo.current() < 0 or self.chord_combo.current() >= len(display):
                self.chord_combo.current(0)
            self.update_inversion_display()
        else:
            self.chord_combo.set("")
            self.inv_combo.set("")

    def on_chord_selected(self, event=None):
        self.update_inversion_display()

    def on_inv_selected(self, event=None):
        idx = self.chord_combo.current()
        if idx < 0:
            return
        desired = self.inv_combo.current()
        if desired < 0:
            return
        base = self.base_inversions[idx] if idx < len(self.base_inversions) else 0
        offset = desired - (self.rotacion + base)
        if offset:
            self.rotaciones_forzadas[idx] = offset
        elif idx in self.rotaciones_forzadas:
            del self.rotaciones_forzadas[idx]

    def update_inversion_display(self):
        idx = self.chord_combo.current()
        if 0 <= idx < len(self.chords):
            base = self.base_inversions[idx] if idx < len(self.base_inversions) else 0
            rot = base + self.rotacion + self.rotaciones_forzadas.get(idx, 0)
            self.inv_combo.current(rot % 4)

    def rotar_mas(self):
        self._rotar_seleccion(1)

    def rotar_menos(self):
        self._rotar_seleccion(-1)

    def octavar_mas(self):
        idx = self.chord_combo.current()
        if idx < 0:
            return
        val = self.octavas_forzadas.get(idx, 0) + 1
        if val:
            self.octavas_forzadas[idx] = val
        elif idx in self.octavas_forzadas:
            del self.octavas_forzadas[idx]

    def octavar_menos(self):
        idx = self.chord_combo.current()
        if idx < 0:
            return
        val = self.octavas_forzadas.get(idx, 0) - 1
        if val:
            self.octavas_forzadas[idx] = val
        elif idx in self.octavas_forzadas:
            del self.octavas_forzadas[idx]

    def get_midi_ports(self):
        if mido is None:
            return []
        try:
            return mido.get_output_names()
        except Exception:
            return []

    def refresh_ports(self):
        ports = self.get_midi_ports()
        self.port_combo["values"] = ports
        if ports:
            self.port_combo.current(0)

    def generar_variacion(self):
        import random
        ventanas = list(range(32))
        random.shuffle(ventanas)
        self.window_order = ventanas

    def preview_midi(self):
        if self.preview_thread and self.preview_thread.is_alive():
            if self.stop_preview:
                self.stop_preview.set()
            self.preview_btn.config(text="Previsualizar")
            return
        if mido is None:
            messagebox.showerror("Error", "La librería mido no está instalada.")
            return
        cifrado = self.cifrado_entry.get("1.0", tk.END).strip()
        if not cifrado:
            messagebox.showerror("Error", "Por favor, escribe un cifrado.")
            return
        if not os.path.exists(self.reference_midi_path):
            messagebox.showerror(
                "Error",
                f"No se encontró '{os.path.basename(self.reference_midi_path)}'",
            )
            return
        port_name = self.port_combo.get()
        if not port_name:
            messagebox.showerror("Error", "Selecciona un puerto MIDI.")
            return

        def run_preview():
            try:
                midi_obj = procesa_midi(
                    self.reference_midi_path,
                    cifrado,
                    rotacion=self.rotacion,
                    rotaciones=self.rotaciones_forzadas,
                    octavas=self.octavas_forzadas,
                    spread=self.spread_var.get(),
                    window_order=self.window_order,
                    save=False,
                )
                import io

                midi_bytes = io.BytesIO()
                midi_obj.write(midi_bytes)
                midi_bytes.seek(0)
                mid = mido.MidiFile(file=midi_bytes)
                with mido.open_output(port_name) as port:
                    for msg in mid.play():
                        if self.stop_preview.is_set():
                            break
                        port.send(msg)
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error al previsualizar:\n{e}")
            finally:
                self.preview_btn.config(text="Previsualizar")
                self.preview_thread = None
                self.stop_preview = None

        self.stop_preview = threading.Event()
        self.preview_btn.config(text="Detener")
        self.preview_thread = threading.Thread(target=run_preview, daemon=True)
        self.preview_thread.start()

    def export_midi(self):
        cifrado = self.cifrado_entry.get("1.0", tk.END).strip()
        if not cifrado:
            messagebox.showerror("Error", "Por favor, escribe un cifrado.")
            return
        if not os.path.exists(self.reference_midi_path):
            messagebox.showerror(
                "Error",
                f"No se encontró '{os.path.basename(self.reference_midi_path)}'",
            )
            return
        try:
            out_path = procesa_midi(
                self.reference_midi_path,
                cifrado,
                rotacion=self.rotacion,
                rotaciones=self.rotaciones_forzadas,
                octavas=self.octavas_forzadas,
                spread=self.spread_var.get(),
                window_order=self.window_order,
            )
            print(f"Archivo exportado: {out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")

    def load_midi(self):
        path = filedialog.askopenfilename(filetypes=[("MIDI", "*.mid"), ("Todos", "*")])
        if path:
            self.reference_midi_path = path
            self.midi_label.config(
                text=f"Archivo MIDI de referencia: {os.path.basename(path)}"
            )

    def open_appearance_window(self):
        win = tk.Toplevel(self)
        win.title("Apariencia")
        win.configure(bg=self.bg_color)

        font_frame = tk.LabelFrame(
            win, text="Fuentes", bg=self.bg_color, fg=self.fg_color, font=self.font
        )
        font_frame.pack(fill="both", expand=True, padx=10, pady=10)

        font_combo = ttk.Combobox(
            font_frame,
            state="readonly",
            values=sorted(tkfont.families()),
            font=self.font,
        )
        font_combo.set(self.font_family)
        font_combo.bind("<<ComboboxSelected>>", lambda e: self.set_font_family(font_combo.get()))
        font_combo.pack(fill="x", padx=10, pady=5)

        size_frame = tk.Frame(font_frame, bg=self.bg_color)
        size_frame.pack(pady=5)
        tk.Label(
            size_frame, text="Tamaño:", bg=self.bg_color, fg=self.fg_color, font=self.font
        ).pack(side="left")
        size_spin = tk.Spinbox(
            size_frame,
            from_=8,
            to=72,
            width=5,
            font=self.font,
            command=lambda: self.set_font_size(int(size_spin.get())),
        )
        size_spin.delete(0, "end")
        size_spin.insert(0, self.font_size)
        size_spin.pack(side="left", padx=5)

        color_frame = tk.LabelFrame(
            win, text="Colores", bg=self.bg_color, fg=self.fg_color, font=self.font
        )
        color_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._add_color_selector(color_frame, "Fondo", "bg_color")
        self._add_color_selector(color_frame, "Panel", "panel_bg_color")
        self._add_color_selector(color_frame, "Texto", "fg_color")
        self._add_color_selector(color_frame, "Texto secundario", "secondary_fg_color")
        self._add_color_selector(color_frame, "Botones", "accent_color")
        self._add_color_selector(color_frame, "Entrada", "entry_bg_color")
        self._add_color_selector(color_frame, "Combobox", "combobox_bg_color")
        self._add_color_selector(color_frame, "Texto combobox", "combobox_fg_color")

    def _add_color_selector(self, parent, label, attr):
        frame = tk.Frame(parent, bg=self.bg_color)
        frame.pack(pady=5, fill="x")
        tk.Label(frame, text=label, bg=self.bg_color, fg=self.fg_color, font=self.font).pack(
            side="left"
        )
        preview = tk.Label(frame, bg=getattr(self, attr), width=3, height=1)
        preview.pack(side="left", padx=5)
        preview.bind(
            "<Button-1>",
            lambda e, a=attr, p=preview: self.choose_color(a, p),
        )

    def choose_color(self, attr, widget):
        color = colorchooser.askcolor(getattr(self, attr))[1]
        if color:
            setattr(self, attr, color)
            widget.config(bg=color)
            self.apply_styles()

    def set_font_family(self, family):
        self.font_family = family
        self.font = (self.font_family, self.font_size)
        self.header_font = (self.font_family, self.font_size + 18)
        self.apply_styles()

    def set_font_size(self, size):
        self.font_size = size
        self.font = (self.font_family, self.font_size)
        self.header_font = (self.font_family, self.font_size + 18)
        self.apply_styles()

    def apply_styles(self):
        self.configure(bg=self.bg_color)
        self.header_label.configure(
            bg=self.bg_color, fg=self.accent_color, font=self.header_font
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=self.combobox_bg_color,
            background=self.combobox_bg_color,
            foreground=self.combobox_fg_color,
            arrowcolor=self.combobox_fg_color,
        )
        for panel in (self.left_panel, self.right_panel):
            panel.configure(bg=self.panel_bg_color)
            for child in panel.winfo_children():
                self._style_widget(child)

    def _style_widget(self, widget):
        if isinstance(widget, tk.Label):
            fg = self.secondary_fg_color if widget in self.secondary_labels else self.fg_color
            widget.configure(bg=self.panel_bg_color, fg=fg, font=self.font)
        elif isinstance(widget, tk.Button):
            widget.configure(
                bg=self.accent_color,
                fg=self.bg_color,
                activebackground=self.accent_color,
                activeforeground=self.bg_color,
                font=(self.font_family, self.font_size, "bold"),
                relief="flat",
                bd=0,
            )
        elif isinstance(widget, tk.Text):
            widget.configure(
                bg=self.entry_bg_color,
                fg=self.fg_color,
                insertbackground=self.fg_color,
                font=self.font,
                relief="flat",
                bd=0,
            )
        elif isinstance(widget, tk.Frame):
            widget.configure(bg=self.panel_bg_color)
        elif isinstance(widget, tk.Checkbutton):
            widget.configure(
                bg=self.panel_bg_color,
                fg=self.fg_color,
                selectcolor=self.accent_color,
                activebackground=self.panel_bg_color,
                activeforeground=self.fg_color,
                font=self.font,
            )
        elif isinstance(widget, ttk.Combobox):
            widget.configure(font=self.font, foreground=self.combobox_fg_color)
        for child in widget.winfo_children():
            self._style_widget(child)

if __name__ == "__main__":
    app = MidiApp()
    app.mainloop()
