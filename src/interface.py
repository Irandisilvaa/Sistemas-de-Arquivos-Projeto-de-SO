import tkinter as tk
from tkinter import simpledialog, messagebox, ttk, filedialog
from filesystem import DirectoryNode, FileNode, MAX_DISK_SIZE, fs
import copy

# --- Inicializa a raiz C: ---
if not hasattr(fs, 'root') or fs.root is None:
    fs.root = DirectoryNode("C:")
    fs.cwd = fs.root
    
    # Adiciona a Lixeira se ela não existir
    if "Lixeira" not in [n.name for n in fs.root.children]:
        fs.mkdir("Lixeira")
        fs.trash = fs.root.get_child("Lixeira")
    else:
        fs.trash = fs.root.get_child("Lixeira")


# ---------------- Função auxiliar ----------------
def exists_in_tree(node: DirectoryNode, name: str) -> bool:
    """Verifica se já existe um arquivo ou pasta com o mesmo nome em toda a árvore a partir do nó dado."""
    if node.name == name:
        return True
    for child in node.children:
        if child.name == name:
            return True
        if isinstance(child, DirectoryNode):
            if exists_in_tree(child, name):
                return True
    return False


# ---------------- Classe FileExplorer ----------------
class FileExplorer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Explorador de Arquivos K-ária")
        self.state("zoomed")
        self.configure(bg="#e6e6e6")
        
        # Variável para armazenar o nó copiado
        self.copied_node = None

        # --- Barra superior ---
        self.top_frame = tk.Frame(self, bg="#2f3640", pady=5)
        self.top_frame.pack(fill="x")

        btn_style = {
            "bg": "#40739e", "fg": "white", "relief": "flat",
            "activebackground": "#487eb0", "activeforeground": "white",
            "width": 12, "font": ("Segoe UI", 10, "bold"), "bd": 0
        }
        
        self.paste_btn_style_active = {**btn_style, "bg": "#6a89cc"}
        self.paste_btn_style_disabled = {**btn_style}

        left_frame = tk.Frame(self.top_frame, bg="#2f3640")
        left_frame.pack(side="left", padx=5)
        tk.Button(left_frame, text="📁 Criar Pasta", command=self.mkdir, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="📝 Criar Arquivo", command=self.touch, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="🗑️ Remover", command=self.rm, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="⬆️ Voltar", command=self.cd_up, **btn_style).pack(side="left", padx=3)

        self.paste_btn = tk.Button(left_frame, text="📋 Colar", command=self.paste_node, **self.paste_btn_style_disabled, state="disabled")
        self.paste_btn.pack(side="left", padx=3)
        
        # Barra de pesquisa
        right_frame = tk.Frame(self.top_frame, bg="#2f3640")
        right_frame.pack(side="right", padx=10)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(right_frame, textvariable=self.search_var, width=25,
                                font=("Segoe UI", 10), relief="flat", bg="#f1f2f6")
        search_entry.pack(side="left", ipady=3, padx=(0,5))
        search_btn = tk.Button(right_frame, text="🔍", font=("Segoe UI", 12), bg="#f1f2f6",
                               relief="flat", command=self.search)
        search_btn.pack(side="left")

        # Caminho atual
        self.path_label = tk.Label(self, text="C:/", font=("Consolas", 12, "bold"), fg="#1a73e8", bg="#e6e6e6")
        self.path_label.pack(fill="x", pady=4, padx=10)

        # Uso de disco
        self.disk_label = tk.Label(self, text="", font=("Consolas", 10), bg="#e6e6e6", fg="#333333")
        self.disk_label.pack(fill="x", pady=2, padx=10)
        self.disk_progress = ttk.Progressbar(self, orient="horizontal", length=450, mode="determinate")
        self.disk_progress.pack(pady=2, padx=10)

        # Frame principal com scroll
        self.main_frame = tk.Frame(self, bg="#e6e6e6")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.canvas = tk.Canvas(self.main_frame, bg="#e6e6e6", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#e6e6e6")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.refresh()

    # -------------------- Funções de interface --------------------
    def refresh(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Atualiza caminho
        path_nodes = []
        node = fs.cwd
        while node and node.parent:
            path_nodes.insert(0, node.name)
            node = node.parent
        full_path = "C:/" + "/".join(path_nodes) if path_nodes else "C:/"
        self.path_label.config(text=full_path)

        # Atualiza uso de disco
        uso_atual = fs.get_disk_usage()
        self.disk_label.config(text=f"Uso de disco: {uso_atual}/{MAX_DISK_SIZE} bytes")
        self.disk_progress['value'] = (uso_atual / MAX_DISK_SIZE) * 100

        for node in fs.cwd.children:
            frame = tk.Frame(self.scrollable_frame, bg="#ffffff", bd=0, relief="flat")
            frame.pack(fill="x", pady=2, padx=2)
            if isinstance(node, DirectoryNode):
                b = tk.Button(frame, text=f"📁 {node.name}", anchor="w", font=("Consolas", 11, "bold"),
                              bg="#cce5ff", fg="#003366", relief="flat",
                              activebackground="#99ccff", command=lambda n=node: self.open_dir(n))
                b.pack(fill="x", padx=5, pady=2)
            else:
                b = tk.Button(frame, text=f"{node.name} ({getattr(node, 'size', 0)} bytes)", anchor="w",
                              font=("Consolas", 11), bg="#e6ffe6", fg="#004d00", relief="flat",
                              activebackground="#ccffcc", command=lambda n=node: self.show_info(n))
                b.pack(fill="x", padx=5, pady=2)

        # Atualiza botão de colar
        if self.copied_node is None:
            self.paste_btn.config(state="disabled", **self.paste_btn_style_disabled)
        else:
            self.paste_btn.config(state="normal", **self.paste_btn_style_active)

    # Abre diretório
    def open_dir(self, node):
        fs.cwd = node
        self.refresh()

    # Mostra info
    def show_info(self, node):
        info = fs.stat(node.name)
        text = "\n".join(f"{k}: {v}" for k, v in info.items())
        info_win = tk.Toplevel(self)
        info_win.title(f"Informações: {node.name}")
        info_label = tk.Label(info_win, text=text, justify="left", font=("Consolas", 10))
        info_label.pack(padx=10, pady=10)

        # Botão copiar
        def copy_node():
            self.copied_node = node
            messagebox.showinfo("Copiado", f"'{node.name}' foi copiado. Vá para a pasta de destino e clique em 'Colar'.")
            info_win.destroy()
            self.refresh()
        copy_btn = tk.Button(info_win, text="📄 Copiar", command=copy_node, bg="#e5e5ff", fg="black")
        copy_btn.pack(pady=5)

    # Criar pasta
    def mkdir(self):
        name = simpledialog.askstring("Criar Pasta", "Nome da pasta:")
        if not name:
            return
        if exists_in_tree(fs.root, name):
            messagebox.showerror("Erro", f"Já existe um arquivo ou pasta chamado '{name}' na árvore!")
            return
        try:
            fs.mkdir(name)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        self.refresh()

    # Criar arquivo simples
    def touch(self):
        name = simpledialog.askstring("Criar Arquivo", "Nome do arquivo:")
        if not name:
            return
        size = simpledialog.askinteger("Tamanho do arquivo", "Tamanho em bytes:", minvalue=0)
        if size is None:
            return
        try:
            fs.touch(name, size)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        self.refresh()

    # Remover
    def rm(self):
        selected = simpledialog.askstring("Remover", "Nome do arquivo ou pasta:")
        if not selected:
            return
        node = None
        for n in fs.cwd.children:
            if n.name == selected:
                node = n
                break
        if node is None:
            messagebox.showerror("Erro", f"Nó '{selected}' não encontrado em {fs.cwd.path}")
            return
        try:
            if fs.cwd == fs.trash:
                fs.rm(node.name, to_trash=False)
            else:
                fs.rm(node.name, to_trash=True)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        self.refresh()

    # Voltar
    def cd_up(self):
        try:
            fs.cd("..")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        self.refresh()

    # Pesquisa
    def search(self):
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Pesquisa", "Digite um nome para pesquisar!")
            return
        results = []

        def recursive_search(node, path=""):
            if query.lower() in node.name.lower():
                results.append((node, path + "/" + node.name if path else "/" + node.name))
            if isinstance(node, DirectoryNode):
                for child in node.children:
                    recursive_search(child, path + "/" + node.name if path else "/" + node.name)

        recursive_search(fs.cwd)
        if not results:
            messagebox.showinfo("Pesquisa", f"Nenhum resultado encontrado para '{query}'")
            return

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        for node, full_path in results:
            frame = tk.Frame(self.scrollable_frame, bg="#ffffcc", bd=1, relief="solid")
            frame.pack(fill="x", pady=2, padx=2)
            label = tk.Label(frame, text=f"{node.name} - {full_path}", anchor="w", bg="#ffffcc")
            label.pack(side="left", padx=5, pady=2, fill="x", expand=True)
            def go_to(n=node):
                fs.cwd = n.parent if n.parent else fs.root
                self.refresh()
                messagebox.showinfo("Navegar", f"Você foi para o diretório de '{n.name}'")
            btn = tk.Button(frame, text="Ir para o local do arquivo", command=go_to, bg="#cce5ff")
            btn.pack(side="right", padx=5, pady=2)

    # -------------------- Colar --------------------
    def paste_node(self):
        if not self.copied_node:
            messagebox.showerror("Erro", "Nenhum arquivo ou pasta para colar.")
            return
        try:
            new_node = copy.deepcopy(self.copied_node)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao copiar o nó: {e}")
            return

        # Ajuste de nome para evitar duplicidade
        original_name = new_node.name
        new_name = original_name
        counter = 1
        while new_name in [child.name for child in fs.cwd.children]:
            new_name = f"{original_name} - Cópia({counter})"
            counter += 1
        new_node.name = new_name
        new_node.parent = fs.cwd
        fs.cwd.children.append(new_node)

        # --- Atualiza o uso de disco corretamente ---
        def increment_disk_usage(node):
            if isinstance(node, FileNode):
                fs.total_disk_usage += node.size
            elif isinstance(node, DirectoryNode):
                for child in node.children:
                    increment_disk_usage(child)

        increment_disk_usage(new_node)

        self.copied_node = None
        self.refresh()
        self.update_idletasks()


# -------------------- Main --------------------
if __name__ == "__main__":
    app = FileExplorer()
    app.mainloop()
