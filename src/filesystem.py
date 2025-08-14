from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import time

MAX_CHILDREN = 5           # Número máximo de filhos por diretório (K)
MAX_DISK_SIZE = 1024*10240 # 10 MB para teste

current_disk_usage = 0     # Variável global para gerenciar "disco cheio"

# ---------------------- Tabela de Índices ----------------------
# Chave: caminho completo do arquivo, Valor: metadados e referência ao node
file_index_table = {}

# ---------------------- Nós da Árvore ----------------------
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
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))

    def touch(self) -> None:
        self.mtime = time.time()
        self.atime = time.time()

@dataclass
class FileNode(Node):
    size: int = 0
    content: str = ""

@dataclass
class DirectoryNode(Node):
    children: List[Node] = field(default_factory=list)

    def add_child(self, node: Node) -> None:
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

    def remove_child(self, name: str) -> None:
        for i, child in enumerate(self.children):
            if child.name == name:
                self.children.pop(i)
                self.touch()
                return
        raise FileNotFoundError(f"Nó '{name}' não encontrado em {self.path}")

# ---------------------- Sistema de Arquivos ----------------------
class FileSystem:
    def __init__(self):
        self.root = DirectoryNode(name="C:")
        self.cwd = self.root
        # Pasta especial para arquivos apagados
        self.trash = DirectoryNode(name=".lixeira")
        self.root.add_child(self.trash)

    # --------- Diretórios ----------
    def mkdir(self, name: str) -> None:
        dir_node = DirectoryNode(name=name)
        self.cwd.add_child(dir_node)
        # Adiciona diretórios na tabela de índices (opcional)
        file_index_table[dir_node.path] = {
            "type": "dir",
            "node": dir_node,
            "created": dir_node.ctime,
            "modified": dir_node.mtime
        }

    def cd(self, name: str) -> None:
        if name == "..":
            if self.cwd.parent is not None:
                self.cwd = self.cwd.parent
        else:
            node = self.cwd.get_child(name)
            if not isinstance(node, DirectoryNode):
                raise NotADirectoryError(f"{node.path} não é diretório")
            self.cwd = node

    def ls(self) -> List[str]:
        return [child.name for child in self.cwd.children]

    # --------- Arquivos ----------
    def touch(self, name: str, size: int = 0) -> None:
        global current_disk_usage
        if current_disk_usage + size > MAX_DISK_SIZE:
            raise MemoryError("Disco cheio")
        file_node = FileNode(name=name, size=size)
        self.cwd.add_child(file_node)
        current_disk_usage += size

        # Atualiza tabela de índices
        file_index_table[file_node.path] = {
            "size": file_node.size,
            "node": file_node,
            "created": file_node.ctime,
            "modified": file_node.mtime,
            "trashed": False
        }

    def rm(self, name: str, to_trash: bool = True) -> None:
        """
        Remove arquivo/pasta. 
        Se to_trash=True, envia para a lixeira; senão, remoção permanente.
        """
        global current_disk_usage
        node = self.cwd.get_child(name)

        def calc_size(n: Node) -> int:
            if isinstance(n, FileNode):
                return n.size
            elif isinstance(n, DirectoryNode):
                return sum(calc_size(child) for child in n.children)
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

    def empty_trash(self, names: Optional[List[str]] = None):
        global current_disk_usage

        def calc_size(n: Node) -> int:
            if isinstance(n, FileNode):
                return n.size
            elif isinstance(n, DirectoryNode):
                return sum(calc_size(child) for child in n.children)
            return 0

        if names is None:
            for node in self.trash.children:
                current_disk_usage -= calc_size(node)
                full_path = node.path
                if full_path in file_index_table:
                    del file_index_table[full_path]
            self.trash.children.clear()
        else:
            to_remove = []
            for node in self.trash.children:
                if node.name in names:
                    current_disk_usage -= calc_size(node)
                    full_path = node.path
                    if full_path in file_index_table:
                        del file_index_table[full_path]
                    to_remove.append(node)
            for node in to_remove:
                self.trash.remove_child(node.name)

    def restore_from_trash(self, name: str, target_dir: Optional[DirectoryNode] = None):
        node = self.trash.get_child(name)
        self.trash.remove_child(name)
        target = target_dir if target_dir else node.original_parent or self.root
        node.original_parent = None
        target.add_child(node)

        # Atualiza tabela de índices
        full_path = node.path
        file_index_table[full_path]["trashed"] = False

    def stat(self, name: str) -> dict:
        node = self.cwd.get_child(name)
        info = {
            "name": node.name,
            "path": node.path,
            "ctime": node.ctime,
            "mtime": node.mtime,
            "atime": node.atime,
            "type": "dir" if isinstance(node, DirectoryNode) else "file",
        }
        if isinstance(node, FileNode):
            info["size"] = node.size
        else:
            info["children"] = [c.name for c in node.children]
        return info

    def get_disk_usage(self) -> int:
        global current_disk_usage
        return current_disk_usage

    # ---------------------- Funções de índice ----------------------
    def find_file_by_path(self, full_path: str):
        return file_index_table.get(full_path)

    def search_files_by_name(self, name: str):
        results = []
        for path, data in file_index_table.items():
            if name.lower() in path.lower():
                results.append((path, data))
        return results

# ---------------------- Inicialização do FS ----------------------
fs = FileSystem()
