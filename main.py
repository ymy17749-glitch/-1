# -*- coding: utf-8 -*-
"""
触屏扫雷 · Kivy 版
可直接用 Buildozer 打包成安卓 APK。

操作方式：
    - 轻点格子    -> 翻开
    - 长按格子    -> 插旗 / 取消插旗
    - 按住拖动    -> 滑动浏览棋盘（大地图）
"""

import os
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Ellipse, Triangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

# 系统中文字体候选路径（安卓 / 桌面都会依次尝试）
CJK_FONT_CANDIDATES = [
    "/system/fonts/SysSans-Hans-Regular.ttf",
    "/system/fonts/SysFont-Hans-Regular.ttf",
    "/system/fonts/SysSans-Hant-Regular.ttf",
    "/system/fonts/SysFont-Regular.ttf",
    "/system/fonts/NotoSansCJK-Regular.ttc",
    "/system/fonts/NotoSerifCJK-Regular.ttc",
    "/system/fonts/FZZWXBTOT_Uni.ttf",
    "/system/fonts/DroidSansFallback.ttf",
    "/system/fonts/DroidSans.ttf",
]


def register_cjk_font():
    """注册中文字体，解决 Kivy 默认字体没有中文字形导致“界面没有字”的问题"""
    from kivy.core.text import LabelBase

    for path in CJK_FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                # 覆盖默认字体名 Roboto，让所有控件（含粗体）都使用该中文字体
                LabelBase.register(
                    name="Roboto",
                    fn_regular=path,
                    fn_bold=path,
                    fn_italic=path,
                    fn_bolditalic=path,
                )
                print("[字体] 已加载中文字体:", path)
                return path
            except Exception as exc:  # noqa: BLE001
                print("[字体] 加载失败:", path, exc)
    print("[字体] 未找到可用的中文字体，中文可能显示为空白")
    return None


# 经典扫雷数字配色（1~8）
NUMBER_COLORS = {
    1: (0.0, 0.0, 1.0, 1),
    2: (0.0, 0.5, 0.0, 1),
    3: (1.0, 0.0, 0.0, 1),
    4: (0.0, 0.0, 0.5, 1),
    5: (0.5, 0.0, 0.0, 1),
    6: (0.0, 0.5, 0.5, 1),
    7: (0.0, 0.0, 0.0, 1),
    8: (0.5, 0.5, 0.5, 1),
}

LONG_PRESS_TIME = 0.4     # 长按判定时间（秒）
MOVE_THRESHOLD = dp(10)   # 手指移动超过该距离则视为滑动


