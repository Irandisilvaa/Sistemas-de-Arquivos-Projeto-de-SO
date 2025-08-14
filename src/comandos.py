"""
comandos.py
-----------
Tradução de comandos em funções que manipulam a árvore K-ária.
"""

from filesystem import FileSystem

fs = FileSystem()

def comando_mkdir(name: str):
    fs.mkdir(name)

def comando_touch(name: str, size: int = 0):
    fs.touch(name, size)

def comando_ls():
    return fs.ls()

def comando_cd(name: str):
    fs.cd(name)

def comando_rm(name: str):
    fs.rm(name)

def comando_stat(name: str):
    return fs.stat(name)
