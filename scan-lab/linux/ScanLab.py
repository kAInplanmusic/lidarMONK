#!/usr/bin/env python3
"""Small Linux GUI for the offline inspector."""
import json
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext
from inspect_media import inspect

root = tk.Tk(); root.title('lidarMONK · Linux Scan Lab'); root.geometry('880x620')
root.configure(background='#101b22')
header = tk.Label(root, text='◈  lidarMONK   /   Linux Scan Lab', fg='#75e2bc', bg='#101b22', font=('Sans', 19, 'bold')); header.pack(anchor='w', padx=18, pady=(18, 6))
info = tk.Label(root, text='Originaldateien lokal prüfen · Keine Übertragung · Keine garantierten Meterangaben', fg='#bed1cf', bg='#101b22', wraplength=800); info.pack(anchor='w', padx=20)
bar = tk.Frame(root, bg='#101b22'); bar.pack(fill='x', padx=18, pady=12)
text = scrolledtext.ScrolledText(root, bg='#19272d', fg='#e9f2ee', insertbackground='white', wrap='word', font=('Monospace', 10)); text.pack(fill='both', expand=True, padx=18, pady=(0, 18))
text.insert('end', 'Wähle Originaldateien. Optional wird ein Ordner für die Exportkopien erkannter Tiefenbilder abgefragt.\n')

def append(line):
    text.insert('end', line); text.see('end')

def choose():
    files = filedialog.askopenfilenames(title='iPhone-Originaldateien auswählen', filetypes=[('Alle Dateien', '*')])
    if not files: return
    out = filedialog.askdirectory(title='Optional: Exportordner für Tiefenbilder auswählen; Abbrechen = nur prüfen') or None
    button.config(state='disabled'); append('\nPrüfe Dateien …\n')
    def work():
        for p in files:
            try: result = inspect(p, out)
            except Exception as exc: result = {'file': p, 'status': 'Fehler', 'detail': str(exc)}
            rendered = json.dumps(result, ensure_ascii=False, indent=2) + '\n\n'
            root.after(0, append, rendered)
        root.after(0, lambda: button.config(state='normal'))
    threading.Thread(target=work, daemon=True).start()
button = tk.Button(bar, text='Originaldateien öffnen', command=choose, bg='#73e0b9', fg='#101c19', padx=12, pady=8); button.pack(side='left')
tk.Label(bar, text='HEIC · JPEG · RAW · MOV · MP4 · weitere', fg='#aabfb9', bg='#101b22').pack(side='left', padx=16)
root.mainloop()
