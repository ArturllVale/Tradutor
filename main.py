#  __                       |
# |  |   _ _ _____ ___ ___  |
# |  |__| | |     | -_|   | |
# |_____|___|_|_|_|___|_|_| |
#         lumen#0110        |
#        2024 - 2025        |
#___________________________|

import os
import asyncio
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from src.api.translation import translate_text
from src.database.translator import Database


class TradutorApp:
    def __init__(self, master):
        self.master = master
        master.title("Tradutor de Ragnarok")

        self.database = Database("database.db")  # Inicializa o banco de dados

        self.label_texto = tk.Label(master, text="Texto:")
        self.label_texto.grid(row=0, column=0, padx=5, pady=5)

        self.texto_original = tk.Text(master, height=10, width=50)
        self.texto_original.grid(row=1, column=0, padx=5, pady=5)

        self.botao_traduzir = tk.Button(master, text="Traduzir", command=self.traduzir_texto)
        self.botao_traduzir.grid(row=2, column=0, padx=5, pady=5)

        self.label_traducao = tk.Label(master, text="Tradução:")
        self.label_traducao.grid(row=0, column=1, padx=5, pady=5)

        self.texto_traduzido = tk.Text(master, height=10, width=50)
        self.texto_traduzido.grid(row=1, column=1, padx=5, pady=5)

        self.botao_salvar = tk.Button(master, text="Salvar Tradução", command=self.salvar_traducao)
        self.botao_salvar.grid(row=2, column=1, padx=5, pady=5)

        # Barra de Progresso
        self.progress_bar = ttk.Progressbar(master, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=3, column=0, columnspan=2, pady=10)
        self.progress_bar["value"] = 0

    def traduzir_texto(self):
        texto = self.texto_original.get("1.0", tk.END)
        if texto.strip():
            try:
                self.progress_bar["value"] = 0  # Reset progress bar
                self.master.update_idletasks()

                traducao = translate_text(texto, self.progress_bar, self.master)  # Pass progress bar and master

                self.texto_traduzido.delete("1.0", tk.END)
                self.texto_traduzido.insert(tk.END, traducao)

                self.progress_bar["value"] = 100  # Complete progress bar
                self.master.update_idletasks()

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao traduzir: {e}")
        else:
            messagebox.showwarning("Aviso", "Insira um texto para traduzir.")

    def salvar_traducao(self):
        texto_original = self.texto_original.get("1.0", tk.END).strip()
        texto_traduzido = self.texto_traduzido.get("1.0", tk.END).strip()

        if texto_original and texto_traduzido:
            try:
                self.database.salvar_traducao(texto_original, texto_traduzido)
                messagebox.showinfo("Sucesso", "Tradução salva com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar tradução: {e}")
        else:
            messagebox.showwarning("Aviso", "Insira o texto original e a tradução para salvar.")

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    root = tk.Tk()
    app = TradutorApp(root)
    root.mainloop()