class Cell(Label):
    """单个雷区格子：直接继承 Label，文字自动居中；用图形绘制旗子/地雷"""

    def __init__(self, row, col, **kwargs):
        super().__init__(**kwargs)
        self.row = row
        self.col = col
        self.revealed = False
        self.flagged = False
        self.is_mine = False
        self.adjacent = 0

        self.halign = "center"
        self.valign = "middle"

        # 背景
        with self.canvas.before:
            self.bg_color = Color(0.74, 0.74, 0.74, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._on_layout, size=self._on_layout)
        self._on_layout()
        self.refresh()

    def _on_layout(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        # 让文字严格在格子内居中
        self.text_size = self.size
        self._redraw_marks()

    def _redraw_marks(self):
        """用图形绘制地雷（黑圆）与旗子（红旗），避免依赖 emoji 字体"""
        self.canvas.after.clear()
        x, y = self.pos
        w, h = self.size

        if self.revealed and self.is_mine:
            with self.canvas.after:
                Color(0.12, 0.12, 0.12, 1)
                d = min(w, h) * 0.62
                Ellipse(pos=(x + (w - d) / 2, y + (h - d) / 2), size=(d, d))
        elif (not self.revealed) and self.flagged:
            with self.canvas.after:
                # 旗杆
                Color(0.25, 0.15, 0.05, 1)
                pw = max(2.0, w * 0.07)
                Rectangle(pos=(x + w * 0.46, y + h * 0.18), size=(pw, h * 0.62))
                # 旗面
                Color(0.9, 0.1, 0.1, 1)
                Triangle(
                    points=[
                        x + w * 0.46 + pw, y + h * 0.80,
                        x + w * 0.46 + pw, y + h * 0.50,
                        x + w * 0.86,       y + h * 0.65,
                    ]
                )

    def refresh(self):
        if self.revealed:
            if self.is_mine:
                self.bg_color.rgba = (1.0, 0.62, 0.62, 1)
                self.text = ""
            else:
                self.bg_color.rgba = (0.86, 0.86, 0.86, 1)
                if self.adjacent > 0:
                    self.text = str(self.adjacent)
                    self.color = NUMBER_COLORS.get(self.adjacent, (0, 0, 0, 1))
                else:
                    self.text = ""
        else:
            self.bg_color.rgba = (0.74, 0.74, 0.74, 1)
            self.text = ""
        self._redraw_marks()


class BoardScrollView(ScrollView):
    """支持手指拖动滑动 + 轻点 + 长按 的滚动视图"""

    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self._start_pos = None
        self._moved = False
        self._fired = False
        self._long_event = None
        self.scroll_type = ["bars", "content"]

    def _inside(self, px, py):
        wx, wy = self.to_window(self.x, self.y)
        return wx <= px <= wx + self.width and wy <= py <= wy + self.height

    def on_touch_down(self, touch):
        if self._inside(touch.x, touch.y):
            self._start_pos = (touch.x, touch.y)
            self._moved = False
            self._fired = False
            if self._long_event:
                self._long_event.cancel()
            self._long_event = Clock.schedule_once(
                lambda dt: self._fire_long(touch), LONG_PRESS_TIME
            )
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._start_pos is not None:
            dx = touch.x - self._start_pos[0]
            dy = touch.y - self._start_pos[1]
            if (dx * dx + dy * dy) ** 0.5 > MOVE_THRESHOLD:
                self._moved = True
                if self._long_event:
                    self._long_event.cancel()
                    self._long_event = None
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._long_event:
            self._long_event.cancel()
            self._long_event = None
        if self._start_pos is not None and not self._moved and not self._fired:
            self.game.handle_tap(*self._start_pos)
        self._start_pos = None
        self._moved = False
        self._fired = False
        return super().on_touch_up(touch)

    def _fire_long(self, touch):
        self._long_event = None
        if not self._moved and self._start_pos is not None:
            self._fired = True
            self.game.handle_long_press(*self._start_pos)


class Game(FloatLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.difficulties = {
            "简单 (7×7)": {"rows": 7, "cols": 7, "mines": 10},
            "中级 (10×10)": {"rows": 10, "cols": 10, "mines": 15},
            "高级 (15×15)": {"rows": 15, "cols": 15, "mines": 30},
        }
        self.rows = 7
        self.cols = 7
        self.mines_count = 10
        self.cell_px = dp(40)
        self.gap = dp(1)

        self.board = []
        self.revealed = []
        self.flagged = []
        self.cells = {}
        self.game_over = False
        self.first_click = True

        self.timer_seconds = 0
        self.timer_running = False
        self.timer_event = None
        self._scrolled_initial = False

        with self.canvas.before:
            Color(0.92, 0.92, 0.92, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._bg_update, size=self._bg_update)

        self.show_menu()

    def _bg_update(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    # ================= 开始菜单 =================
    def show_menu(self):
        self.stop_timer()
        self.clear_widgets()

        wrapper = BoxLayout(
            orientation="vertical",
            padding=dp(30),
            spacing=dp(14),
            size_hint=(1, 1),
        )
        wrapper.add_widget(Widget())  # 顶部弹性占位
        wrapper.add_widget(
            Label(
                text="触屏扫雷",
                font_size=dp(30),
                bold=True,
                color=(0.2, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(60),
            )
        )
        wrapper.add_widget(
            Label(
                text="轻点翻开 · 长按插旗 · 拖动滑动",
                font_size=dp(14),
                color=(0.4, 0.4, 0.4, 1),
                size_hint_y=None,
                height=dp(30),
            )
        )

        for name in self.difficulties.keys():
            btn = Button(
                text=name,
                font_size=dp(18),
                size_hint_y=None,
                height=dp(52),
                background_normal="",
                background_color=(0.29, 0.56, 0.89, 1),
                color=(1, 1, 1, 1),
            )
            btn.bind(on_release=lambda inst, n=name: self.start_game(n))
            wrapper.add_widget(btn)

        wrapper.add_widget(Widget())  # 底部弹性占位
        self.add_widget(wrapper)

    # ================= 游戏界面 =================
    def start_game(self, difficulty_name):
        cfg = self.difficulties[difficulty_name]
        self.rows = cfg["rows"]
        self.cols = cfg["cols"]
        self.mines_count = cfg["mines"]
        self._build_ui()
        self.reset_game()

    def _build_ui(self):
        self.clear_widgets()
        self._scrolled_initial = False

        root_box = BoxLayout(orientation="vertical", spacing=dp(2))

        # ---- 顶部状态栏 ----
        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6), padding=dp(4))
        menu_btn = Button(
            text="菜单", font_size=dp(15), size_hint_x=None, width=dp(72),
            background_normal="", background_color=(0.6, 0.6, 0.6, 1),
        )
        menu_btn.bind(on_release=lambda *a: self.show_menu())
        top.add_widget(menu_btn)

        self.timer_label = Label(text="0 秒", font_size=dp(16), color=(0.8, 0, 0, 1))
        top.add_widget(self.timer_label)

        self.smiley = Button(
            text=":)", font_size=dp(18), size_hint_x=None, width=dp(56),
            background_normal="", background_color=(0.85, 0.85, 0.85, 1),
        )
        self.smiley.bind(on_release=lambda *a: self.reset_game())
        top.add_widget(self.smiley)
        root_box.add_widget(top)

        # ---- 棋盘区域 ----
        board_area = FloatLayout()
        self.sv = BoardScrollView(self)
        board_area.add_widget(self.sv)
        root_box.add_widget(board_area)
        self.add_widget(root_box)

        # 计算格子尺寸：尽量大，但不小于 dp(32)、不大于 dp(56)
        self.cell_px = self._compute_cell_size()
        self.gap = dp(1)

        # 网格：直接作为 ScrollView 的子控件
        self.grid = GridLayout(
            cols=self.cols,
            spacing=self.gap,
            size_hint=(None, None),
        )
        self.cells = {}
        for r in range(self.rows):
            for c in range(self.cols):
                cell = Cell(
                    r, c,
                    size_hint=(None, None),
                    size=(self.cell_px, self.cell_px),
                    font_size=dp(20),
                    bold=True,
                )
                self.grid.add_widget(cell)
                self.cells[(r, c)] = cell

        # 让网格尺寸跟随其内容
        self.grid.bind(minimum_size=self._on_grid_min_size)
        self.sv.add_widget(self.grid)

        # 视口尺寸变化时重新计算内边距（实现小棋盘居中 / 大棋盘可滚动）
        self.sv.bind(size=self._relayout)
        Clock.schedule_once(self._relayout, 0.1)

    def _on_grid_min_size(self, instance, value):
        instance.size = value

    def _board_size(self):
        bw = self.cols * self.cell_px + (self.cols - 1) * self.gap
        bh = self.rows * self.cell_px + (self.rows - 1) * self.gap
        return bw, bh

    def _relayout(self, *args):
        if not hasattr(self, "grid"):
            return
        bw, bh = self._board_size()
        vw, vh = self.sv.width, self.sv.height
        # 棋盘比视口小时，用内边距把它居中；比视口大时内边距为 0
        pw = max(0.0, (vw - bw) / 2.0)
        ph = max(0.0, (vh - bh) / 2.0)
        self.grid.padding = [pw, ph, pw, ph]
        # 内容比视口高时，初始滚动到顶部
        if bh > vh and not self._scrolled_initial:
            self._scrolled_initial = True
            Clock.schedule_once(lambda dt: setattr(self.sv, "scroll_y", 1), 0)

    def _compute_cell_size(self):
        avail_w = Window.width * 0.94
        avail_h = Window.height * 0.74
        fit = min(avail_w / self.cols, avail_h / self.rows)
        return max(min(fit, dp(56)), dp(32))

    # ================= 计时器 =================
    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.timer_seconds = 0
            self.timer_event = Clock.schedule_interval(self._tick, 1.0)

    def _tick(self, dt):
        self.timer_seconds += 1
        if hasattr(self, "timer_label"):
            self.timer_label.text = f"{self.timer_seconds} 秒"

    def stop_timer(self):
        self.timer_running = False
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

    # ================= 重置 / 布雷 =================
    def reset_game(self):
        self.stop_timer()
        self.timer_seconds = 0
        if hasattr(self, "timer_label"):
            self.timer_label.text = "0 秒"
        if hasattr(self, "smiley"):
            self.smiley.text = ":)"

        self.game_over = False
        self.first_click = True
        self.board = [[0] * self.cols for _ in range(self.rows)]
        self.revealed = [[False] * self.cols for _ in range(self.rows)]
        self.flagged = [[False] * self.cols for _ in range(self.rows)]

        for cell in self.cells.values():
            cell.revealed = False
            cell.flagged = False
            cell.is_mine = False
            cell.adjacent = 0
            cell.refresh()

    def place_mines(self, safe_r, safe_c):
        placed = 0
        while placed < self.mines_count:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            if abs(r - safe_r) <= 1 and abs(c - safe_c) <= 1:
                continue
            if self.board[r][c] != -1:
                self.board[r][c] = -1
                placed += 1
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1:
                    continue
                count = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if self.board[nr][nc] == -1:
                                count += 1
                self.board[r][c] = count
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[(r, c)]
                cell.is_mine = self.board[r][c] == -1
                cell.adjacent = 0 if self.board[r][c] == -1 else self.board[r][c]

    # ================= 触摸交互逻辑 =================
    def _find_cell(self, px, py):
        for (r, c), cell in self.cells.items():
            wx, wy = cell.to_window(cell.x, cell.y)
            if wx <= px <= wx + cell.width and wy <= py <= wy + cell.height:
                return (r, c)
        return None

    def handle_tap(self, px, py):
        if self.game_over:
            return
        pos = self._find_cell(px, py)
        if pos is None:
            return
        r, c = pos
        if self.flagged[r][c] or self.revealed[r][c]:
            return

        if self.first_click:
            self.start_timer()
            self.place_mines(r, c)
            self.first_click = False

        if self.board[r][c] == -1:
            self._lose(r, c)
            return
        self._reveal(r, c)
        self._check_win()

    def handle_long_press(self, px, py):
        if self.game_over:
            return
        pos = self._find_cell(px, py)
        if pos is None:
            return
        r, c = pos
        if self.revealed[r][c]:
            return
        self.flagged[r][c] = not self.flagged[r][c]
        self.cells[(r, c)].flagged = self.flagged[r][c]
        self.cells[(r, c)].refresh()

    def _reveal(self, r, c):
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        if self.revealed[r][c] or self.flagged[r][c]:
            return
        self.revealed[r][c] = True
        cell = self.cells[(r, c)]
        cell.revealed = True
        cell.adjacent = 0 if self.board[r][c] == -1 else self.board[r][c]
        cell.refresh()

        if self.board[r][c] == 0:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    self._reveal(r + dr, c + dc)

    def _lose(self, r, c):
        self.stop_timer()
        self.game_over = True
        self.smiley.text = ":("
        for (rr, cc), cell in self.cells.items():
            if self.board[rr][cc] == -1:
                cell.revealed = True
                cell.refresh()
            elif self.flagged[rr][cc]:
                cell.flagged = False
                cell.refresh()
        self._show_popup(
            "游戏结束", f"很遗憾，你踩到雷了！\n用时：{self.timer_seconds} 秒"
        )

    def _check_win(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != -1 and not self.revealed[r][c]:
                    return
        self.stop_timer()
        self.game_over = True
        self.smiley.text = "8)"
        for (rr, cc), cell in self.cells.items():
            if self.board[rr][cc] == -1 and not cell.flagged:
                cell.flagged = True
                cell.refresh()
        self._show_popup(
            "恭喜", f"太棒了，你成功排除了所有雷！\n总用时：{self.timer_seconds} 秒"
        )

    def _show_popup(self, title, msg):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        content.add_widget(Label(text=msg, halign="center"))
        btn = Button(
            text="确定", size_hint_y=None, height=dp(46),
            background_normal="", background_color=(0.29, 0.56, 0.89, 1),
            color=(1, 1, 1, 1),
        )
        content.add_widget(btn)
        popup = Popup(
            title=title, content=content, size_hint=(0.8, 0.38),
            auto_dismiss=True,
        )
        btn.bind(on_release=popup.dismiss)
        popup.open()


class MinesweeperApp(App):
    def build(self):
        self.title = "触屏扫雷"
        Window.clearcolor = (0.92, 0.92, 0.92, 1)
        # 关键：在创建任何控件之前先注册中文字体
        register_cjk_font()
        return Game()


if __name__ == "__main__":
    MinesweeperApp().run()