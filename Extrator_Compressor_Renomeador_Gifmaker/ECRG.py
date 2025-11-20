import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog, messagebox
from PIL import Image
import cv2
import os
import threading
import re
import shutil
import io
import time

# --- Funções Auxiliares Gerais ---
# Ordenação Natural: Garante que 'frame_2.jpg' venha antes de 'frame_10.jpg'
def natural_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

# --- Formatadores ---
def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.1f} {power_labels[n]}B"

def format_time(seconds):
    if seconds < 60: return f"{int(seconds)}s"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{int(h)}h {int(m)}m {int(s)}s"
    return f"{int(m)}m {int(s)}s"

class AppPipelineMonocromatica:
    def __init__(self, root):
        self.root = root
        self.root.title("Processador de mídia")
        self.root.geometry("700x1000")
        
        self.style = ttk.Style()
        self.style.configure('Bold.Secondary.TButton', font=('Helvetica', 11, 'bold'))

        # Variáveis de Controle (Checkboxes e Inputs)
        self.chk_extract = ttk.BooleanVar(value=False)
        self.chk_compress = ttk.BooleanVar(value=True)
        self.chk_rename = ttk.BooleanVar(value=True)
        self.chk_gif = ttk.BooleanVar(value=True)
        
        self.src_path = ttk.StringVar()
        self.dest_path = ttk.StringVar()
        self.is_video_source = False
        self.progress_var = ttk.DoubleVar(value=0)

        # --- CONSTRUÇÃO DA UI ---
        self._criar_cabecalho()
        self._criar_secao_diretorios()
        self._criar_secao_configuracoes()
        self._criar_painel_execucao()
        
        # Define o estado inicial da UI (bloqueios e regras)
        self.toggle_ui()
        self.ao_mudar_resolucao(None)
        
    # ... [Métodos de construção visual, focando na lógica] ...

    def _criar_cabecalho(self):
        frm = ttk.Frame(self.root, padding=20)
        frm.pack(fill=X)
        lbl = ttk.Label(frm, text="Processador de mídia", font=("Helvetica", 16, "bold"))
        lbl.pack(fill=X, pady=5, anchor="center")

    def _criar_secao_diretorios(self):
        lf = ttk.Labelframe(self.root, text="📂 Origem e Destino", padding=15, bootstyle="bold")
        lf.pack(fill=X, padx=20, pady=10)

        frm_src = ttk.Frame(lf)
        frm_src.pack(fill=X, pady=5)
        ttk.Label(frm_src, text="Fonte:", width=8).pack(side=LEFT)
        self.entry_src = ttk.Entry(frm_src, textvariable=self.src_path, state="readonly")
        self.entry_src.pack(side=LEFT, fill=X, expand=YES, padx=5)
        ttk.Button(frm_src, text="🎞️ Vídeo", bootstyle="bold", command=self.sel_video_source).pack(side=LEFT, padx=2)
        ttk.Button(frm_src, text="📁 Pasta", bootstyle="bold", command=self.sel_folder_source).pack(side=LEFT)

        frm_dest = ttk.Frame(lf)
        frm_dest.pack(fill=X, pady=5)
        ttk.Label(frm_dest, text="Destino:", width=8).pack(side=LEFT)
        ttk.Entry(frm_dest, textvariable=self.dest_path, state="readonly").pack(side=LEFT, fill=X, expand=YES, padx=5)
        ttk.Button(frm_dest, text="📂 Selecionar", bootstyle="bold", command=self.sel_dest).pack(side=LEFT)

    def _criar_secao_configuracoes(self):
        container = ttk.Frame(self.root, padding=(20, 0))
        container.pack(fill=BOTH, expand=YES)

        # === EXTRATOR ===
        lf_ext = ttk.Labelframe(container, text="Extrator", padding=10, bootstyle="bold")
        lf_ext.pack(fill=X, pady=5)
        
        frm_ext_top = ttk.Frame(lf_ext)
        frm_ext_top.pack(fill=X)
        self.widget_chk_extract = ttk.Checkbutton(frm_ext_top, text="Ativar Extração", variable=self.chk_extract, 
                                                  bootstyle="secondary-round-toggle", command=self.toggle_ui)
        self.widget_chk_extract.pack(side=LEFT)
        ttk.Label(frm_ext_top, text=" |  Intervalo (frames):").pack(side=LEFT, padx=(15, 5))
        self.ext_interval = ttk.Spinbox(frm_ext_top, from_=1, to=600, width=5)
        self.ext_interval.set(5)
        self.ext_interval.pack(side=LEFT)

        # === COMPRESSOR ===
        lf_comp = ttk.Labelframe(container, text="Compressor", padding=10, bootstyle="bold")
        lf_comp.pack(fill=X, pady=5)

        frm_comp_head = ttk.Frame(lf_comp)
        frm_comp_head.pack(fill=X)
        ttk.Checkbutton(frm_comp_head, text="Ativar Compressão", variable=self.chk_compress, 
                        bootstyle="secondary-round-toggle", command=self.toggle_ui).pack(side=LEFT)

        frm_comp_body = ttk.Frame(lf_comp, padding=(0, 10))
        frm_comp_body.pack(fill=X)
        
        # Linha 1: Formato e Porcentagem
        frm_c1 = ttk.Frame(frm_comp_body)
        frm_c1.pack(fill=X, pady=2)
        ttk.Label(frm_c1, text="Formato:").pack(side=LEFT)
        self.comp_fmt = ttk.StringVar(value="JPEG")
        self.om_fmt = ttk.Combobox(frm_c1, textvariable=self.comp_fmt, values=["JPEG", "WEBP", "PNG"], state="readonly", width=8)
        self.om_fmt.pack(side=LEFT, padx=5)
        self.om_fmt.bind("<<ComboboxSelected>>", lambda e: self.toggle_ui())

        ttk.Label(frm_c1, text="Meta Tam. (%):").pack(side=LEFT, padx=(15, 5))
        self.comp_pct = ttk.Spinbox(frm_c1, from_=1, to=100, width=5)
        self.comp_pct.set(80)
        self.comp_pct.pack(side=LEFT)

        # Linha 2: Resolução 
        frm_c2 = ttk.Frame(frm_comp_body)
        frm_c2.pack(fill=X, pady=5)
        
        ttk.Label(frm_c2, text="Resolução:").pack(side=LEFT)
        self.res_selection = ttk.StringVar(value="Original")
        self.cb_res = ttk.Combobox(frm_c2, textvariable=self.res_selection, state="readonly", width=22,
                                   values=[
                                       "Original",
                                       "3840x2160 (4K)",
                                       "1920x1080 (Full HD)",
                                       "1280x720 (HD)",
                                       "854x480 (480p)",
                                       "Customizado"
                                   ])
        self.cb_res.pack(side=LEFT, padx=5)
        self.cb_res.bind("<<ComboboxSelected>>", self.ao_mudar_resolucao)

        ttk.Label(frm_c2, text="Manual (L x A):").pack(side=LEFT, padx=(10, 2))
        self.comp_w = ttk.Entry(frm_c2, width=5); self.comp_w.insert(0, "0"); self.comp_w.pack(side=LEFT)
        ttk.Label(frm_c2, text="x").pack(side=LEFT, padx=2)
        self.comp_h = ttk.Entry(frm_c2, width=5); self.comp_h.insert(0, "0"); self.comp_h.pack(side=LEFT)


        # === ORDENADOR E GIF ===
        frm_row = ttk.Frame(container)
        frm_row.pack(fill=X, pady=5)

        lf_ord = ttk.Labelframe(frm_row, text="Renomear", padding=10, bootstyle="bold")
        lf_ord.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 5))
        ttk.Checkbutton(lf_ord, text="Ativar", variable=self.chk_rename, bootstyle="secondary-round-toggle", command=self.toggle_ui).pack(anchor=W)
        ttk.Label(lf_ord, text="Prefixo:").pack(anchor=W, pady=(5,0))
        self.ord_prefix = ttk.Entry(lf_ord); self.ord_prefix.insert(0, "frame_"); self.ord_prefix.pack(fill=X)

        lf_gif = ttk.Labelframe(frm_row, text="GIF Maker", padding=10, bootstyle="bold")
        lf_gif.pack(side=LEFT, fill=BOTH, expand=YES, padx=(5, 0))
        ttk.Checkbutton(lf_gif, text="Criar GIF", variable=self.chk_gif, bootstyle="secondary-round-toggle", command=self.toggle_ui).pack(anchor=W)
        frm_gif_in = ttk.Frame(lf_gif)
        frm_gif_in.pack(fill=X, pady=(5,0))
        ttk.Label(frm_gif_in, text="ms:").pack(side=LEFT)
        self.gif_dur = ttk.Entry(frm_gif_in, width=5); self.gif_dur.insert(0, "67"); self.gif_dur.pack(side=LEFT, padx=5)
        ttk.Label(frm_gif_in, text="Nome:").pack(side=LEFT)
        self.gif_name = ttk.Entry(frm_gif_in, width=10); self.gif_name.insert(0, "final.gif"); self.gif_name.pack(side=LEFT, padx=5)

    def _criar_painel_execucao(self):
        frm = ttk.Frame(self.root, padding=(20, 2, 20, 20))
        frm.pack(fill=BOTH, expand=YES)

        self.btn_start = ttk.Button(frm, text="🚀 INICIAR PROCESSAMENTO", bootstyle="bold", command=self.start_thread)
        self.btn_start.pack(fill=X, ipady=5)

        frm_info = ttk.Frame(frm)
        frm_info.pack(fill=X, pady=(10, 0))
        self.lbl_status = ttk.Label(frm_info, text="Aguardando...", font=("Arial", 9, "bold"))
        self.lbl_status.pack(side=LEFT)
        self.lbl_eta = ttk.Label(frm_info, text="", font=("Arial", 9), bootstyle="secondary")
        self.lbl_eta.pack(side=RIGHT)
        
        self.progress = ttk.Progressbar(frm, variable=self.progress_var, maximum=100, bootstyle="secondary-striped")
        self.progress.pack(fill=X, pady=(0, 10))

        self.log_area = ScrolledText(frm, height=15, font=("Consolas", 9))
        self.log_area.pack(fill=BOTH, expand=YES)
        self.log_area.configure(state='disabled')

    # --- LOGICA DA COMBOBOX DE RESOLUÇÃO ---
    def ao_mudar_resolucao(self, event):
        """ Preenche automaticamente W e H baseado no preset """
        escolha = self.res_selection.get()
        
        # Se a compressão estiver desligada, ignora
        if not self.chk_compress.get():
            return

        if escolha == "Original":
            self.comp_w.delete(0, END); self.comp_w.insert(0, "0")
            self.comp_h.delete(0, END); self.comp_h.insert(0, "0")
            self.comp_w.configure(state='disabled')
            self.comp_h.configure(state='disabled')
        
        elif escolha == "Customizado":
            self.comp_w.configure(state='normal')
            self.comp_h.configure(state='normal')
        
        else:
            # Extrai números da string (ex: "1920x1080 (Full HD)")
            # Pega a primeira parte "1920x1080" e divide
            res_part = escolha.split(" ")[0]
            w, h = res_part.split("x")
            
            self.comp_w.configure(state='normal') # Habilita p/ escrever
            self.comp_h.configure(state='normal')
            
            self.comp_w.delete(0, END); self.comp_w.insert(0, w)
            self.comp_h.delete(0, END); self.comp_h.insert(0, h)
            
            self.comp_w.configure(state='disabled') # Trava de novo
            self.comp_h.configure(state='disabled')

    def aplicar_regras_fonte(self, is_video):
        self.is_video_source = is_video
        if is_video:
            self.chk_extract.set(True)
            self.widget_chk_extract.configure(state='disabled')
            self.ext_interval.configure(state='normal')
        else:
            self.chk_extract.set(False)
            self.widget_chk_extract.configure(state='disabled')
            self.ext_interval.configure(state='disabled')

    def sel_video_source(self):
        f = filedialog.askopenfilename(filetypes=[("Vídeo", "*.mp4 *.avi *.mkv *.mov")])
        if f:
            self.src_path.set(f)
            self.aplicar_regras_fonte(True)
            self.toggle_ui()

    def sel_folder_source(self):
        d = filedialog.askdirectory()
        if d:
            self.src_path.set(d)
            self.aplicar_regras_fonte(False)
            self.toggle_ui()

    def sel_dest(self):
        d = filedialog.askdirectory()
        if d: self.dest_path.set(d)

    def toggle_ui(self):
        def set_state(widgets, active):
            state = 'normal' if active else 'disabled'
            for w in widgets: w.configure(state=state)

        is_comp = self.chk_compress.get()
        is_png = (self.comp_fmt.get() == "PNG")
        
        # Lógica de Resolução
        if is_comp:
            self.cb_res.configure(state='readonly') # Habilita combobox
            # Chama a função para garantir que os campos manuais sigam a combobox
            self.ao_mudar_resolucao(None)
        else:
            self.cb_res.configure(state='disabled')
            self.comp_w.configure(state='disabled')
            self.comp_h.configure(state='disabled')

        if is_comp and not is_png: self.comp_pct.configure(state='normal')
        else: self.comp_pct.configure(state='disabled')

        set_state([self.ord_prefix], self.chk_rename.get())
        set_state([self.gif_dur, self.gif_name], self.chk_gif.get())

    def log(self, msg):
        self.log_area.configure(state='normal')
        self.log_area.insert(END, msg + "\n")
        self.log_area.see(END)
        self.log_area.configure(state='disabled')

    def update_status(self, status, progress_val, start_time_stage, current_item_idx, total_items_stage):
        self.lbl_status.config(text=status)
        self.progress_var.set(progress_val)
        if total_items_stage > 0 and current_item_idx > 0:
            elapsed = time.time() - start_time_stage
            rate = current_item_idx / elapsed
            remaining_items = total_items_stage - current_item_idx
            eta_seconds = remaining_items / rate if rate > 0 else 0
            self.lbl_eta.config(text=f"ETA Etapa: {format_time(eta_seconds)}")
        else:
            self.lbl_eta.config(text="Calculando ETA...")
        self.root.update()

    def start_thread(self):
        src, dest = self.src_path.get(), self.dest_path.get()
        if not src or not dest: return messagebox.showerror("Erro", "Defina Fonte e Destino!")
        self.btn_start.configure(state='disabled', text="⏳ Processando...", bootstyle="secondary")
        self.progress_var.set(0)
        self.log_area.configure(state='normal'); self.log_area.delete('1.0', END); self.log_area.configure(state='disabled')
        threading.Thread(target=self.run_pipeline, args=(src, dest), daemon=True).start()

    def redimensionar_img(self, img, target_w, target_h):
        if target_w == 0 and target_h == 0: return img
        if target_w > 0 and target_h > 0: return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        elif target_w > 0:
            ratio = target_w / float(img.width)
            return img.resize((target_w, int(float(img.height) * ratio)), Image.Resampling.LANCZOS)
        elif target_h > 0:
            ratio = target_h / float(img.height)
            return img.resize((int(float(img.width) * ratio), target_h), Image.Resampling.LANCZOS)
        return img

    def encontrar_qualidade(self, img, fmt, target_bytes):
        min_q, max_q, melhor_q = 1, 100, 0
        buffer = io.BytesIO()
        while min_q <= max_q:
            mid_q = (min_q + max_q) // 2
            buffer.seek(0); buffer.truncate(0)
            img.save(buffer, format=fmt, quality=mid_q)
            if buffer.tell() <= target_bytes:
                melhor_q = mid_q
                min_q = mid_q + 1
            else:
                max_q = mid_q - 1
        return max(1, melhor_q)

    def processar_imagem(self, pil_img, out_path, fmt, pct_target, orig_size=None):
        try: w, h = int(self.comp_w.get()), int(self.comp_h.get())
        except: w, h = 0, 0
        
        pil_img = self.redimensionar_img(pil_img, w, h)
        if pil_img.mode == 'RGBA' and fmt != 'PNG':
            bg = Image.new("RGB", pil_img.size, (255,255,255))
            bg.paste(pil_img, mask=pil_img.split()[3])
            pil_img = bg
        elif pil_img.mode != 'RGB' and fmt == 'JPEG':
            pil_img = pil_img.convert('RGB')

        if fmt == "PNG":
            pil_img.save(out_path, "PNG", optimize=True, compress_level=9)
            return "PNG Lossless"
        else:
            if orig_size:
                target = orig_size * (pct_target / 100.0)
                q = self.encontrar_qualidade(pil_img, fmt, target)
            else:
                q = int(pct_target)
            if fmt == "JPEG": pil_img.save(out_path, "JPEG", quality=q, optimize=True)
            elif fmt == "WEBP": pil_img.save(out_path, "WEBP", quality=q)
            return f"Q={q}"

    def run_pipeline(self, source_path, dest_path):
        try:
            self.log("=== INICIANDO PROCESSAMENTO ===")
            start_time_global = time.time()
            
            fmt = self.comp_fmt.get()
            try: pct = int(self.comp_pct.get())
            except: pct = 80

            total_weight = 0
            if self.is_video_source or True: total_weight += 50
            if self.chk_rename.get(): total_weight += 10
            if self.chk_gif.get(): total_weight += 40
            
            current_progress_base = 0
            
            # --- FASE 1: PROCESSAMENTO ---
            phase_weight = 50
            start_time_phase = time.time()
            
            if self.is_video_source:
                try: interval = int(self.ext_interval.get())
                except: interval = 5
                cap = cv2.VideoCapture(source_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                estimated_output = total_frames // interval
                
                self.log(f"VÍDEO: {total_frames} frames. Estimativa: {estimated_output} saídas.")
                
                count, saved = 0, 0
                while True:
                    ret, frame = cap.read()
                    if not ret: break
                    if count % interval == 0:
                        fname = f"temp_{saved}.{fmt.lower()}"
                        final = os.path.join(dest_path, fname)
                        info_log = ""
                        if self.chk_compress.get():
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_img = Image.fromarray(frame_rgb)
                            info = self.processar_imagem(pil_img, final, fmt, pct, None)
                            sz = os.path.getsize(final)
                            info_log = f"-> {info} | {format_bytes(sz)}"
                        else:
                            cv2.imwrite(final, frame)
                            sz = os.path.getsize(final)
                            info_log = f"(Raw) | {format_bytes(sz)}"
                        
                        self.log(f"Frame {saved}: {info_log}")
                        saved += 1
                        if estimated_output > 0:
                            prog_phase = (saved / estimated_output) * phase_weight
                            self.update_status(f"Extraindo Frame {saved}...", current_progress_base + prog_phase, start_time_phase, saved, estimated_output)
                    count += 1
                cap.release()

            else: # PASTA
                files = [f for f in os.listdir(source_path) if f.lower().endswith(('.jpg','.png','.jpeg'))]
                total_files = len(files)
                self.log(f"PASTA: {total_files} imagens.")
                
                for idx, f in enumerate(files):
                    inp = os.path.join(source_path, f)
                    out = os.path.join(dest_path, os.path.splitext(f)[0] + f".{fmt.lower()}")
                    
                    sz_orig = os.path.getsize(inp)
                    info_log = ""
                    if self.chk_compress.get():
                        with Image.open(inp) as img:
                            info = self.processar_imagem(img, out, fmt, pct, sz_orig)
                        sz_new = os.path.getsize(out)
                        reduc = (1 - sz_new/sz_orig) * 100
                        info_log = f"{format_bytes(sz_orig)}->{format_bytes(sz_new)} (-{reduc:.1f}%) [{info}]"
                    else:
                        shutil.copy2(inp, out)
                        info_log = "Copiado"
                    
                    self.log(f"{f}: {info_log}")
                    prog_phase = ((idx + 1) / total_files) * phase_weight
                    self.update_status(f"Processando {idx+1}/{total_files}...", current_progress_base + prog_phase, start_time_phase, idx+1, total_files)
            
            current_progress_base += phase_weight

            # --- FASE 2: ORDENAÇÃO ---
            if self.chk_rename.get():
                phase_weight = 10
                start_time_phase = time.time()
                prefix = self.ord_prefix.get()
                files = sorted([f for f in os.listdir(dest_path) if f.lower().endswith(('.jpg','.png','.webp','.jpeg'))], key=natural_sort_key)
                total_files = len(files)
                
                temps = []
                for idx, f in enumerate(files):
                    old = os.path.join(dest_path, f)
                    tmp = old + ".tmp_srt"
                    os.rename(old, tmp)
                    temps.append((tmp, os.path.splitext(f)[1]))
                    if idx % 10 == 0: self.update_status("Ordenando (Temp)...", current_progress_base + (idx/total_files * 5), start_time_phase, idx, total_files*2)
                
                for i, (tmp, ext) in enumerate(temps):
                    new_name = f"{prefix}{i}{ext}"
                    os.rename(tmp, os.path.join(dest_path, new_name))
                    self.log(f"Renomeado: {new_name}")
                    if i % 5 == 0: self.update_status(f"Renomeando...", current_progress_base + 5 + (i/total_files * 5), start_time_phase, len(files)+i, total_files*2)
                
                current_progress_base += phase_weight

            # --- FASE 3: GIF ---
            if self.chk_gif.get():
                phase_weight = 40
                start_time_phase = time.time()
                try: dur = int(self.gif_dur.get())
                except: dur = 67
                gname = self.gif_name.get()
                if not gname.endswith(".gif"): gname += ".gif"
                
                files = sorted([f for f in os.listdir(dest_path) if f.lower().endswith(('.jpg','.png','.webp','.jpeg'))], key=natural_sort_key)
                total_files = len(files)
                
                if files:
                    frames = []
                    self.log(f"Montando GIF ({total_files} frames)...")
                    for idx, f in enumerate(files):
                        try:
                            i = Image.open(os.path.join(dest_path, f))
                            if i.mode != 'RGB': i = i.convert('RGB')
                            frames.append(i)
                            self.log(f"Carregando: {f}")
                        except: pass
                        prog_phase = (idx / total_files) * (phase_weight * 0.8)
                        self.update_status(f"GIF: Lendo {idx+1}/{total_files}...", current_progress_base + prog_phase, start_time_phase, idx+1, total_files)
                    
                    if frames:
                        self.log("Salvando GIF no disco...")
                        self.update_status("Salvando GIF...", 95, start_time_phase, total_files, total_files)
                        frames[0].save(os.path.join(dest_path, gname), save_all=True, append_images=frames[1:], duration=dur, loop=0, optimize=True)
                        self.log(f"GIF Pronto: {gname}")
                
                current_progress_base += phase_weight

            self.progress_var.set(100)
            total_time = time.time() - start_time_global
            self.lbl_status.config(text=f"Concluído em {format_time(total_time)}!")
            self.lbl_eta.config(text="")
            self.log("=== PROCESSO FINALIZADO ===")
            messagebox.showinfo("Sucesso", "Processamento finalizado com sucesso!")

        except Exception as e:
            self.log(f"ERRO: {str(e)}")
            self.lbl_status.config(text="Erro Fatal!")
            messagebox.showerror("Erro", str(e))
        
        self.btn_start.configure(state='normal', text="🚀 INICIAR PROCESSAMENTO", bootstyle="secondary")

if __name__ == "__main__":
    app = ttk.Window(themename="darkly")
    AppPipelineMonocromatica(app)
    app.mainloop()