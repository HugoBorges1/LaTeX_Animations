import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image
import os
import threading
import re
import sys

# --- Função Auxiliar Global (Ordenação Natural) ---
def natural_sort_key(s):
    """ Ajuda a ordenar arquivos como: img_1, img_2, img_10 (em vez de 1, 10, 2) """
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

# =============================================================================
# ABA 1: COMPRESSOR E CONVERSOR
# =============================================================================
class TabCompressor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill='both', expand=True)
        
        self.pasta_origem = tk.StringVar()
        self.pasta_destino = tk.StringVar()
        self.formato_saida = tk.StringVar(value="JPEG")

        # UI
        self._criar_ui()

    def _criar_ui(self):
        # Origem
        fr_origem = tk.Frame(self, pady=5)
        fr_origem.pack(fill='x', padx=10, pady=(10, 5))
        tk.Label(fr_origem, text="Origem:", width=10, anchor='w').pack(side=tk.LEFT)
        tk.Entry(fr_origem, textvariable=self.pasta_origem, state='disabled').pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        tk.Button(fr_origem, text="...", command=self.selecionar_origem).pack(side=tk.LEFT)

        # Destino
        fr_destino = tk.Frame(self, pady=5)
        fr_destino.pack(fill='x', padx=10)
        tk.Label(fr_destino, text="Destino:", width=10, anchor='w').pack(side=tk.LEFT)
        tk.Entry(fr_destino, textvariable=self.pasta_destino, state='disabled').pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        tk.Button(fr_destino, text="...", command=self.selecionar_destino).pack(side=tk.LEFT)

        # Opções
        fr_opts = tk.LabelFrame(self, text="Configurações", padx=10, pady=5)
        fr_opts.pack(fill='x', padx=10, pady=10)
        
        # Radio Buttons
        tk.Radiobutton(fr_opts, text="JPEG", variable=self.formato_saida, value="JPEG", command=self.atualizar_ui).pack(side=tk.LEFT)
        tk.Radiobutton(fr_opts, text="WEBP", variable=self.formato_saida, value="WEBP", command=self.atualizar_ui).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(fr_opts, text="PNG", variable=self.formato_saida, value="PNG", command=self.atualizar_ui).pack(side=tk.LEFT)

        # Qualidade
        tk.Label(fr_opts, text="|  Qualidade (1-100):").pack(side=tk.LEFT, padx=(10, 5))
        self.entry_qualidade = tk.Entry(fr_opts, width=5)
        self.entry_qualidade.insert(0, "80")
        self.entry_qualidade.pack(side=tk.LEFT)

        # Botão
        self.btn_iniciar = tk.Button(self, text="COMPRIMIR IMAGENS", bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'), pady=8, command=self.iniciar_thread)
        self.btn_iniciar.pack(fill='x', padx=10, pady=5)

        # Log
        self.log_area = scrolledtext.ScrolledText(self, height=10, state='disabled')
        self.log_area.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.atualizar_ui()

    def selecionar_origem(self):
        d = filedialog.askdirectory()
        if d: self.pasta_origem.set(d)

    def selecionar_destino(self):
        d = filedialog.askdirectory()
        if d: self.pasta_destino.set(d)

    def atualizar_ui(self):
        if self.formato_saida.get() == "PNG":
            self.entry_qualidade.config(state='disabled')
        else:
            self.entry_qualidade.config(state='normal')

    def log(self, msg):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def iniciar_thread(self):
        origem = self.pasta_origem.get()
        destino = self.pasta_destino.get()
        if not origem or not destino:
            messagebox.showerror("Erro", "Selecione as pastas.")
            return
        
        formato = self.formato_saida.get()
        qualidade = 0
        if formato != "PNG":
            try:
                qualidade = int(self.entry_qualidade.get())
                if not 1 <= qualidade <= 100: raise ValueError
            except:
                messagebox.showerror("Erro", "Qualidade inválida.")
                return

        self.btn_iniciar.config(state='disabled', text="Processando...")
        self.log_area.config(state='normal'); self.log_area.delete('1.0', tk.END); self.log_area.config(state='disabled')
        
        threading.Thread(target=self.executar, args=(origem, destino, qualidade, formato), daemon=True).start()

    def executar(self, origem, destino, qualidade, formato):
        sucesso, falha = 0, 0
        exts = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")
        nova_ext = f".{formato.lower()}"

        self.log(f"Iniciando compressão para {formato}...")

        for f in os.listdir(origem):
            if f.lower().endswith(exts):
                path_in = os.path.join(origem, f)
                path_out = os.path.join(destino, os.path.splitext(f)[0] + nova_ext)
                
                try:
                    with Image.open(path_in) as img:
                        sz_orig = os.path.getsize(path_in)
                        
                        # Tratamento de cor
                        salvar = img
                        if img.mode == 'RGBA' and formato != 'PNG':
                            salvar = Image.new("RGB", img.size, (255, 255, 255))
                            salvar.paste(img, mask=img.split()[3])
                        elif img.mode != 'RGB' and formato == 'JPEG':
                            salvar = img.convert('RGB')

                        if formato == "JPEG": salvar.save(path_out, "JPEG", quality=qualidade, optimize=True)
                        elif formato == "WEBP": salvar.save(path_out, "WEBP", quality=qualidade)
                        elif formato == "PNG": salvar.save(path_out, "PNG", optimize=True, compress_level=9)

                        sz_new = os.path.getsize(path_out)
                        red = (1 - sz_new/sz_orig) * 100
                        self.log(f"[OK] {f}: {red:.1f}% menor")
                        sucesso += 1
                except Exception as e:
                    self.log(f"[ERRO] {f}: {e}")
                    falha += 1
        
        self.log(f"\nConcluído: {sucesso} sucessos, {falha} falhas.")
        self.after(0, lambda: self.btn_iniciar.config(state='normal', text="COMPRIMIR IMAGENS"))
        self.after(0, lambda: messagebox.showinfo("Fim", "Compressão finalizada!"))


# =============================================================================
# ABA 2: RENOMEADOR EM MASSA
# =============================================================================
class TabRenamer(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill='both', expand=True)
        
        self.pasta_alvo = tk.StringVar()
        self.prefixo = tk.StringVar()
        self._criar_ui()

    def _criar_ui(self):
        fr_pasta = tk.Frame(self, pady=5)
        fr_pasta.pack(fill='x', padx=10, pady=(10, 5))
        tk.Label(fr_pasta, text="Pasta:", width=10, anchor='w').pack(side=tk.LEFT)
        tk.Entry(fr_pasta, textvariable=self.pasta_alvo, state='disabled').pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        tk.Button(fr_pasta, text="...", command=self.selecionar_pasta).pack(side=tk.LEFT)

        fr_pre = tk.Frame(self, pady=5)
        fr_pre.pack(fill='x', padx=10)
        tk.Label(fr_pre, text="Prefixo:", width=10, anchor='w').pack(side=tk.LEFT)
        e = tk.Entry(fr_pre, textvariable=self.prefixo)
        e.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        e.insert(0, "imagem_")

        self.btn_iniciar = tk.Button(self, text="RENOMEAR ARQUIVOS", bg='#D32F2F', fg='white', font=('Arial', 10, 'bold'), pady=8, command=self.iniciar_thread)
        self.btn_iniciar.pack(fill='x', padx=10, pady=10)

        self.log_area = scrolledtext.ScrolledText(self, height=10, state='disabled')
        self.log_area.pack(fill='both', expand=True, padx=10, pady=(0, 10))

    def selecionar_pasta(self):
        d = filedialog.askdirectory()
        if d: self.pasta_alvo.set(d)

    def log(self, msg):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def iniciar_thread(self):
        pasta = self.pasta_alvo.get()
        prefixo = self.prefixo.get().strip()
        
        if not pasta or not prefixo:
            messagebox.showerror("Erro", "Preencha todos os campos.")
            return

        if not messagebox.askyesno("Cuidado", "Isso irá renomear PERMANENTEMENTE os arquivos. Continuar?"):
            return

        self.btn_iniciar.config(state='disabled', text="Processando...")
        self.log_area.config(state='normal'); self.log_area.delete('1.0', tk.END); self.log_area.config(state='disabled')
        
        threading.Thread(target=self.executar, args=(pasta, prefixo), daemon=True).start()

    def executar(self, pasta, prefixo):
        try:
            arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            
            # Passo 1: Temp
            temp_data = []
            for f in arquivos:
                old = os.path.join(pasta, f)
                ext = os.path.splitext(f)[1]
                temp = old + ".tmp_rename"
                os.rename(old, temp)
                temp_data.append((temp, ext))

            # Passo 2: Final
            count = 0
            for temp, ext in temp_data:
                new_name = f"{prefixo}{count}{ext}"
                new_path = os.path.join(pasta, new_name)
                os.rename(temp, new_path)
                self.log(f"Renomeado: {new_name}")
                count += 1
            
            self.log(f"Total: {count} arquivos.")
            self.after(0, lambda: messagebox.showinfo("Sucesso", "Arquivos renomeados!"))

        except Exception as e:
            self.log(f"ERRO FATAL: {e}")
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        
        self.after(0, lambda: self.btn_iniciar.config(state='normal', text="RENOMEAR ARQUIVOS"))


# =============================================================================
# ABA 3: CRIADOR DE GIF
# =============================================================================
class TabGifMaker(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill='both', expand=True)
        
        self.pasta_origem = tk.StringVar()
        self.arquivo_destino = tk.StringVar()
        self.redimensionar = tk.BooleanVar(value=True)
        
        self._criar_ui()

    def _criar_ui(self):
        # Inputs
        fr_in = tk.Frame(self, pady=5)
        fr_in.pack(fill='x', padx=10, pady=(10, 5))
        tk.Label(fr_in, text="Pasta Imagens:", width=12, anchor='w').pack(side=tk.LEFT)
        tk.Entry(fr_in, textvariable=self.pasta_origem, state='disabled').pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        tk.Button(fr_in, text="...", command=self.sel_origem).pack(side=tk.LEFT)

        fr_out = tk.Frame(self, pady=5)
        fr_out.pack(fill='x', padx=10)
        tk.Label(fr_out, text="Salvar GIF:", width=12, anchor='w').pack(side=tk.LEFT)
        tk.Entry(fr_out, textvariable=self.arquivo_destino, state='disabled').pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        tk.Button(fr_out, text="...", command=self.sel_destino).pack(side=tk.LEFT)

        # Configs
        fr_cfg = tk.LabelFrame(self, text="Configurações do GIF", padx=10, pady=5)
        fr_cfg.pack(fill='x', padx=10, pady=5)

        tk.Label(fr_cfg, text="Duração (ms):").pack(side=tk.LEFT)
        self.entry_duracao = tk.Entry(fr_cfg, width=5)
        self.entry_duracao.insert(0, "67")
        self.entry_duracao.pack(side=tk.LEFT, padx=5)

        tk.Checkbutton(fr_cfg, text="Redimensionar Largura para:", variable=self.redimensionar, command=self.toggle_resize).pack(side=tk.LEFT, padx=(15, 0))
        self.entry_largura = tk.Entry(fr_cfg, width=6)
        self.entry_largura.insert(0, "800")
        self.entry_largura.pack(side=tk.LEFT, padx=5)
        tk.Label(fr_cfg, text="px").pack(side=tk.LEFT)

        self.btn_iniciar = tk.Button(self, text="CRIAR GIF", bg='#0277BD', fg='white', font=('Arial', 10, 'bold'), pady=8, command=self.iniciar_thread)
        self.btn_iniciar.pack(fill='x', padx=10, pady=10)

        self.log_area = scrolledtext.ScrolledText(self, height=10, state='disabled')
        self.log_area.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.toggle_resize()

    def toggle_resize(self):
        state = 'normal' if self.redimensionar.get() else 'disabled'
        self.entry_largura.config(state=state)

    def sel_origem(self):
        d = filedialog.askdirectory()
        if d: self.pasta_origem.set(d)

    def sel_destino(self):
        f = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF", "*.gif")])
        if f: self.arquivo_destino.set(f)

    def log(self, msg):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def iniciar_thread(self):
        origem = self.pasta_origem.get()
        destino = self.arquivo_destino.get()
        if not origem or not destino:
            messagebox.showerror("Erro", "Selecione origem e destino.")
            return
        
        try:
            duracao = int(self.entry_duracao.get())
            largura = int(self.entry_largura.get()) if self.redimensionar.get() else 0
        except:
            messagebox.showerror("Erro", "Valores numéricos inválidos.")
            return

        self.btn_iniciar.config(state='disabled', text="Processando...")
        self.log_area.config(state='normal'); self.log_area.delete('1.0', tk.END); self.log_area.config(state='disabled')
        
        threading.Thread(target=self.executar, args=(origem, destino, duracao, largura), daemon=True).start()

    def executar(self, origem, destino, duracao, largura):
        try:
            imgs = [f for f in os.listdir(origem) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            if not imgs: raise Exception("Nenhuma imagem encontrada.")
            
            imgs.sort(key=natural_sort_key)
            frames = []
            
            self.log(f"Processando {len(imgs)} frames...")
            
            for f in imgs:
                path = os.path.join(origem, f)
                with Image.open(path) as img:
                    if largura > 0 and img.width > largura:
                        ratio = largura / float(img.width)
                        h = int(float(img.height) * float(ratio))
                        img = img.resize((largura, h), Image.Resampling.LANCZOS)
                    
                    if img.mode == 'RGBA':
                        bg = Image.new("RGB", img.size, (255,255,255))
                        bg.paste(img, mask=img.split()[3])
                        frames.append(bg)
                    elif img.mode != 'RGB':
                        frames.append(img.convert('RGB'))
                    else:
                        frames.append(img.copy())

            frames[0].save(destino, save_all=True, append_images=frames[1:], duration=duracao, loop=0, optimize=True)
            
            self.log("GIF criado com sucesso!")
            self.after(0, lambda: messagebox.showinfo("Sucesso", "GIF criado!"))

        except Exception as e:
            self.log(f"ERRO: {e}")
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        
        self.after(0, lambda: self.btn_iniciar.config(state='normal', text="CRIAR GIF"))

# =============================================================================
# JANELA PRINCIPAL (APP)
# =============================================================================
class AppPrincipal:
    def __init__(self, root):
        self.root = root
        self.root.title("Caixa de Ferramentas de Imagem")
        self.root.geometry("650x600")

        # Cria o sistema de abas (Notebook)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Cria as abas (instanciando as classes acima)
        self.tab1 = TabCompressor(self.notebook)
        self.tab2 = TabRenamer(self.notebook)
        self.tab3 = TabGifMaker(self.notebook)

        # Adiciona as abas ao notebook
        self.notebook.add(self.tab1, text=" 1. Compressor ")
        self.notebook.add(self.tab2, text=" 2. Renomeador ")
        self.notebook.add(self.tab3, text=" 3. Criador de GIF ")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppPrincipal(root)
    root.mainloop()