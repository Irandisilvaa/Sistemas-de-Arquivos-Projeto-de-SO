import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import copy
import re

# =================================================================
# --- Componentes do Sistema de Arquivos (Simulado) ---
#    (Incluídos aqui para tornar o código autônomo)
# =================================================================
MAX_DISK_SIZE = 1000000  # Tamanho total do disco em bytes

class Node:
    """Nó base para arquivos e diretórios."""
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.size = 0  # Tamanho padrão para nós

class FileNode(Node):
    """Representa um arquivo."""
    def __init__(self, name, size, parent=None, content=None):
        super().__init__(name, parent)
        self.size = size
        self.content = content # Conteúdo do arquivo, pode ser string ou bytes

class DirectoryNode(Node):
    """Representa um diretório."""
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.children = []

    def get_child(self, name):
        """Retorna um nó filho pelo nome, ou None se não existir."""
        for child in self.children:
            if child.name == name:
                return child
        return None

    def get_size(self):
        """Calcula o tamanho total do diretório (soma dos tamanhos dos arquivos)."""
        total_size = 0
        for child in self.children:
            if isinstance(child, FileNode):
                total_size += child.size
            elif isinstance(child, DirectoryNode):
                total_size += child.get_size()
        return total_size

class FileSystem:
    def __init__(self, max_size):
        self.root = None
        self.cwd = None  # Current Working Directory
        self.trash = None # Diretório da Lixeira
        self.total_disk_usage = 0
        self.max_size = max_size

    def mkdir(self, name):
        """Cria um novo diretório."""
        if not name:
            raise ValueError("Nome do diretório não pode ser vazio.")
        if self.cwd.get_child(name):
            raise FileExistsError(f"O diretório '{name}' já existe.")
        
        new_dir = DirectoryNode(name, self.cwd)
        self.cwd.children.append(new_dir)

    def touch(self, name, size, content=None):
        """Cria um novo arquivo."""
        if not name:
            raise ValueError("Nome do arquivo não pode ser vazio.")
        if self.cwd.get_child(name):
            raise FileExistsError(f"O arquivo '{name}' já existe.")
        if self.total_disk_usage + size > self.max_size:
            raise MemoryError("Espaço em disco insuficiente.")
        
        new_file = FileNode(name, size, self.cwd, content)
        self.cwd.children.append(new_file)
        self.total_disk_usage += size

    def rm(self, name, to_trash=True):
        """Remove um arquivo ou diretório, movendo para a Lixeira se to_trash for True."""
        node = self.cwd.get_child(name)
        if not node:
            raise FileNotFoundError(f"'{name}' não encontrado.")

        if to_trash and self.cwd != self.trash:
            # Move para a lixeira
            self.cwd.children.remove(node)
            node.parent = self.trash
            self.trash.children.append(node)
            messagebox.showinfo("Sucesso", f"'{name}' movido para a Lixeira.")
        else:
            # Remove permanentemente
            self.cwd.children.remove(node)
            if isinstance(node, FileNode):
                self.total_disk_usage -= node.size
            elif isinstance(node, DirectoryNode):
                self.total_disk_usage -= node.get_size()
            messagebox.showinfo("Sucesso", f"'{name}' removido permanentemente.")

    def cd(self, name):
        """Muda o diretório atual."""
        if name == "..":
            if self.cwd.parent:
                self.cwd = self.cwd.parent
            return
        
        node = self.cwd.get_child(name)
        if not isinstance(node, DirectoryNode):
            raise NotADirectoryError(f"'{name}' não é um diretório.")
        self.cwd = node

    def stat(self, name):
        """Retorna informações sobre um arquivo ou diretório."""
        node = self.cwd.get_child(name)
        if not node:
            raise FileNotFoundError(f"'{name}' não encontrado.")
        
        info = {
            "Nome": node.name,
            "Tipo": "Diretório" if isinstance(node, DirectoryNode) else "Arquivo",
            "Caminho": self.get_path(node),
            "Tamanho": f"{node.size} bytes" if isinstance(node, FileNode) else "Variável"
        }
        return info

    def get_disk_usage(self):
        """Retorna o uso total do disco."""
        return self.total_disk_usage

    def restore_from_trash(self, name):
        """Restaura um item da Lixeira para seu local original."""
        node = self.trash.get_child(name)
        if not node:
            raise FileNotFoundError(f"'{name}' não encontrado na Lixeira.")

        original_parent = node.parent if hasattr(node, "parent") and node.parent != self.trash else self.root

        # Verifica se o nó já existe no diretório de destino
        if original_parent.get_child(node.name):
            raise FileExistsError(f"Já existe um item com o nome '{node.name}' no diretório raiz. Renomeie o item antes de restaurá-lo.")

        # Remove da lixeira
        self.trash.children.remove(node)
        
        # Restaura para o diretório pai original
        node.parent = original_parent
        original_parent.children.append(node)

    def update_file_size(self, file_node, new_size):
        """Atualiza o tamanho de um arquivo e do uso total do disco."""
        size_difference = new_size - file_node.size
        if self.total_disk_usage + size_difference > self.max_size:
            raise MemoryError("Espaço em disco insuficiente para salvar o arquivo com o novo tamanho.")
        self.total_disk_usage += size_difference
        file_node.size = new_size

    def get_path(self, node):
        """Obtém o caminho completo de um nó."""
        path_nodes = []
        current = node
        while current and current.name != "C:":
            path_nodes.insert(0, current.name)
            current = current.parent
        full_path = "C:/" + "/".join(path_nodes)
        return full_path

