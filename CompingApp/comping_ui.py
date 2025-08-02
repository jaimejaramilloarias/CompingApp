import tkinter as tk
from tkinter import messagebox, ttk
import os
from procesa_midi import procesa_midi

try:
    import mido
except Exception:  # pragma: no cover - mido no es esencial para las pruebas
    mido = None

class MidiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Comping MIDI Exporter")
        self.geometry("560x270")

        self.cifrado_label = tk.Label(self, text="Cifrado (usa | para separar compases):")
        self.cifrado_label.pack(pady=5)
        self.cifrado_entry = tk.Text(self, width=65, height=3)
        self.cifrado_entry.pack()

        self.midi_label = tk.Label(self, text="Archivo MIDI de referencia: reference_comping.mid")
        self.midi_label.pack(pady=10)

        self.rotacion = 0
        # Rotaciones individuales por acorde (índice de corchea -> rotación)
        self.rotaciones_forzadas = {}
        self.rot_label = tk.Label(self, text="Rotar: 0")
        self.rot_label.pack()
        self.rot_frame = tk.Frame(self)
        self.rot_frame.pack(pady=5)
        self.rot_minus = tk.Button(self.rot_frame, text="-", command=self.rotar_menos)
        self.rot_minus.pack(side="left")
        self.rot_plus = tk.Button(self.rot_frame, text="+", command=self.rotar_mas)
        self.rot_plus.pack(side="left")

        self.port_label = tk.Label(self, text="Puerto MIDI de salida:")
        self.port_label.pack(pady=5)
        self.port_combo = ttk.Combobox(self, state="readonly")
        self.port_combo.pack()
        self.refresh_ports()

        self.preview_btn = tk.Button(self, text="Previsualizar", command=self.preview_midi)
        self.preview_btn.pack(pady=10)

        self.export_btn = tk.Button(self, text="Exportar MIDI", command=self.export_midi)
        self.export_btn.pack(pady=5)

    def _rotar_seleccion(self, delta):
        """Rota los acordes seleccionados en ``cifrado_entry``.

        Si no hay selección, se ajusta la rotación global.
        ``delta`` debe ser ``+1`` o ``-1``.
        """
        try:
            sel_start = self.cifrado_entry.index("sel.first")
            sel_end = self.cifrado_entry.index("sel.last")
        except tk.TclError:
            sel_start = sel_end = None

        if sel_start and sel_end:
            antes = self.cifrado_entry.get("1.0", sel_start)
            seleccion = self.cifrado_entry.get(sel_start, sel_end)
            n_antes = len([c for c in antes.replace("|", " ").split() if c])
            chords_sel = [c for c in seleccion.replace("|", " ").split() if c]
            for i in range(len(chords_sel)):
                idx = n_antes + i
                actual = self.rotaciones_forzadas.get(idx, 0) + delta
                if -3 <= actual <= 3:
                    if actual:
                        self.rotaciones_forzadas[idx] = actual
                    elif idx in self.rotaciones_forzadas:
                        del self.rotaciones_forzadas[idx]
        else:
            nueva = self.rotacion + delta
            if -3 <= nueva <= 3:
                self.rotacion = nueva
                self.rot_label.config(text=f"Rotar: {self.rotacion:+d}")

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
            )
            print(f"Archivo exportado: {out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")

if __name__ == "__main__":
    app = MidiApp()
    app.mainloop()
