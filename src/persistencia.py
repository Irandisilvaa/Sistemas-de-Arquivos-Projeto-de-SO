"""
persistencia.py
---------------
Funções para salvar e carregar o sistema de arquivos K-ária.
Inclui persistência do FileSystem e do uso atual de disco.
"""

import pickle
from filesystem import FileSystem, current_disk_usage

def save_fs(fs: FileSystem, filename: str):
    """
    Salva o FileSystem em arquivo, incluindo o uso atual de disco.
    """
    data = {
        "fs": fs,
        "disk_usage": current_disk_usage
    }
    with open(filename, "wb") as f:
        pickle.dump(data, f)

def load_fs(filename: str) -> FileSystem:
    """
    Carrega o FileSystem de arquivo e atualiza o uso atual de disco.
    """
    global current_disk_usage
    with open(filename, "rb") as f:
        data = pickle.load(f)
        fs = data.get("fs")
        current_disk_usage = data.get("disk_usage", 0)
        return fs
