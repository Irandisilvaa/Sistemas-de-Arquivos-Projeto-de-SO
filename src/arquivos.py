"""
arquivos.py
-----------
API de conveniência (pode ser usada por outros módulos/testes).
Chama diretamente métodos do FileSystem.
"""

from filesystem import FileSystem

class ArquivosAPI:
    def __init__(self, fs: FileSystem):
        self.fs = fs

    def criar_arquivo(self, caminho: str) -> None:
        self.fs.touch(caminho)

    def escrever(self, caminho: str, conteudo: str, append: bool=False) -> None:
        self.fs.write(caminho, conteudo, append=append)

    def ler(self, caminho: str) -> str:
        return self.fs.read(caminho)

    def remover(self, caminho: str) -> None:
        self.fs.rm(caminho)

    def listar(self, caminho: str | None=None):
        return self.fs.ls(caminho if caminho else ".")
