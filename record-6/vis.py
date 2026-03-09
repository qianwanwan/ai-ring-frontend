import os
import random
from datetime import datetime
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from tkinter import messagebox

from config import RecordConfig
from log import Log


MIN_VALID_DURATION_S = 0.4


# ---------- util ----------
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def session_logfile() -> str:
    ensure_dir(RecordConfig.record_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(RecordConfig.record_dir, f"session_{ts}.log")


# ---------- trial builder ----------
def build_trials_single(body_part: str, content: str, speed: str):
    """
    单组设置展开 trials：
      - number: 10 * RecordConfig.number_times
      - alphabet: 52 * RecordConfig.alphabet_times
      - word: RecordConfig.word_times
      - password: RecordConfig.password_times（每条为长度为 RecordConfig.password_length 的随机数字串）
    speed: fast / slow（整组同速）
    """
    num_cycles = RecordConfig.number_times
    alpha_cycles = RecordConfig.alphabet_times
    word_count = RecordConfig.word_times
    password_count = RecordConfig.password_times
    password_length = RecordConfig.password_length

    numbers_base = RecordConfig.number_list
    alphabet_base = RecordConfig.alphabet_list_upper + RecordConfig.alphabet_list_lower

    def repeat_cycles(seq, cycles):
        ret = []
        for _ in range(cycles):
            random.shuffle(seq)
            ret.extend(seq)
        return ret

    def numbers_stimuli():
        return repeat_cycles(numbers_base, num_cycles)

    def alphabet_stimuli():
        return repeat_cycles(alphabet_base, alpha_cycles)

    def words_stimuli(n):
        wl = RecordConfig.word_list or []
        if not wl:
            return [""] * n
        if len(wl) >= n:
            return random.sample(wl, k=n)
        return random.choices(wl, k=n)

    def gestures_stimuli():
        gl = getattr(RecordConfig, 'gesture_list', []) or []
        # 不重复循环：每组直接使用 command.txt 中的所有手势，顺序打乱
        if not gl:
            return [""]
        seq = list(gl)
        random.shuffle(seq)
        return seq

    def password_stimuli(n):
        upper_bound = 10 ** password_length
        fmt = f"{{:0{password_length}d}}"
        return [fmt.format(random.randrange(upper_bound)) for _ in range(n)]

    if content == "number":
        stimuli = numbers_stimuli()
    elif content == "alphabet":
        stimuli = alphabet_stimuli()
    elif content == "password":
        stimuli = password_stimuli(password_count)
    elif content == "gesture":
        stimuli = gestures_stimuli()
    else:  # word
        stimuli = words_stimuli(word_count)

    speeds_seq = [speed] * len(stimuli)

    trials = []
    for i, stim in enumerate(stimuli):
        trials.append({
            "body_part": body_part,
            "content": content,
            "speed": speeds_seq[i],
            "stimulus": stim,
        })
    return trials


# ---------- setup dialog (OptionMenu) ----------
class SetupDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("实验设置")
        self.resizable(False, False)
        self.geometry("600x240")
        self.configure(bg="#F6F7F9")
        self.selection = None

        # palette + fonts
        self.COL_BG = "#F6F7F9"
        self.COL_PANEL = "#FFFFFF"
        self.COL_TEXT = "#111827"
        self.COL_MUTED = "#6B7280"
        self.COL_LINE = "#E5E7EB"
        self.font_title = tkfont.Font(family="Arial", size=18, weight="bold")
        self.font_body = tkfont.Font(family="Arial", size=12)

        self.body_parts = ["board", "palm", "thigh", "pocket", "in-air"]
        # 默认只保留手势内容选项（从 command.txt 加载）
        self.contents = ["gesture", "number", "password", "alphabet", "word"]
        self.speeds = ["medium", "fast", "slow"]

        # container
        wrap = tk.Frame(self, bg=self.COL_BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(wrap, text="选择本次实验参数", font=self.font_title, fg=self.COL_TEXT, bg=self.COL_BG)\
            .pack(anchor="w")
        tk.Label(wrap, text="仅设置一组（部位/内容/速度），开始后自动展开为多条试次。",
                 font=self.font_body, fg=self.COL_MUTED, bg=self.COL_BG)\
            .pack(anchor="w", pady=(6, 12))

        card = tk.Frame(wrap, bg=self.COL_PANEL, highlightthickness=1, highlightbackground=self.COL_LINE)
        card.pack(fill="x")

        row = tk.Frame(card, bg=self.COL_PANEL)
        row.pack(fill="x", padx=14, pady=14)

        # fields with OptionMenu
        self.body_var = tk.StringVar(value="board")
        self.content_var = tk.StringVar(value="gesture")
        self.speed_var = tk.StringVar(value="medium")

        self._option_field(row, 0, "部位", self.body_var, self.body_parts)
        self._option_field(row, 1, "内容", self.content_var, self.contents)
        self._option_field(row, 2, "速度", self.speed_var, self.speeds)

        # buttons
        btns = tk.Frame(wrap, bg=self.COL_BG)
        btns.pack(fill="x", pady=(12, 0))
        tk.Button(btns, text="开始实验", width=12, command=self.on_ok)\
            .pack(side="right")
        tk.Button(btns, text="取消退出", width=10, command=self.on_cancel)\
            .pack(side="right", padx=(0, 8))

        self.bind("<Escape>", lambda e: self.on_cancel())
        self.grab_set()

    def _option_field(self, parent, col, title, var, options):
        col_frame = tk.Frame(parent, bg=self.COL_PANEL)
        col_frame.grid(row=0, column=col, padx=(0 if col == 0 else 16, 0))
        tk.Label(col_frame, text=title, bg=self.COL_PANEL, fg=self.COL_MUTED, font=("Arial", 11)).pack(anchor="w")
        # OptionMenu（原生下拉，点击即选）
        om = tk.OptionMenu(col_frame, var, *options)
        om.config(width=12, bg=self.COL_PANEL, fg=self.COL_TEXT, highlightthickness=1, highlightbackground=self.COL_LINE)
        om["menu"].config(bg="#FFFFFF", fg=self.COL_TEXT, activebackground="#E5E7EB", activeforeground=self.COL_TEXT)
        om.pack(anchor="w", pady=(4, 0))
        return om

    def on_ok(self):
        body = self.body_var.get().strip()
        content = self.content_var.get().strip()
        speed = self.speed_var.get().strip()
        if body not in self.body_parts or content not in self.contents or speed not in self.speeds:
            messagebox.showerror("错误", "请选择合法选项。", parent=self)
            return
        self.selection = {"body_part": body, "content": content, "speed": speed}
        self.destroy()

    def on_cancel(self):
        self.selection = None
        self.destroy()

    def get_selection(self):
        return self.selection


# ---------- main UI ----------
class ExperimentUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.index = 0
        self.recording = False
        self.logger = Log(session_logfile())
        self.total_written = 0
        self.total_qualified = 0
        self.warning_active = False
        self.warning_text = ""
        self.all_trials = []
        # 构建试次：仅使用手势内容，按速度分为三组（慢/中/快）
        # 每组包含 command.txt 中的所有手势（不重复），保证每组为 31 个手势
        body_default = RecordConfig.body_parts[0] if RecordConfig.body_parts else "board"
        for speed in RecordConfig.speeds:
            self.all_trials.append(build_trials_single(body_default, "gesture", speed))
        self.trial_end = False
        self.current_trial_index = 0
        self.trials = self.all_trials[self.current_trial_index]
        self.trial_total = len(self.all_trials)

        # palette
        self.COL_BG = "#F6F7F9"
        self.COL_PANEL = "#FFFFFF"
        self.COL_TEXT = "#111827"
        self.COL_MUTED = "#6B7280"
        self.COL_LINE = "#E5E7EB"
        self.COL_ACCENT = "#3B82F6"
        self.COL_GO = "#16A34A"
        self.COL_IDLE = "#9CA3AF"

        self._setup_root()
        self._setup_fonts()
        self._setup_style()
        self._build_layout()
        self._bind_keys()
        self.update_view()

    def _setup_root(self):
        self.root.title("WR RecordVis")
        self.root.geometry("1040x700")
        self.root.configure(bg=self.COL_BG)
        self.root.minsize(960, 620)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def _setup_fonts(self):
        self.font_title = tkfont.Font(family="Times New Roman", size=24, weight="bold")
        self.font_h2 = tkfont.Font(family="Times New Roman", size=16, weight="bold")
        self.font_body = tkfont.Font(family="Times New Roman", size=14)
        self.font_small = tkfont.Font(family="Times New Roman", size=11)
        self.font_stim = tkfont.Font(family="Times New Roman", size=72, weight="bold")
        self.font_transition = tkfont.Font(family="Times New Roman", size=26, weight="bold")

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Card.TFrame", background=self.COL_PANEL)
        style.configure("Muted.TLabel", background=self.COL_PANEL, foreground=self.COL_MUTED, font=self.font_small)
        style.configure("Body.TLabel", background=self.COL_PANEL, foreground=self.COL_TEXT, font=self.font_body)
        style.configure("H2.TLabel", background=self.COL_PANEL, foreground=self.COL_TEXT, font=self.font_h2)
        style.configure("TitlePage.TLabel", background=self.COL_BG, foreground=self.COL_TEXT, font=self.font_title)
        style.configure("TProgressbar", background=self.COL_ACCENT, troughcolor=self.COL_LINE)

    def _build_layout(self):
        header = ttk.Frame(self.root, style="Card.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, text="可视化实验记录平台", style="TitlePage.TLabel").grid(row=0, column=0, sticky="w")
        lbl_kbd = ttk.Label(header, text="SPACE 开始/结束   •   ESC 退出   •   F11 全屏   •   BACKSPACE 退回上一试次", style="TitlePage.TLabel")
        lbl_kbd.configure(font=self.font_small, foreground=self.COL_MUTED)
        lbl_kbd.grid(row=0, column=1, sticky="e")

        card = ttk.Frame(self.root, style="Card.TFrame")
        card.grid(row=1, column=0, sticky="nsew", padx=28, pady=12)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        meta = ttk.Frame(card, style="Card.TFrame")
        meta.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        for c in range(8):
            meta.grid_columnconfigure(c, weight=1)

        self.meta_body = self._meta_block(meta, 0, "部位", "")
        self.meta_content = self._meta_block(meta, 1, "内容", "")
        self.meta_speed = self._meta_block(meta, 2, "速度", "")
        self.meta_progress = self._meta_block(meta, 3, "进度", "")
        self.meta_allt = self._meta_block(meta, 4, "总进度", "")
        self.meta_written = self._meta_block(meta, 5, "已写", "0")
        self.meta_ok = self._meta_block(meta, 6, "合格", "0")
        self.meta_ok_rate = self._meta_block(meta, 7, "合格率", "-")

        line = tk.Frame(card, height=1, bg=self.COL_LINE, bd=0, highlightthickness=0)
        line.grid(row=0, column=0, sticky="ew", padx=24, pady=(14, 0))

        stim_area = ttk.Frame(card, style="Card.TFrame")
        stim_area.grid(row=1, column=0, sticky="nsew", padx=24, pady=8)
        stim_area.grid_columnconfigure(0, weight=1)
        stim_area.grid_rowconfigure(0, weight=1)
        self.lbl_stim = tk.Label(stim_area, text="", font=self.font_stim, fg=self.COL_TEXT, bg=self.COL_PANEL)
        self.lbl_stim.grid(row=0, column=0, sticky="nsew")

        status = ttk.Frame(card, style="Card.TFrame")
        status.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 20))
        status.grid_columnconfigure(1, weight=1)
        self.status_dot = tk.Canvas(status, width=14, height=14, bg=self.COL_PANEL, highlightthickness=0)
        self.status_dot.grid(row=0, column=0, padx=(0, 8))
        self.lbl_status = ttk.Label(status, text="", style="Body.TLabel")
        self.lbl_status.grid(row=0, column=1, sticky="w")

        footer = ttk.Frame(self.root, style="Card.TFrame")
        footer.grid(row=2, column=0, sticky="ew", padx=28, pady=(12, 24))
        footer.grid_columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(footer, orient="horizontal", mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew")

    def _meta_block(self, parent, col, title, value):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=0, column=col, sticky="w", padx=(0 if col == 0 else 16, 0))
        ttk.Label(frame, text=title, style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        lbl = ttk.Label(frame, text=value, style="H2.TLabel")
        lbl.grid(row=1, column=0, sticky="w", pady=(2, 0))
        return lbl

    def _bind_keys(self):
        self.root.bind("<space>", self.on_space)
        self.root.bind("<Escape>", self.on_escape)
        self.root.bind("<F11>", self.on_toggle_fullscreen)
        self.root.bind("<BackSpace>", self.on_backspace)

    def current_trial(self):
        return self.trials[self.index] if self.index < len(self.trials) else None
    
    def update_trial(self):
        self.current_trial_index += 1
        if self.current_trial_index >= len(self.all_trials):
            self.trial_end = True
            self.trials = []
        else:
            self.trials = self.all_trials[self.current_trial_index]
            self.index = 0
        

    def _label_map(self):
        return {
            "gesture": "手势",
            "number": "数字",
            "alphabet": "字母",
            "word": "单词",
            "password": "数字串",
            "thigh": "大腿",
            "pocket": "上衣口袋",
            "palm": "手掌",
            "board": "手写板",
            "in-air": "空中",
            "fast": "快",
            "medium": "中",
            "slow": "慢",
        }

    def _trial_key(self, t):
        if not t:
            return None
        return (t.get("body_part"), t.get("content"), t.get("speed"))

    def _format_key(self, key):
        if not key:
            return "-"
        body_part, content, speed = key
        lm = self._label_map()
        return f"{lm.get(body_part, body_part)} / {lm.get(content, content)} / {lm.get(speed, speed)}"

    def _diff_key(self, cur_key, next_key):
        if not cur_key or not next_key:
            return []
        lm = self._label_map()
        changes = []
        labels = [("部位", 0), ("内容", 1), ("速度", 2)]
        for label, idx in labels:
            if cur_key[idx] != next_key[idx]:
                before = lm.get(cur_key[idx], cur_key[idx])
                after = lm.get(next_key[idx], next_key[idx])
                changes.append(f"{label} {before}→{after}")
        return changes

    def update_view(self):
        if self.trial_end:
            self._set_status(False, "所有测试结束，按ESC退出")
            return
        t = self.current_trial()
        total = len(self.trials)
        lm = self._label_map()

        self.meta_written.config(text=str(self.total_written))
        self.meta_ok.config(text=str(self.total_qualified))
        if self.total_written:
            self.meta_ok_rate.config(text=f"{(self.total_qualified / self.total_written) * 100:.1f}%")
        else:
            self.meta_ok_rate.config(text="-")

        if not t:
            self.logger.save_log()

            cur_group = self.trials[0] if isinstance(self.trials, list) and self.trials else None
            cur_key = self._trial_key(cur_group)
            next_group = None
            if (self.current_trial_index + 1) < len(self.all_trials):
                nxt = self.all_trials[self.current_trial_index + 1]
                next_group = nxt[0] if nxt else None
            next_key = self._trial_key(next_group)

            self.meta_body.config(text="-")
            self.meta_content.config(text="-")
            self.meta_speed.config(text="-")
            self.meta_progress.config(text=f"{total}/{total}")
            self.meta_allt.config(text=f"{min(self.current_trial_index + 1, self.trial_total)}/{self.trial_total}")
            self.progress["value"] = 100

            if next_key is None:
                self.lbl_stim.config(text="完成", font=self.font_transition)
                self._set_status(False, "所有测试结束，按ESC退出")
                return

            changes = self._diff_key(cur_key, next_key)
            change_hint = ("，".join(changes)) if changes else ""
            self.lbl_stim.config(
                text=f"{self._format_key(next_key)}\n{change_hint}",
                font=self.font_transition,
            )
            self._set_status(False, "本轮测试结束，按空格进入下一轮")
            return
        self.meta_body.config(text=lm.get(t["body_part"], t["body_part"]))
        self.meta_content.config(text=lm.get(t["content"], t["content"]))
        self.meta_speed.config(text=lm.get(t["speed"], t["speed"]))
        self.meta_progress.config(text=f"{min(self.index + 1, total)}/{total}")
        self.meta_allt.config(text=f"{min(self.current_trial_index + 1, self.trial_total)}/{self.trial_total}")

        # 退出“切换提示”态后恢复大号刺激字体
        if self.lbl_stim.cget("font") != str(self.font_stim):
            self.lbl_stim.config(font=self.font_stim)

        # 始终显示当前试次的刺激（开始/停止时均不改变）
        if t and isinstance(t, dict):
            self.lbl_stim.config(text=f"{t['stimulus']}")

        if self.warning_active:
            self._set_status(self.recording, self.warning_text, is_warning=True)
        else:
            if self.recording:
                self._set_status(True, "正在记录 • 再按空格结束")
            else:
                self._set_status(False, "按空格开始记录")

        pct = int((self.index / total) * 100) if total else 0
        self.progress["value"] = pct

    def _set_status(self, recording: bool, msg: str, *, is_warning: bool = False):
        self.lbl_status.config(text=msg)
        if is_warning:
            self.lbl_status.config(foreground="#DC2626")
        else:
            self.lbl_status.config(foreground=self.COL_TEXT)
        color = self.COL_GO if recording else self.COL_IDLE
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 12, 12, fill=color, outline=color)

    def on_space(self, _event=None):
        if self.trial_end:
            return
        t = self.current_trial()
        if not t:
            self.update_trial()
            self.recording = False
            self.warning_active = False
            if self.trial_end:
                self.update_view()
                return
            self.update_view()
            return
        # 新逻辑：按空格开始采集，再按空格结束采集
        if not self.recording:
            self.recording = True
            self.warning_active = False
            self.logger.record_start()
        else:
            # 结束当前采集并保存
            log = self.logger.save_log_cache(
                body_part=t["body_part"],
                content=t["content"],
                speed=t["speed"],
                trial_index=self.index + 1,
                stimulus=t["stimulus"],
                min_valid_duration_s=MIN_VALID_DURATION_S,
            )
            self.total_written += 1
            if log.get("qualified"):
                self.total_qualified += 1
                self.warning_active = False
            else:
                dur = log.get("duration_s")
                if isinstance(dur, (int, float)):
                    dur_s = f"{dur:.3f}s"
                else:
                    dur_s = "<0.4s"
                self.warning_active = True
                self.warning_text = f"不合格（{dur_s}）：可能按空格时间过短或误操作，可按 Backspace 回退"

            self.index += 1
            # 不自动开始下一个采集，等待用户下一次按空格
            self.recording = False

        self.update_view()

    def on_escape(self, _event=None):
        self.root.quit()
    
    def on_backspace(self, _event=None):
        popped = self.logger.pop_log_cache()
        if popped is not None:
            self.total_written = max(0, self.total_written - 1)
            if popped.get("qualified"):
                self.total_qualified = max(0, self.total_qualified - 1)
        if self.index >= 1:
            self.index -= 1
        self.warning_active = False
        if self.recording:
            self.logger.record_start()
        self.update_view()

    def on_toggle_fullscreen(self, _event=None):
        cur = bool(self.root.attributes("-fullscreen"))
        self.root.attributes("-fullscreen", not cur)


# ---------- app entry ----------
def main():
    random.seed()
    root = tk.Tk()

    # dlg = SetupDialog(root)
    # root.wait_window(dlg)
    # sel = dlg.get_selection()
    # if not sel:
    #     root.destroy()
    #     return
    # for part in RecordConfig.body_parts:
    #     for content in RecordConfig.contents:
    #         for speed in RecordConfig.speeds:
    #             trials = build_trials_single(part, content, speed)
    #             ExperimentUI(root, trials=trials)
    #             root.mainloop()
    ExperimentUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
