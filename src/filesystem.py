import time
from dataclasses import dataclass, field
from typing import List, Optional


# Configurações iniciais 
MAX_CHILDREN = 10
MAX_DISK_SIZE = 1024 * 1024 
current_disk_usage = 0
file_index_table = {}

# Nodes da árvore
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

# FileSystem 
class FileSystem:
    def _init_(self):
        self.root = DirectoryNode(name="C:")
        self.cwd = self.root
        self.trash = DirectoryNode(name="Lixeira")
        self.root.add_child(self.trash)

    # Comandos 
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

    def update_file_size(self, node: FileNode, new_size: int):
        """Atualiza o tamanho do arquivo e o uso total do disco."""
        global current_disk_usage
        size_change = new_size - node.size
        if current_disk_usage + size_change > MAX_DISK_SIZE:
            raise MemoryError("Espaço em disco insuficiente para salvar as alterações!")
        current_disk_usage += size_change
        node.size = new_size
        node.touch()

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

    def copy_node(self, node: Node, target_dir: Optional[DirectoryNode] = None):
        """Cria uma cópia de um nó (arquivo ou diretório) no target_dir ou cwd."""
        import copy
        target_dir = target_dir or self.cwd
        new_node = copy.deepcopy(node)

        # Garante que o nome não exista no destino
        original_name = new_node.name
        counter = 1
        while any(c.name == new_node.name for c in target_dir.children):
            new_node.name = f"{original_name} - Cópia({counter})"
            counter += 1

        target_dir.add_child(new_node)

        # Atualiza o uso do disco
        self.add_disk_usage_for_node(new_node)
        return new_node
    
fs = FileSystem()