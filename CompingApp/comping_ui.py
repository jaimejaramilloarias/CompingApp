import tkinter as tk
from tkinter import messagebox, ttk
import os
from procesa_midi import procesa_midi, notas_midi_acorde, notas_naturales
from cifrado_utils import analizar_cifrado

# Colores y fuente para un aspecto moderno
BACKGROUND = "#2b2b2b"
FOREGROUND = "#f5f5f5"
# Color oscuro para botones y entradas
ACCENT = "#3c3f41"
ENTRY_BACKGROUND = "#3c3f41"
FONT = ("Helvetica", 20)

try:
    import mido
except Exception:  # pragma: no cover - mido no es esencial para las pruebas
    mido = None

class MidiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Comping MIDI Exporter")
        self.geometry("560x360")
        self.configure(bg=BACKGROUND)

        self.cifrado_label = tk.Label(
            self,
            text="Cifrado (usa | para separar compases):",
            bg=BACKGROUND,
            fg=FOREGROUND,
            font=FONT,
        )
        self.cifrado_label.pack(pady=5)
        self.cifrado_entry = tk.Text(
            self,
            width=65,
            height=3,
            bg=ENTRY_BACKGROUND,
            fg=FOREGROUND,
            insertbackground=FOREGROUND,
            font=FONT,
        )
        self.cifrado_entry.pack()
        self.cifrado_entry.bind("<KeyRelease>", lambda e: self.update_chord_list())

        self.midi_label = tk.Label(
            self,
            text="Archivo MIDI de referencia: reference_comping.mid",
            bg=BACKGROUND,
            fg=FOREGROUND,
            font=FONT,
        )
        self.midi_label.pack(pady=10)

        self.rotacion = 0
        # Rotaciones individuales por acorde (índice de corchea -> rotación)
        self.rotaciones_forzadas = {}
        self.chords = []
        # Inversiones base calculadas a partir de la nota más grave de cada acorde
        self.base_inversions = []
        self.rot_label = tk.Label(self, text="Rotar: 0", bg=BACKGROUND, fg=FOREGROUND, font=FONT)
        self.rot_label.pack()
        self.rot_frame = tk.Frame(self, bg=BACKGROUND)
        self.rot_frame.pack(pady=5)
        self.rot_minus = tk.Button(
            self.rot_frame,
            text="-",
            command=self.rotar_menos,
            bg=ACCENT,
            fg=FOREGROUND,
            activebackground=ACCENT,
            activeforeground=FOREGROUND,
            font=FONT,
        )
        self.rot_minus.pack(side="left")
        self.rot_plus = tk.Button(
            self.rot_frame,
            text="+",
            command=self.rotar_mas,
            bg=ACCENT,
            fg=FOREGROUND,
            activebackground=ACCENT,
            activeforeground=FOREGROUND,
            font=FONT,
        )
        self.rot_plus.pack(side="left")

        self.reset_btn = tk.Button(
            self,
            text="Reestablecer",
            command=self.reset_rotaciones,
            bg=ACCENT,
            fg=FOREGROUND,
            activebackground=ACCENT,
            activeforeground=FOREGROUND,
            font=FONT,
        )
        self.reset_btn.pack(pady=5)

        self.chord_label = tk.Label(self, text="Acorde:", bg=BACKGROUND, fg=FOREGROUND, font=FONT)
        self.chord_label.pack(pady=5)
        self.chord_combo = ttk.Combobox(self, state="readonly", font=FONT)
        self.chord_combo.bind("<<ComboboxSelected>>", self.on_chord_selected)
        self.chord_combo.pack()

        self.inv_label = tk.Label(self, text="Inversión:", bg=BACKGROUND, fg=FOREGROUND, font=FONT)
        self.inv_label.pack(pady=5)
        self.inv_options = ["Fundamental", "1ª inversión", "2ª inversión", "3ª inversión"]
        self.inv_combo = ttk.Combobox(self, state="readonly", values=self.inv_options, font=FONT)
        self.inv_combo.bind("<<ComboboxSelected>>", self.on_inv_selected)
        self.inv_combo.pack()
        self.update_chord_list()

        self.spread_var = tk.BooleanVar(value=False)
        self.spread_btn = tk.Checkbutton(
            self,
            text="Spread",
            variable=self.spread_var,
            bg=ACCENT,
            fg=FOREGROUND,
            selectcolor=ACCENT,
            activebackground=ACCENT,
            activeforeground=FOREGROUND,
            font=FONT,
        )
        self.spread_btn.pack(pady=5)

        self.port_label = tk.Label(self, text="Puerto MIDI de salida:", bg=BACKGROUND, fg=FOREGROUND, font=FONT)
        self.port_label.pack(pady=5)
        self.port_combo = ttk.Combobox(self, state="readonly", font=FONT)
        self.port_combo.pack()
        self.refresh_ports()

        self.preview_btn = tk.Button(
            self,
            text="Previsualizar",
            command=self.preview_midi,
            bg=ACCENT,
            fg=FOREGROUND,
            activebackground=ACCENT,
            activeforeground=FOREGROUND,
            font=FONT,
        )
        self.preview_btn.pack(pady=10)

        self.export_btn = tk.Button(
            self,
            text="Exportar MIDI",
            command=self.export_midi,
            bg=ACCENT,
            fg=FOREGROUND,
            activebackground=ACCENT,
            activeforeground=FOREGROUND,
            font=FONT,
        )
        self.export_btn.pack(pady=5)

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

    def preview_midi(self):
        if mido is None:
            messagebox.showerror("Error", "La librería mido no está instalada.")
            return
        cifrado = self.cifrado_entry.get("1.0", tk.END).strip()
        if not cifrado:
            messagebox.showerror("Error", "Por favor, escribe un cifrado.")
            return
        if not os.path.exists("reference_comping.mid"):
            messagebox.showerror("Error", "No se encontró 'reference_comping.mid' en esta carpeta.")
            return
        port_name = self.port_combo.get()
        if not port_name:
            messagebox.showerror("Error", "Selecciona un puerto MIDI.")
            return
        try:
            midi_obj = procesa_midi(
                "reference_comping.mid",
                cifrado,
                rotacion=self.rotacion,
                rotaciones=self.rotaciones_forzadas,
                spread=self.spread_var.get(),
                save=False,
            )
            import io

            midi_bytes = io.BytesIO()
            midi_obj.write(midi_bytes)
            midi_bytes.seek(0)
            mid = mido.MidiFile(file=midi_bytes)
            with mido.open_output(port_name) as port:
                for msg in mid.play():
                    port.send(msg)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al previsualizar:\n{e}")

    def export_midi(self):
        cifrado = self.cifrado_entry.get("1.0", tk.END).strip()
        if not cifrado:
            messagebox.showerror("Error", "Por favor, escribe un cifrado.")
            return
        if not os.path.exists("reference_comping.mid"):
            messagebox.showerror("Error", "No se encontró 'reference_comping.mid' en esta carpeta.")
            return
        try:
            out_path = procesa_midi(
                "reference_comping.mid",
                cifrado,
                rotacion=self.rotacion,
                rotaciones=self.rotaciones_forzadas,
                spread=self.spread_var.get(),
            )
            print(f"Archivo exportado: {out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")

if __name__ == "__main__":
    app = MidiApp()
    app.mainloop()
