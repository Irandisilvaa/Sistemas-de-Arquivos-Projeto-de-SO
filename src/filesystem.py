import tkinter as tk
from tkinter import simpledialog, messagebox, ttk, filedialog
from dataclasses import dataclass, field
from typing import List, Optional
import time
from pathlib import Path

# ---------------------- Configurações ----------------------
MAX_CHILDREN = 5
MAX_DISK_SIZE = 1024 * 10240  # 10 MB
current_disk_usage = 0
file_index_table = {}

# ---------------------- Nodes ----------------------
@dataclass
class Node:
    name: str
    parent: Optional["DirectoryNode"] = field(default=None, repr=False)
    ctime: float = field(default_factory=time.time)
    mtime: float = field(default_factory=time.time)
    atime: float = field(default_factory=time.time)
    original_parent: Optional["DirectoryNode"] = field(default=None, repr=False)

    @property
    def path(self) -> str:
        if self.parent is None:
            return "/"
        parts = []
        node = self
        while node.parent:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))

    def touch(self):
        self.mtime = self.atime = time.time()

@dataclass
class FileNode(Node):
    size: int = 0
    content: str = ""

@dataclass
class DirectoryNode(Node):
    children: List[Node] = field(default_factory=list)

    def add_child(self, node: Node):
        if len(self.children) >= MAX_CHILDREN:
            raise MemoryError(f"Diretório {self.path} atingiu limite de filhos ({MAX_CHILDREN})")
        for child in self.children:
            if child.name == node.name:
                raise FileExistsError(f"Nó '{node.name}' já existe em {self.path}")
        node.parent = self
        self.children.append(node)
        self.touch()

    def get_child(self, name: str) -> Node:
        for child in self.children:
            if child.name == name:
                return child
        raise FileNotFoundError(f"Nó '{name}' não encontrado em {self.path}")

    def remove_child(self, name: str):
        for i, child in enumerate(self.children):
            if child.name == name:
                self.children.pop(i)
                self.touch()
                return
        raise FileNotFoundError(f"Nó '{name}' não encontrado em {self.path}")

# ---------------------- FileSystem ----------------------
class FileSystem:
    def __init__(self):
        self.root = DirectoryNode(name="C:")
        self.cwd = self.root
        self.trash = DirectoryNode(name=".lixeira")
        self.root.add_child(self.trash)

    def mkdir(self, name: str):
        dir_node = DirectoryNode(name=name)
        try:
            self.cwd.add_child(dir_node)
        except FileExistsError as e:
            raise e
        file_index_table[dir_node.path] = {
            "type": "dir",
            "node": dir_node,
            "created": dir_node.ctime,
            "modified": dir_node.mtime
        }

    def touch(self, name: str, size: int = 0):
        global current_disk_usage
        if current_disk_usage + size > MAX_DISK_SIZE:
            raise MemoryError("Disco cheio")
        file_node = FileNode(name=name, size=size)
        try:
            self.cwd.add_child(file_node)
        except FileExistsError as e:
            raise e
        current_disk_usage += size
        file_index_table[file_node.path] = {
            "size": file_node.size,
            "node": file_node,
            "created": file_node.ctime,
            "modified": file_node.mtime,
            "trashed": False
        }

    def cd(self, name: str):
        if name == "..":
            if self.cwd.parent:
                self.cwd = self.cwd.parent
        else:
            node = self.cwd.get_child(name)
            if not isinstance(node, DirectoryNode):
                raise NotADirectoryError(f"{node.path} não é diretório")
            self.cwd = node

    def ls(self):
        return [child.name for child in self.cwd.children]

    def rm(self, name: str, to_trash: bool = True):
        global current_disk_usage
        node = self.cwd.get_child(name)

        def calc_size(n: Node) -> int:
            if isinstance(n, FileNode):
                return n.size
            elif isinstance(n, DirectoryNode):
                return sum(calc_size(c) for c in n.children)
            return 0

        size_to_free = calc_size(node)
        self.cwd.remove_child(name)
        full_path = node.path

        if full_path in file_index_table:
            if to_trash:
                file_index_table[full_path]["trashed"] = True
            else:
                del file_index_table[full_path]

        if to_trash:
            node.original_parent = self.cwd
            node.parent = None
            trash_name = name
            counter = 1
            while any(c.name == trash_name for c in self.trash.children):
                trash_name = f"{name}_{counter}"
                counter += 1
            node.name = trash_name
            self.trash.add_child(node)
        else:
            if isinstance(node, DirectoryNode):
                node.children.clear()
            current_disk_usage -= size_to_free

    def restore_from_trash(self, name: str, target_dir: Optional[DirectoryNode] = None):
        node = self.trash.get_child(name)
        self.trash.remove_child(name)
        target = target_dir if target_dir else node.original_parent or self.root
        node.original_parent = None
        original_name = node.name
        counter = 1
        while any(c.name == node.name for c in target.children):
            node.name = f"{original_name}_{counter}"
            counter += 1
        target.add_child(node)
        file_index_table[node.path]["trashed"] = False

    def stat(self, name: str):
        node = self.cwd.get_child(name)
        info = {
            "name": node.name,
            "path": node.path,
            "ctime": node.ctime,
            "mtime": node.mtime,
            "atime": node.atime,
            "type": "dir" if isinstance(node, DirectoryNode) else "file"
        }
        if isinstance(node, FileNode):
            info["size"] = node.size
        else:
            info["children"] = [c.name for c in node.children]
        return info

    def get_disk_usage(self):
        global current_disk_usage
        return current_disk_usage

