import tkinter as tk
from tkinter import ttk, colorchooser
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from PIL import Image, ImageDraw
import numpy as np
import dataset

# Студ. ID: 70227481
# Рекурсивная сумма цифр: 4
# Толщина кисти по умолчанию: 4 // 2 + 5 = 7
# Цвет кисти: последние 6 цифр ID = 227481
#   R = 22, G = 74, B = 81 -> #164A51
DEFAULT_BRUSH_SIZE = 7
DEFAULT_COLOR = '#164A51'
DEFAULT_CMAP = 'YlOrRd'

NUMERIC_COLS = dataset.NUMERIC_COLS
CATEGORICAL_COLS = dataset.CATEGORICAL_COLS
ALL_COLS = NUMERIC_COLS + CATEGORICAL_COLS
MARKER = 's'

CMAPS = [
    'viridis', 'plasma', 'inferno', 'magma', 'cividis',
    'Greys', 'Purples', 'Blues', 'Greens', 'Oranges',
    'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd',
    'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu',
    'PuBuGn', 'BuGn', 'YlGn', 'binary', 'gist_yarg',
    'spring', 'summer', 'autumn', 'winter'
]


class DrawApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Рисование на графике")
        self.x_col = ALL_COLS[0]
        self.y_col = ALL_COLS[1] if len(ALL_COLS) > 1 else ALL_COLS[0]
        self.cmap = DEFAULT_CMAP
        self.draw_mode = False
        self.brush_size = DEFAULT_BRUSH_SIZE
        self.brush_color = DEFAULT_COLOR
        self.drawing = False
        self.strokes = []          # список ВСЕХ завершённых мазков (каждый — список точек)
        self.current_stroke = []   # точки текущего, ещё не завершённого мазка
        self.overlay = None        # PIL Image для рисования
        self._build_ui()
        # Форсируем расчёт реальных размеров виджетов ДО первого построения
        # графика — иначе на момент первого _update_plot() окно ещё не
        # отрисовано, winfo_width/height вернут 1x1, self.overlay не
        # создастся, и рисовать будет нельзя до первой смены осей.
        self.root.update_idletasks()
        self._update_plot()

    def _build_ui(self):
        # Верхняя панель: цветовая схема + инструменты рисования
        top_frame = tk.Frame(self.root)
        top_frame.grid(row=0, column=0, columnspan=3, pady=5, sticky='w', padx=10)

        tk.Label(top_frame, text="Цветовая схема:", font=('Arial', 9, 'bold')).pack(side='left')
        self.cmap_var = tk.StringVar(value=DEFAULT_CMAP)
        cmap_box = ttk.Combobox(top_frame, textvariable=self.cmap_var,
                                values=CMAPS, state='readonly', width=12)
        cmap_box.pack(side='left', padx=5)
        cmap_box.bind('<<ComboboxSelected>>', self._on_cmap_change)

        # Кнопка режима рисования
        self.draw_btn = tk.Button(top_frame, text="✏️ Рисование",
                                  command=self._toggle_draw, relief='raised',
                                  font=('Arial', 9))
        self.draw_btn.pack(side='left', padx=10)

        # Цвет кисти
        tk.Label(top_frame, text="Цвет:", font=('Arial', 9)).pack(side='left')
        self.color_btn = tk.Button(top_frame, bg=DEFAULT_COLOR, width=3,
                                   command=self._choose_color, relief='raised')
        self.color_btn.pack(side='left', padx=3)

        # Толщина кисти
        tk.Label(top_frame, text="Толщина:", font=('Arial', 9)).pack(side='left', padx=(10, 0))
        self.size_var = tk.IntVar(value=DEFAULT_BRUSH_SIZE)
        size_spin = tk.Spinbox(top_frame, from_=1, to=30, textvariable=self.size_var,
                               width=4, command=self._on_size_change)
        size_spin.pack(side='left', padx=3)

        # График
        self.fig, self.ax = plt.subplots(figsize=(6, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        widget = self.canvas.get_tk_widget()
        widget.grid(row=1, column=1, padx=5, pady=5)

        # Привязка событий мыши
        widget.bind('<ButtonPress-1>', self._on_mouse_press)
        widget.bind('<B1-Motion>', self._on_mouse_drag)
        widget.bind('<ButtonRelease-1>', self._on_mouse_release)
        widget.bind('<ButtonPress-3>', self._stop_draw_mode)
        # Ловим Ctrl+Z по физическому коду клавиши (event.keycode), а не по
        # символу (keysym) — символ зависит от раскладки (на ЙЦУКЕН клавиша
        # в этом месте печатает "я", а не "z", и обычный '<Control-z>'
        # с ней вообще не совпадает). keycode же определяется положением
        # клавиши на клавиатуре и от раскладки не зависит: на Windows это
        # VK_Z = 90 всегда, на Linux/X11 обычно 52, на macOS — 6.
        # Проверяем оба варианта (keysym и keycode) для надёжности сразу
        # на нескольких платформах.
        self.root.bind_all('<Control-KeyPress>', self._on_ctrl_key)

        # Корректное завершение процесса при закрытии окна: без этого
        # обработчика после клика по крестику Tk-виджеты уничтожаются,
        # но matplotlib продолжает хранить фигуру в своём глобальном
        # реестре (pyplot.Gcf), из-за чего процесс python не завершается.
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

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



    def _toggle_draw(self):
        self.draw_mode = not self.draw_mode
        if self.draw_mode:
            self.draw_btn.config(relief='sunken', bg='#FFD700')
            self.canvas.get_tk_widget().config(cursor='pencil')
        else:
            self._stop_draw_mode()

    def _stop_draw_mode(self, event=None):
        self.draw_mode = False
        self.draw_btn.config(relief='raised', bg='SystemButtonFace')
        self.canvas.get_tk_widget().config(cursor='arrow')

    def _choose_color(self):
        color = colorchooser.askcolor(color=self.brush_color, title="Выберите цвет")[1]
        if color:
            self.brush_color = color
            self.color_btn.config(bg=color)

    def _on_size_change(self):
        self.brush_size = self.size_var.get()

    def _on_cmap_change(self, event=None):
        self.cmap = self.cmap_var.get()
        self._update_plot()

    def _set_x(self, col):
        self.x_col = col
        self._stop_draw_mode()
        self._update_plot()

    def _set_y(self, col):
        self.y_col = col
        self._stop_draw_mode()
        self._update_plot()

    def _get_canvas_size(self):
        widget = self.canvas.get_tk_widget()
        w, h = widget.winfo_width(), widget.winfo_height()
        # Пока окно не отрисовано на экране (сразу после запуска, до первого
        # события Expose/Configure), winfo_width/height возвращают 1x1 —
        # реальные размеры ещё не посчитаны geometry-менеджером. В этом
        # случае используем "запрошенный" размер виджета (winfo_reqwidth/
        # reqheight), который для canvas с фиксированным figsize известен
        # сразу при создании и не зависит от того, замаплено ли окно.
        if w <= 1 or h <= 1:
            w, h = widget.winfo_reqwidth(), widget.winfo_reqheight()
        return w, h

    def _on_mouse_press(self, event):
        if not self.draw_mode:
            return
        self.drawing = True
        self.current_stroke = []
        self._paint(event.x, event.y)

    def _on_mouse_drag(self, event):
        if not self.draw_mode or not self.drawing:
            return
        self._paint(event.x, event.y)

    def _on_mouse_release(self, event):
        if not self.draw_mode:
            return
        self.drawing = False
        # Завершённый мазок целиком уходит в историю (если что-то было нарисовано)
        if self.current_stroke:
            self.strokes.append(self.current_stroke)
        self.current_stroke = []

    def _paint(self, x, y):
        if self.overlay is None:
            return
        draw = ImageDraw.Draw(self.overlay)
        r = self.brush_size // 2
        # Рисуем квадрат
        draw.rectangle([x - r, y - r, x + r, y + r], fill=self.brush_color)
        # Запоминаем точку вместе с толщиной и цветом на момент рисования —
        # это нужно, чтобы при отмене можно было точно восстановить все
        # оставшиеся мазки, даже если цвет/толщина потом менялись
        self.current_stroke.append((x, y, self.brush_size, self.brush_color))
        self._refresh_canvas()

    def _on_ctrl_key(self, event):
        """Диспетчер для Ctrl+<любая клавиша>. Вызывает отмену, если это
        именно Z — распознаём и по keysym (сработает на латинской
        раскладке), и по keycode (сработает независимо от раскладки,
        в т.ч. на ЙЦУКЕН, где эта же физическая клавиша печатает "я")."""
        keysym = (event.keysym or '').lower()
        if keysym in ('z', 'cyrillic_ya') or event.keycode in (90, 52, 6, 29):
            self._undo(event)

    def _undo(self, event=None):
        if not self.draw_mode or self.drawing or not self.strokes:
            return
        # Убираем последний завершённый мазок из истории...
        self.strokes.pop()
        # ...и перерисовываем оверлей с нуля по оставшимся мазкам,
        # так что все более ранние линии остаются на месте
        self._rebuild_overlay()
        self._refresh_canvas()

    def _rebuild_overlay(self):
        """Полностью пересобирает оверлей по текущему списку self.strokes."""
        w, h = self._get_canvas_size()
        new_overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(new_overlay)
        for stroke in self.strokes:
            for (x, y, size, color) in stroke:
                r = size // 2
                draw.rectangle([x - r, y - r, x + r, y + r], fill=color)
        self.overlay = new_overlay

    def _refresh_canvas(self):
        """Накладываем оверлей поверх графика matplotlib."""
        # Получаем изображение matplotlib
        self.fig.canvas.draw()
        buf = self.fig.canvas.buffer_rgba()
        w_fig = int(self.fig.get_figwidth() * self.fig.dpi)
        h_fig = int(self.fig.get_figheight() * self.fig.dpi)
        img = Image.frombuffer('RGBA', (w_fig, h_fig), buf, 'raw', 'RGBA', 0, 1)

        # Накладываем оверлей
        if self.overlay is not None:
            overlay_resized = self.overlay.resize((w_fig, h_fig))
            img = Image.alpha_composite(img, overlay_resized)

        # Отображаем результат на tk canvas
        import io
        from PIL import ImageTk
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        self._tk_img = ImageTk.PhotoImage(Image.open(bio))
        widget = self.canvas.get_tk_widget()
        widget.create_image(0, 0, anchor='nw', image=self._tk_img)

    def _update_plot(self):
        self.ax.clear()
        df = dataset.df
        x = self.x_col
        y = self.y_col
        x_num = x in NUMERIC_COLS
        y_num = y in NUMERIC_COLS

        import matplotlib.cm as cm

        if x == y and x_num:
            n, bins, patches = self.ax.hist(df[x], bins=10)
            cmap_obj = cm.get_cmap(self.cmap)
            for i, patch in enumerate(patches):
                patch.set_facecolor(cmap_obj(i / 10))
            self.ax.set_xlabel(x)
            self.ax.set_ylabel("Частота")
            self.ax.set_title(f"Гистограмма: {x}")

        elif x == y and not x_num:
            counts = df[x].value_counts()
            colors = [cm.get_cmap(self.cmap)(i / len(counts)) for i in range(len(counts))]
            self.ax.pie(counts.values, labels=counts.index, colors=colors, autopct='%1.1f%%')
            self.ax.set_title(f"Круговая диаграмма: {x}")

        elif x_num and not y_num:
            categories = df[y].unique()
            data = [df[df[y] == cat][x].dropna().values for cat in categories]
            bp = self.ax.boxplot(data, labels=categories, patch_artist=True)
            colors = [cm.get_cmap(self.cmap)(i / len(categories)) for i in range(len(categories))]
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
            self.ax.set_xlabel(y)
            self.ax.set_ylabel(x)
            self.ax.set_title(f"Коробочная диаграмма: {x} по {y}")
            self.ax.tick_params(axis='x', rotation=45)

        elif not x_num and y_num:
            counts = df[x].value_counts()
            colors = [cm.get_cmap(self.cmap)(i / len(counts)) for i in range(len(counts))]
            self.ax.bar(counts.index, counts.values, color=colors)
            self.ax.set_xlabel(x)
            self.ax.set_ylabel("Количество")
            self.ax.set_title(f"Столбчатая диаграмма: {x}")
            self.ax.tick_params(axis='x', rotation=45)

        else:
            self.ax.scatter(df[x], df[y], marker=MARKER, alpha=0.6,
                            c=range(len(df)), cmap=self.cmap)
            self.ax.set_xlabel(x)
            self.ax.set_ylabel(y)
            self.ax.set_title(f"{x} vs {y}")

        self.fig.tight_layout()
        self.canvas.draw()

        # Сбрасываем оверлей и историю мазков при обновлении графика —
        # новый график не должен "помнить" рисунок со старого
        w, h = self._get_canvas_size()
        if w > 1 and h > 1:
            self.overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.strokes = []
        self.current_stroke = []

    def _on_close(self):
        """Закрывает фигуру matplotlib и полностью завершает процесс."""
        plt.close(self.fig)
        self.root.quit()
        self.root.destroy()

    def _save(self):
        """Сохраняем финальное изображение (график + рисунок)."""
        now = datetime.now()
        filename = f"graph{now.strftime('%H_%M_%S')}.png"
        self.fig.canvas.draw()
        buf = self.fig.canvas.buffer_rgba()
        w_fig = int(self.fig.get_figwidth() * self.fig.dpi)
        h_fig = int(self.fig.get_figheight() * self.fig.dpi)
        img = Image.frombuffer('RGBA', (w_fig, h_fig), buf, 'raw', 'RGBA', 0, 1)
        if self.overlay is not None:
            overlay_resized = self.overlay.resize((w_fig, h_fig))
            img = Image.alpha_composite(img, overlay_resized)
        img.convert('RGB').save(filename)
        print(f"График сохранён: {filename}")


if __name__ == '__main__':
    root = tk.Tk()
    app = DrawApp(root)
    root.mainloop()