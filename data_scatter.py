import tkinter as tk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import dataset

# Студ. ID: 70227481
# Рекурсивная сумма: 7+0+2+2+7+4+8+1=31 -> 3+1=4
# Маркер №4: 's' (квадрат)
MARKER = 's'

NUMERIC_COLS = dataset.NUMERIC_COLS


class ScatterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Точечная диаграмма")
        self.x_col = NUMERIC_COLS[0]
        self.y_col = NUMERIC_COLS[1]
        self._build_ui()
        self._update_plot()

    def _build_ui(self):
        # Верхняя рамка: график
        self.fig, self.ax = plt.subplots(figsize=(6, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=0, column=1, padx=5, pady=5)

        # Кнопки слева (ось Y) + кнопка сохранения внизу
        left_frame = tk.Frame(self.root)
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky='ns')
        tk.Label(left_frame, text="Ось Y", font=('Arial', 10, 'bold')).pack()
        for col in NUMERIC_COLS:
            btn = tk.Button(left_frame, text=col, width=18,
                            command=lambda c=col: self._set_y(c))
            btn.pack(pady=2)

        save_btn = tk.Button(left_frame, text="Сохранить",
                             command=self._save, font=('Arial', 10))
        save_btn.pack(side='bottom', pady=5)

        # Кнопки снизу (ось X)
        bottom_frame = tk.Frame(self.root)
        bottom_frame.grid(row=1, column=1, pady=5)
        tk.Label(bottom_frame, text="Ось X:", font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        for col in NUMERIC_COLS:
            btn = tk.Button(bottom_frame, text=col, width=18,
                            command=lambda c=col: self._set_x(c))
            btn.pack(side='left', padx=2)

    def _set_x(self, col):
        self.x_col = col
        self._update_plot()

    def _set_y(self, col):
        self.y_col = col
        self._update_plot()

    def _update_plot(self):
        self.ax.clear()
        df = dataset.df
        self.ax.scatter(df[self.x_col], df[self.y_col], marker=MARKER, alpha=0.6, color='steelblue')
        self.fig.tight_layout()
        self.canvas.draw()

    def _save(self):
        now = datetime.now()
        filename = f"graph{now.strftime('%H_%M_%S')}.png"
        self.fig.savefig(filename)
        print(f"График сохранён: {filename}")


if __name__ == '__main__':
    root = tk.Tk()
    app = ScatterApp(root)
    root.mainloop()