# =================================================================
# --- Inicializa o Sistema de Arquivos ---
# =================================================================
fs = FileSystem(MAX_DISK_SIZE)
if not fs.root:
    fs.root = DirectoryNode("C:")
    fs.cwd = fs.root
    
    fs.mkdir("Lixeira")
    fs.trash = fs.root.get_child("Lixeira")

# =================================================================
# --- Classe FileExplorer (GUI) ---
# =================================================================
class FileExplorer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Explorador de Arquivos K-ária")
        self.state("zoomed")
        self.configure(bg="#e6e6e6")
        
        self.copied_node = None

        # --- Barra superior ---
        self.top_frame = tk.Frame(self, bg="#2f3640", pady=5)
        self.top_frame.pack(fill="x")

        btn_style = {
            "bg": "#40739e", "fg": "white", "relief": "flat",
            "activebackground": "#487eb0", "activeforeground": "white",
            "width": 12, "font": ("Segoe UI", 10, "bold"), "bd": 0
        }
        
        self.paste_btn_style_active = {
            "bg": "#6a89cc", "fg": "white", "relief": "flat",
            "activebackground": "#487eb0", "activeforeground": "white",
            "width": 12, "font": ("Segoe UI", 10, "bold"), "bd": 0
        }
        self.paste_btn_style_disabled = {
            "bg": "#40739e", "fg": "white", "relief": "flat",
            "activebackground": "#487eb0", "activeforeground": "white",
            "width": 12, "font": ("Segoe UI", 10, "bold"), "bd": 0
        }

        left_frame = tk.Frame(self.top_frame, bg="#2f3640")
        left_frame.pack(side="left", padx=5)
        tk.Button(left_frame, text="📁 Criar Pasta", command=self.mkdir, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="📝 Criar Arquivo", command=self.touch, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="🗑️ Remover", command=self.rm, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="⬆️ Voltar", command=self.cd_up, **btn_style).pack(side="left", padx=3)

        self.paste_btn = tk.Button(left_frame, text="📋 Colar", command=self.paste_node, **self.paste_btn_style_disabled, state="disabled")
        self.paste_btn.pack(side="left", padx=3)
        
        right_frame = tk.Frame(self.top_frame, bg="#2f3640")
        right_frame.pack(side="right", padx=10)

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(right_frame, textvariable=self.search_var, width=25,
                                 font=("Segoe UI", 10), relief="flat", bg="#f1f2f6")
        search_entry.pack(side="left", ipady=3, padx=(0,5))

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

        full_path = fs.get_path(fs.cwd)
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

        if isinstance(node, FileNode) and isinstance(getattr(node, "content", None), str):
            def open_text():
                text_win = tk.Toplevel(self)
                text_win.title(f"Conteúdo: {node.name}")
                text_win.geometry("600x400")

                text_box = tk.Text(text_win, wrap="word", width=70, height=20)
                text_box.pack(padx=10, pady=10, fill="both", expand=True)
                text_box.insert("1.0", node.content)
                text_box.config(state="disabled")

            open_btn = tk.Button(info_win, text="📖 Abrir", command=open_text, bg="#d4edda")
            open_btn.pack(pady=5)

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

    # -------------------- Criar pasta --------------------
    def mkdir(self):
        """Cria uma nova pasta no diretório atual."""
        trash_ancestor = False
        n = fs.cwd
        while n:
            if n == fs.trash:
                trash_ancestor = True
                break
            n = n.parent
        
        if trash_ancestor:
            messagebox.showerror("Erro", "Não é permitido criar pastas dentro da Lixeira!")
            return

        name = simpledialog.askstring("Criar Pasta", "Nome da pasta:")
        if not name:
            return
        
        try:
            fs.mkdir(name)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        self.refresh()

    # -------------------- Criar arquivo --------------------
    def touch(self):
        """Cria um novo arquivo no diretório atual."""
        trash_ancestor = False
        n = fs.cwd
        while n:
            if n == fs.trash:
                trash_ancestor = True
                break
            n = n.parent
        
        if trash_ancestor:
            messagebox.showerror("Erro", "Não é permitido criar arquivos dentro da Lixeira!")
            return

        while True:
            name = simpledialog.askstring("Criar Arquivo", "Nome do arquivo:")
            if not name:
                return

            try:
                tipo = simpledialog.askstring(
                    "Tipo de Arquivo",
                    "Escolha o tipo de arquivo:\n1 - Texto\n2 - Outro (tamanho manual)"
                )
                if not tipo:
                    return
                if tipo in ["1", "2"]:
                    break
                else:
                    messagebox.showerror("Opção inválida", "Digite uma opção válida (1 ou 2).")
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                return

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
                    fs.touch(name, size, content)
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
            self.refresh()

    # -------------------- Remover --------------------
    def rm(self):
        """Move o arquivo ou pasta selecionado para a Lixeira ou o remove permanentemente."""
        selected = simpledialog.askstring("Remover", "Nome do arquivo ou pasta:")
        if not selected:
            return
        
        node = fs.cwd.get_child(selected)
        if not node:
            messagebox.showerror("Erro", f"Nó '{selected}' não encontrado em {fs.get_path(fs.cwd)}")
            return
        
        confirmar = messagebox.askyesno("Confirmação", f"Você deseja realmente apagar '{selected}'?")
        if not confirmar:
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
            # Adiciona o próprio nó se ele corresponder à consulta
            current_path = path + "/" + node.name if path else "/" + node.name
            if query.lower() in node.name.lower():
                results.append((node, current_path))
            
            # Se for um diretório, continua a busca nos filhos
            if isinstance(node, DirectoryNode):
                for child in node.children:
                    recursive_search(child, current_path)

        recursive_search(fs.root, path="C:")

        if not results:
            messagebox.showinfo("Pesquisa", f"Nenhum resultado encontrado para '{query}'")
            return
        
        # Limpa e exibe os resultados
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for node, full_path in results:
            frame = tk.Frame(self.scrollable_frame, bg="#ffffcc", bd=1, relief="solid")
            frame.pack(fill="x", pady=2, padx=2)
            label = tk.Label(frame, text=f"{node.name} - {full_path}", anchor="w", bg="#ffffcc")
            label.pack(side="left", padx=5, pady=2, fill="x", expand=True)

            def go_to(n=node):
                if n.parent:
                    fs.cwd = n.parent
                    self.refresh()
                    messagebox.showinfo("Navegar", f"Você foi para o diretório de '{n.name}'")
                else:
                    messagebox.showinfo("Navegar", f"O item '{n.name}' está na raiz.")

            btn = tk.Button(frame, text="Ir para o local do arquivo", command=go_to, bg="#cce5ff")
            btn.pack(side="right", padx=5, pady=2)
    
    # -------------------- Colar --------------------
    def paste_node(self):
        """Cola o nó copiado no diretório atual."""
        if not self.copied_node:
            messagebox.showerror("Erro", "Nenhum arquivo ou pasta para colar.")
            return

        trash_ancestor = False
        n = fs.cwd
        while n:
            if n == fs.trash:
                trash_ancestor = True
                break
            n = n.parent
        
        if trash_ancestor:
            messagebox.showerror("Erro", "Não é permitido colar itens na Lixeira!")
            return

        try:
            new_node = copy.deepcopy(self.copied_node)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao copiar o nó: {e}")
            return

        original_name = new_node.name
        counter = 1
        new_name_attempt = original_name
        
        if fs.cwd.get_child(new_name_attempt):
            new_name_attempt = f"{original_name} - Cópia"
            if fs.cwd.get_child(new_name_attempt):
                while fs.cwd.get_child(f"{original_name} - Cópia({counter})"):
                    counter += 1
                new_name_attempt = f"{original_name} - Cópia({counter})"
        
        new_node.name = new_name_attempt
        
        new_node.parent = fs.cwd
        fs.cwd.children.append(new_node)
        
        if isinstance(new_node, FileNode):
            fs.total_disk_usage += new_node.size
        elif isinstance(new_node, DirectoryNode):
            total_size = new_node.get_size()
            fs.total_disk_usage += total_size

        self.copied_node = None
        self.refresh()
        messagebox.showinfo("Sucesso", f"'{new_node.name}' colado com sucesso!")
        
# -------------------- Main --------------------
if __name__ == "__main__":
    app = FileExplorer()
    app.mainloop()
