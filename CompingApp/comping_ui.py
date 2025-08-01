import tkinter as tk
from tkinter import messagebox, ttk
import os
from procesa_midi import procesa_midi

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

        self.inv_label = tk.Label(self, text="Inversión inicial del acorde:")
        self.inv_label.pack()
        self.inversion = ttk.Combobox(self, state="readonly")
        self.inversion['values'] = ("fundamental", "primera inversión", "segunda inversión", "tercera inversión")
        self.inversion.current(0)
        self.inversion.pack(pady=5)

        self.export_btn = tk.Button(self, text="Exportar MIDI", command=self.export_midi)
        self.export_btn.pack(pady=20)

    def export_midi(self):
        cifrado = self.cifrado_entry.get("1.0", tk.END).strip()
        if not cifrado:
            messagebox.showerror("Error", "Por favor, escribe un cifrado.")
            return
        if not os.path.exists("reference_comping.mid"):
            messagebox.showerror("Error", "No se encontró 'reference_comping.mid' en esta carpeta.")
            return
        try:
            inversion_idx = self.inversion.current()
            out_path = procesa_midi("reference_comping.mid", cifrado, inversion_inicial=inversion_idx)
            messagebox.showinfo("¡Listo!", f"Archivo exportado:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")

if __name__ == "__main__":
    app = MidiApp()
    app.mainloop()
