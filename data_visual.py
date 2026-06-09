import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import datatest

# Студ. ID: 70227481, фамилия на М
# Цветовая схема по умолчанию: 'YlOrRd'
DEFAULT_CMAP = 'YlOrRd'
MARKER = 'P'

NUMERIC_COLS = datatest.NUMERIC_COLS
CATEGORICAL_COLS = datatest.CATEGORICAL_COLS
ALL_COLS = NUMERIC_COLS + CATEGORICAL_COLS

CMAPS = [
    'viridis', 'plasma', 'inferno', 'magma', 'cividis',
    'Greys', 'Purples', 'Blues', 'Greens', 'Oranges',
    'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd',
    'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu',
    'PuBuGn', 'BuGn', 'YlGn', 'binary', 'gist_yarg',
    'spring', 'summer', 'autumn', 'winter'
]


class VisualApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Визуализация данных")
        self.x_col = ALL_COLS[0]
        self.y_col = ALL_COLS[1] if len(ALL_COLS) > 1 else ALL_COLS[0]
        self.cmap = DEFAULT_CMAP
        self._build_ui()
        self._update_plot()

    def _build_ui(self):
        # Панель выбора цветовой схемы сверху
        top_frame = tk.Frame(self.root)
        top_frame.grid(row=0, column=0, columnspan=3, pady=5, sticky='w', padx=10)
        tk.Label(top_frame, text="Цветовая схема:", font=('Arial', 10, 'bold')).pack(side='left')
        self.cmap_var = tk.StringVar(value=DEFAULT_CMAP)
        cmap_box = ttk.Combobox(top_frame, textvariable=self.cmap_var,
                                values=CMAPS, state='readonly', width=15)
        cmap_box.pack(side='left', padx=5)
        cmap_box.bind('<<ComboboxSelected>>', self._on_cmap_change)

        # График
        self.fig, self.ax = plt.subplots(figsize=(6, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=1, column=1, padx=5, pady=5)

        # Кнопки слева (ось Y)
        left_frame = tk.Frame(self.root)
        left_frame.grid(row=1, column=0, padx=5, pady=5, sticky='ns')
        tk.Label(left_frame, text="Ось Y", font=('Arial', 10, 'bold')).pack()
        for col in ALL_COLS:
            btn = tk.Button(left_frame, text=col, width=22,
                            command=lambda c=col: self._set_y(c))
            btn.pack(pady=2)

        # Кнопка сохранения
        save_btn = tk.Button(left_frame, text="Сохранить",
                             command=self._save, font=('Arial', 10))
        save_btn.pack(side='bottom', pady=5)

        # Кнопки снизу (ось X)
        bottom_frame = tk.Frame(self.root)
        bottom_frame.grid(row=2, column=1, pady=5)
        tk.Label(bottom_frame, text="Ось X:", font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        for col in ALL_COLS:
            btn = tk.Button(bottom_frame, text=col, width=16,
                            command=lambda c=col: self._set_x(c))
            btn.pack(side='left', padx=2)



    def _on_cmap_change(self, event=None):
        self.cmap = self.cmap_var.get()
        self._update_plot()

    def _set_x(self, col):
        self.x_col = col
        self._update_plot()

    def _set_y(self, col):
        self.y_col = col
        self._update_plot()

    def _get_colors(self, n):
        """Получить список из n цветов из текущей цветовой карты."""
        import matplotlib.cm as cm
        import numpy as np
        cmap_obj = cm.get_cmap(self.cmap)
        return [cmap_obj(i / max(n - 1, 1)) for i in range(n)]

    def _update_plot(self):
        self.ax.clear()
        df = datatest.df
        x = self.x_col
        y = self.y_col
        x_num = x in NUMERIC_COLS
        y_num = y in NUMERIC_COLS

        import matplotlib.cm as cm
        import numpy as np

        if x == y and x_num:
            # Гистограмма
            colors = self._get_colors(10)
            n, bins, patches = self.ax.hist(df[x], bins=10, color='steelblue')
            cmap_obj = cm.get_cmap(self.cmap)
            for i, patch in enumerate(patches):
                patch.set_facecolor(cmap_obj(i / 10))
            self.ax.set_xlabel(x)
            self.ax.set_ylabel("Частота")
            self.ax.set_title(f"Гистограмма: {x}")

        elif x == y and not x_num:
            # Круговая диаграмма
            counts = df[x].value_counts()
            colors = self._get_colors(len(counts))
            self.ax.pie(counts.values, labels=counts.index, colors=colors, autopct='%1.1f%%')
            self.ax.set_title(f"Круговая диаграмма: {x}")

        elif x_num and not y_num:
            # Коробочная диаграмма
            categories = df[y].unique()
            data = [df[df[y] == cat][x].dropna().values for cat in categories]
            bp = self.ax.boxplot(data, labels=categories, patch_artist=True)
            colors = self._get_colors(len(categories))
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
            self.ax.set_xlabel(y)
            self.ax.set_ylabel(x)
            self.ax.set_title(f"Коробочная диаграмма: {x} по {y}")
            self.ax.tick_params(axis='x', rotation=45)

        elif not x_num and y_num:
            # Столбчатая диаграмма
            counts = df[x].value_counts()
            colors = self._get_colors(len(counts))
            self.ax.bar(counts.index, counts.values, color=colors)
            self.ax.set_xlabel(x)
            self.ax.set_ylabel("Количество")
            self.ax.set_title(f"Столбчатая диаграмма: {x}")
            self.ax.tick_params(axis='x', rotation=45)

        else:
            # Точечная диаграмма (оба числовые, разные)
            scatter = self.ax.scatter(df[x], df[y], marker=MARKER, alpha=0.6,
                                      c=range(len(df)), cmap=self.cmap)
            self.ax.set_xlabel(x)
            self.ax.set_ylabel(y)
            self.ax.set_title(f"{x} vs {y}")

        self.fig.tight_layout()
        self.canvas.draw()

    def _save(self):
        now = datetime.now()
        filename = f"graph{now.strftime('%H_%M_%S')}.png"
        self.fig.savefig(filename)
        print(f"График сохранён: {filename}")


if __name__ == '__main__':
    root = tk.Tk()
    app = VisualApp(root)
    root.mainloop()
