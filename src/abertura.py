import tkinter as tk
import random
from interface import FileExplorer  # importa sua interface principal

class WelcomeScreen(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bem-vindo!")
        self.state("zoomed")  # Abre em tela cheia
        self.configure(bg="#2f3640")

        # Texto de boas-vindas
        self.label = tk.Label(self, text="", font=("Segoe UI", 40, "bold"), fg="white", bg="#2f3640")
        self.label.place(relx=0.5, rely=0.3, anchor="center")
        self.full_text = "Bem-vindo ao Melhor Gerenciador de Arquivos do DCOMP!"
        self.text_index = 0

        # Canvas para animação de ícones
        self.canvas = tk.Canvas(self, bg="#2f3640", highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.65, anchor="center", relwidth=1, relheight=0.5)
        self.icons = []

        # Inicializa a animação
        self.animate_text()
        self.create_icons()
        self.animate_icons()

    def animate_text(self):
        if self.text_index < len(self.full_text):
            self.label.config(text=self.full_text[:self.text_index+1])
            self.text_index += 1
            self.after(50, self.animate_text)  # muda a cada 50ms
        else:
            # após terminar o texto, espera 1s e abre a interface principal
            self.after(1000, self.open_main_app)

    def create_icons(self):
        width = self.winfo_screenwidth()
        for _ in range(30):  # 30 ícones de pasta
            x = random.randint(0, width-50)
            y = random.randint(-400, -50)
            icon = self.canvas.create_text(x, y, text="📁", font=("Segoe UI", 40))
            self.icons.append(icon)

    def animate_icons(self):
        height = self.winfo_screenheight() // 2
        width = self.winfo_screenwidth()
        for icon in self.icons:
            self.canvas.move(icon, 0, random.randint(2, 6))
            pos = self.canvas.coords(icon)
            if pos[1] > height:  # reinicia no topo
                self.canvas.coords(icon, random.randint(0, width-50), random.randint(-400, -50))
        self.after(50, self.animate_icons)

    def open_main_app(self):
        self.destroy()
        app = FileExplorer()
        app.mainloop()

if __name__ == "__main__":
    welcome = WelcomeScreen()
    welcome.mainloop()
