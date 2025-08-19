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
    """
    Verifica se já existe um arquivo ou pasta com o mesmo nome
    em toda a árvore a partir do nó dado.
    """
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
        
        # Estilos específicos para o botão de colar
        self.paste_btn_style_active = {
            "bg": "#6a89cc",  # Cor mais clara quando ativo
            "fg": "white",
            "relief": "flat",
            "activebackground": "#487eb0",
            "activeforeground": "white",
            "width": 12,
            "font": ("Segoe UI", 10, "bold"),
            "bd": 0
        }
        self.paste_btn_style_disabled = {
            "bg": "#40739e",  # Cor padrão quando desabilitado
            "fg": "white",
            "relief": "flat",
            "activebackground": "#487eb0",
            "activeforeground": "white",
            "width": 12,
            "font": ("Segoe UI", 10, "bold"),
            "bd": 0
        }

        # Botões principais à esquerda
        left_frame = tk.Frame(self.top_frame, bg="#2f3640")
        left_frame.pack(side="left", padx=5)
        tk.Button(left_frame, text="📁 Criar Pasta", command=self.mkdir, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="📝 Criar Arquivo", command=self.touch, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="🗑️ Remover", command=self.rm, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="⬆️ Voltar", command=self.cd_up, **btn_style).pack(side="left", padx=3)

        # Botão para colar (agora global)
        self.paste_btn = tk.Button(left_frame, text="📋 Colar", command=self.paste_node, **self.paste_btn_style_disabled, state="disabled")
        self.paste_btn.pack(side="left", padx=3)
        
        # Barra de pesquisa separada à direita
        right_frame = tk.Frame(self.top_frame, bg="#2f3640")
        right_frame.pack(side="right", padx=10)

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(right_frame, textvariable=self.search_var, width=25,
                                font=("Segoe UI", 10), relief="flat", bg="#f1f2f6")
        search_entry.pack(side="left", ipady=3, padx=(0,5))

        # Botão da lupa
        search_btn = tk.Button(right_frame, text="🔍", font=("Segoe UI", 12), bg="#f1f2f6",
                               relief="flat", command=self.search)
        search_btn.pack(side="left")

        # --- Caminho atual ---
        self.path_label = tk.Label(self, text="C:/", font=("Consolas", 12, "bold"), fg="#1a73e8", bg="#e6e6e6")
        self.path_label.pack(fill="x", pady=4, padx=10)

        # --- Uso de disco ---
        self.disk_label = tk.Label(self, text="", font=("Consolas", 10), bg="#e6e6e6", fg="#333333")
        self.disk_label.pack(fill="x", pady=2, padx=10)

        self.disk_progress = ttk.Progressbar(self, orient="horizontal", length=450, mode="determinate")
        self.disk_progress.pack(pady=2, padx=10)

        # --- Frame principal com scroll ---
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
        """Atualiza a exibição do explorador de arquivos."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Caminho completo desde a raiz
        path_nodes = []
        node = fs.cwd
        while node and node.parent:
            path_nodes.insert(0, node.name)
            node = node.parent
        full_path = "C:/" + "/".join(path_nodes) if path_nodes else "C:/"
        self.path_label.config(text=full_path)

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
                b = tk.Button(frame, text=f"{node.name} ({node.size} bytes)", anchor="w", font=("Consolas", 11),
                                bg="#e6ffe6", fg="#004d00", relief="flat",
                                activebackground="#ccffcc", command=lambda n=node: self.show_info(n))
                b.pack(fill="x", padx=5, pady=2)
        
        # Habilita ou desabilita o botão de colar e muda a cor para feedback visual
        if self.copied_node is None:
            self.paste_btn.config(state="disabled", **self.paste_btn_style_disabled)
        else:
            self.paste_btn.config(state="normal", **self.paste_btn_style_active)

    def open_dir(self, node):
        """Muda o diretório atual para o nó selecionado."""
        fs.cwd = node
        self.refresh()

    def show_info(self, node):
        """Exibe uma janela com informações sobre o arquivo ou pasta."""
        info = fs.stat(node.name)
        text = "\n".join(f"{k}: {v}" for k, v in info.items())
        info_win = tk.Toplevel(self)
        info_win.title(f"Informações: {node.name}")
        info_label = tk.Label(info_win, text=text, justify="left", font=("Consolas", 10))
        info_label.pack(padx=10, pady=10)

        # --- Se for um arquivo de texto, adicionar botões para abrir e editar ---
        if isinstance(node, FileNode) and isinstance(getattr(node, "content", None), str):
            # Botão Abrir
            def open_text():
                text_win = tk.Toplevel(self)
                text_win.title(f"Conteúdo: {node.name}")
                text_win.geometry("600x400")

                text_box = tk.Text(text_win, wrap="word", width=70, height=20)
                text_box.pack(padx=10, pady=10, fill="both", expand=True)
                text_box.insert("1.0", node.content)
                text_box.config(state="disabled")  # somente leitura

            open_btn = tk.Button(info_win, text="📖 Abrir", command=open_text, bg="#d4edda")
            open_btn.pack(pady=5)

            # Adiciona o botão "Editar" somente se o diretório atual não for a Lixeira
            if fs.cwd != fs.trash:
                def edit_text():
                    edit_win = tk.Toplevel(self)
                    edit_win.title(f"Editar: {node.name}")
                    edit_win.geometry("600x400")

                    text_box = tk.Text(edit_win, wrap="word", width=70, height=20)
                    text_box.pack(padx=10, pady=10, fill="both", expand=True)
                    text_box.insert("1.0", node.content)

                    def save_edit():
                        new_content = text_box.get("1.0", tk.END).rstrip("\n")
                        new_size = len(new_content.encode("utf-8"))

                        try:
                            # Chama a função do sistema de arquivos para atualizar o tamanho
                            fs.update_file_size(node, new_size)
                            node.content = new_content
                            edit_win.destroy()
                            self.refresh()
                            messagebox.showinfo("Sucesso", f"Arquivo '{node.name}' atualizado com sucesso!")
                        except Exception as e:
                            messagebox.showerror("Erro", str(e))

                    save_btn = tk.Button(edit_win, text="💾 Salvar", command=save_edit, bg="#cce5ff",
                                        font=("Consolas", 12, "bold"), width=10, height=2)
                    save_btn.pack(pady=10)

                edit_btn = tk.Button(info_win, text="✏️ Editar", command=edit_text, bg="#fff3cd")
                edit_btn.pack(pady=5)

        # --- Se estiver na lixeira, permitir restaurar
        if fs.cwd == fs.trash:
            def restore_node():
                try:
                    fs.restore_from_trash(node.name)
                    messagebox.showinfo("Sucesso", f"'{node.name}' foi restaurado!")
                    info_win.destroy()
                    self.refresh()
                except Exception as e:
                    messagebox.showerror("Erro", str(e))
            restore_btn = tk.Button(info_win, text="♻️ Restaurar", command=restore_node, bg="#cce5ff")
            restore_btn.pack(pady=5)
        
        def copy_node():
            self.copied_node = node
            messagebox.showinfo("Copiado", f"'{node.name}' foi copiado. Vá para a pasta de destino e clique em 'Colar'.")
            info_win.destroy()
            self.refresh()
            
        copy_btn = tk.Button(info_win, text="📄 Copiar", command=copy_node, bg="#e5e5ff", fg="black")
        copy_btn.pack(pady=5)

    # Criar pasta 
    def mkdir(self):
        """Cria uma nova pasta no diretório atual."""
        # Bloqueia criação se o cwd estiver na Lixeira (ou em subpastas dela)
        trash = getattr(fs, "trash", None)
        n = fs.cwd
        inside_trash = False
        while n is not None:
            if n == trash:
                inside_trash = True
                break
            n = n.parent
        if inside_trash:
            messagebox.showerror("Erro", "Não é permitido criar pastas dentro da Lixeira!")
            return

        name = simpledialog.askstring("Criar Pasta", "Nome da pasta:")
        if not name:
            return
        # Verifica duplicidade de arquivos ou pastas em toda a árvore
        if exists_in_tree(fs.root, name):
            messagebox.showerror("Erro", f"Já existe um arquivo ou pasta chamado '{name}' na árvore!")
            return
        try:
            fs.mkdir(name)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        self.refresh()

    # arquivo
        """Cria um novo arquivo no diretório atual."""
        # Bloqueia criação se o cwd estiver na Lixeira (ou em subpastas dela)
        trash = getattr(fs, "trash", None)
        n = fs.cwd
        inside_trash = False
        while n is not None:
            if n == trash:
                inside_trash = True
                break
            n = n.parent
        if inside_trash:
            messagebox.showerror("Erro", "Não é permitido criar arquivos dentro da Lixeira!")
            return

        while True:
            name = simpledialog.askstring("Criar Arquivo", "Nome do arquivo:")
            if not name:
                return
            # Verifica duplicidade em toda a árvore
            if exists_in_tree(fs.root, name):
                messagebox.showerror("Erro", f"Já existe um arquivo ou pasta chamado '{name}' na árvore!")
                continue

            tipo = simpledialog.askstring(
                "Tipo de Arquivo",
                "Escolha o tipo de arquivo:\n1 - Texto\n2 - Outro (tamanho manual)\n3 - Importar Arquivo"
            )
            if not tipo:
                return
            if tipo in ["1", "2", "3"]:
                break
            else:
                messagebox.showerror("Opção inválida", "Digite uma opção válida (1, 2 ou 3).")

        if tipo == "1":
            text_win = tk.Toplevel(self)
            text_win.title("Conteúdo do arquivo de texto")
            text_win.geometry("600x400")
            tk.Label(text_win, text="Digite o conteúdo do arquivo:").pack(pady=5)
            text_box = tk.Text(text_win, wrap="word", width=70, height=20)
            text_box.pack(padx=10, pady=5, fill="both", expand=True)

            def save_text():
                content = text_box.get("1.0", tk.END).rstrip("\n")
                size = len(content.encode("utf-8"))
                try:
                    fs.touch(name, size)
                    node = fs.cwd.get_child(name)
                    if isinstance(node, FileNode):
                        node.content = content
                    text_win.destroy()
                    self.refresh()
                except Exception as e:
                    messagebox.showerror("Erro", str(e))

            ok_btn = tk.Button(text_win, text="OK", command=save_text, bg="#cce5ff",
                                font=("Consolas", 12, "bold"), width=10, height=2)
            ok_btn.pack(pady=10)

        elif tipo == "2":
            size = None
            while size is None:
                size_str = simpledialog.askstring("Criar Arquivo", "Tamanho do arquivo em bytes:")
                if size_str is None:
                    return
                try:
                    size = int(size_str)
                    if size < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Erro", "Digite um número válido para o tamanho do arquivo!")
                    size = None
            try:
                fs.touch(name, size)
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        elif tipo == "3":
            filepath = filedialog.askopenfilename(
                title="Importar arquivo",
                filetypes=[("Imagens PNG/JPEG", "*.png;*.jpg;*.jpeg"), ("PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
            )
            if not filepath:
                return
            try:
                with open(filepath, "rb") as f:
                    content = f.read()
                size = len(content)
                fs.touch(name, size)
                node = fs.cwd.get_child(name)
                if isinstance(node, FileNode):
                    node.content = content
                messagebox.showinfo("Sucesso", f"Arquivo '{name}' importado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        self.refresh()

    # -------------------- Remover --------------------
    def rm(self):
        """Move o arquivo ou pasta selecionado para a Lixeira ou o remove permanentemente."""
        selected = simpledialog.askstring("Remover", "Nome do arquivo ou pasta:")
        if not selected:
            return
        confirmar = messagebox.askyesno("Confirmação", f"Você deseja realmente apagar '{selected}'?")
        if not confirmar:
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

    # -------------------- Voltar --------------------
    def cd_up(self):
        """Volta para o diretório pai."""
        try:
            fs.cd("..")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        self.refresh()

    # -------------------- Pesquisa --------------------
    def search(self):
        """Pesquisa por arquivos ou pastas na árvore de diretórios atual."""
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
        """Cola o nó copiado no diretório atual."""
        if not self.copied_node:
            messagebox.showerror("Erro", "Nenhum arquivo ou pasta para colar.")
            return

        # Verifica se o diretório atual está na Lixeira
        trash = getattr(fs, "trash", None)
        n = fs.cwd
        inside_trash = False
        while n is not None:
            if n == trash:
                inside_trash = True
                break
            n = n.parent
        if inside_trash:
            messagebox.showerror("Erro", "Não é permitido colar itens na Lixeira!")
            return

        # Cria uma cópia profunda do nó para não afetar o original
        try:
            new_node = copy.deepcopy(self.copied_node)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao copiar o nó: {e}")
            return

        # Manipula o nome para evitar conflitos
        original_name = new_node.name
        new_name = original_name
        counter = 1
        while new_name in [child.name for child in fs.cwd.children]:
            new_name = f"{original_name} (Cópia{'' if counter == 1 else ' ' + str(counter)})"
            counter += 1
        
        new_node.name = new_name
        
        # Define o novo pai e adiciona o nó ao diretório atual
        # Isso garante que o caminho do novo arquivo/pasta seja atualizado automaticamente.
        new_node.parent = fs.cwd
        fs.cwd.children.append(new_node)
        
        # Se for um arquivo, ajusta o uso de disco
        if isinstance(new_node, FileNode):
            fs.total_disk_usage += new_node.size
        else: # Se for uma pasta, calcula o tamanho total dos arquivos nela
            total_size = new_node.get_size()
            fs.total_disk_usage += total_size

        messagebox.showinfo("Sucesso", f"'{original_name}' foi colado como '{new_name}'.")
        self.copied_node = None # Limpa a área de transferência
        self.refresh()

# -------------------- Main --------------------
if __name__ == "__main__":
    app = FileExplorer()
    app.mainloop()