fs = FileSystem()

# ---------------------- Tkinter FileExplorer ----------------------
def center_window(win, width, height):
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = int((screen_width - width)/2)
    y = int((screen_height - height)/2)
    win.geometry(f"{width}x{height}+{x}+{y}")

class FileExplorer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Explorador K-ária")
        self.geometry("950x650")
        self.configure(bg="#e6e6e6")

        # Barra superior
        self.top_frame = tk.Frame(self, bg="#2f3640", pady=5)
        self.top_frame.pack(fill="x")

        btn_style = {"bg": "#40739e", "fg": "white", "relief": "flat",
                     "activebackground": "#487eb0", "activeforeground": "white",
                     "width": 14, "font": ("Segoe UI", 10, "bold"), "bd": 0}

        left_frame = tk.Frame(self.top_frame, bg="#2f3640")
        left_frame.pack(side="left", padx=5)

        tk.Button(left_frame, text="📁 Criar Pasta", command=self.mkdir, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="📝 Criar Arquivo", command=self.touch, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="🗑️ Remover", command=self.rm, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="⬅️ Voltar", command=self.cd_up, **btn_style).pack(side="left", padx=3)
        tk.Button(left_frame, text="🔄 Atualizar", command=self.refresh, **btn_style).pack(side="left", padx=3)

        right_frame = tk.Frame(self.top_frame, bg="#2f3640")
        right_frame.pack(side="right", padx=10)

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(right_frame, textvariable=self.search_var, width=25,
                                font=("Segoe UI", 10), relief="flat", bg="#f1f2f6")
        search_entry.pack(side="left", ipady=3, padx=(0,5))

        search_btn = tk.Button(right_frame, text="🔍", font=("Segoe UI", 12), bg="#f1f2f6",
                               relief="flat", command=self.search)
        search_btn.pack(side="left")

        self.path_label = tk.Label(self, text="C:/", font=("Consolas", 12, "bold"), fg="#1a73e8", bg="#e6e6e6")
        self.path_label.pack(fill="x", pady=4, padx=10)

        self.disk_label = tk.Label(self, text="", font=("Consolas", 10), bg="#e6e6e6", fg="#333333")
        self.disk_label.pack(fill="x", pady=2, padx=10)
        self.disk_progress = ttk.Progressbar(self, orient="horizontal", length=450, mode="determinate")
        self.disk_progress.pack(pady=2, padx=10)

        self.main_frame = tk.Frame(self, bg="#e6e6e6")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(self.main_frame, bg="#e6e6e6", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#e6e6e6")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0,0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.refresh()

    # ---------------- Funções principais ----------------
    def refresh(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
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

    def open_dir(self, node):
        fs.cwd = node
        self.refresh()

    def show_info(self, node):
        info = fs.stat(node.name)
        text = "\n".join(f"{k}: {v}" for k, v in info.items())
        info_win = tk.Toplevel(self)
        info_win.title(f"Informações: {node.name}")
        center_window(info_win, 400, 300)
        tk.Label(info_win, text=text, justify="left", font=("Consolas", 10)).pack(padx=10, pady=10)

        if fs.cwd == fs.trash:
            def restore_node():
                try:
                    fs.restore_from_trash(node.name)
                    messagebox.showinfo("Sucesso", f"'{node.name}' foi restaurado!")
                    info_win.destroy()
                    self.refresh()
                except Exception as e:
                    messagebox.showerror("Erro", str(e))
            tk.Button(info_win, text="Restaurar", command=restore_node, bg="#cce5ff", font=("Segoe UI", 12)).pack(pady=5)

    # Outras funções de criação de pasta, arquivo, remoção, cd_up e pesquisa podem ser incluídas aqui seguindo o mesmo padrão

if __name__ == "__main__":
    app = FileExplorer()
    app.mainloop()
