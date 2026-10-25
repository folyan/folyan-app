import os
import json
import time
import threading
import contextlib

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.core.text import Label as CoreLabel
from kivy.core.clipboard import Clipboard
from kivy.uix.label import Label
from kivy.metrics import dp, sp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import MDTextField

from rockscissorspaper import check_win
from passwordmanager import generate_password, DEFAULT_ITERATIONS, DEFAULT_SALT

APP_DIR = "/storage/emulated/0/Folyan/FolyanApp/"
SCRIPTS_DIR = APP_DIR + "userscripts/"
USERDATA_DIR = APP_DIR + "userdata/"


def userdata_dir():
    try:
        os.makedirs(USERDATA_DIR, exist_ok=True)
        if os.access(USERDATA_DIR, os.W_OK):
            return USERDATA_DIR
    except OSError:
        pass
    return MDApp.get_running_app().user_data_dir

KV = """
#:set BG (0.055, 0.086, 0.129, 1)

<MenuButton@MDButton>:
    caption: ""
    style: "filled"
    pos_hint: {"center_x": 0.5}

    MDButtonText:
        text: root.caption

<ChoiceCard@MDCard>:
    source: ""
    size_hint: None, None
    size: "100dp", "100dp"
    style: "elevated"
    radius: [20]

    FitImage:
        source: root.source

<MenuScreen>:
    MDBoxLayout:
        id: menu_layout
        orientation: "vertical"
        padding: "20dp"
        spacing: "20dp"
        md_bg_color: BG

<RockPaperScissorsScreen>:
    MDBoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "20dp"
        md_bg_color: BG

        MDIconButton:
            icon: "arrow-left"
            theme_icon_color: "Custom"
            icon_color: (1, 1, 1, 1)
            on_release: root.go_to("menu")

        MDLabel:
            id: label
            text: "Камень, Ножницы, Бумага"
            halign: "center"
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1)

        MDBoxLayout:
            orientation: "horizontal"
            spacing: "10dp"

            ChoiceCard:
                source: "rock.png"
                on_release: root.on_image_click("rock")

            ChoiceCard:
                source: "scissors.png"
                on_release: root.on_image_click("scissors")

            ChoiceCard:
                source: "paper.png"
                on_release: root.on_image_click("paper")

<InterpreterScreen>:
    MDBoxLayout:
        orientation: "vertical"
        padding: ["8dp", "8dp", "8dp", "8dp"]
        spacing: "8dp"
        md_bg_color: BG

        MDIconButton:
            icon: "arrow-left"
            theme_icon_color: "Custom"
            icon_color: (1, 1, 1, 1)
            on_release: root.go_to("menu")

        ScrollView:
            id: scroll_view
            do_scroll_x: False
            MDBoxLayout:
                id: chat_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: "8dp"
                padding: ["12dp", "8dp"]

        MDBoxLayout:
            id: file_box
            size_hint_y: None
            height: "0dp"
            padding: ["8dp", 0]

            MDCard:
                id: file_card
                style: "outlined"
                radius: [16]
                padding: "12dp"
                size_hint_y: None
                height: "0dp"
                opacity: 0
                md_bg_color: (0.094, 0.145, 0.200, 1)

                MDLabel:
                    id: file_name
                    text: ""
                    halign: "center"
                    font_name: "font.ttf"
                    theme_text_color: "Custom"
                    text_color: (1, 1, 1, 1)

        MDBoxLayout:
            orientation: "horizontal"
            spacing: "8dp"
            size_hint_y: None
            height: "56dp"
            padding: ["4dp", 0]

            MDIconButton:
                icon: "paperclip"
                theme_icon_color: "Custom"
                icon_color: (0.165, 0.671, 0.933, 1)
                on_release: root.go_to("files")

            MDTextField:
                id: answer_field
                hint_text: "Ответ или код"
                font_name: "font.ttf"

            MDIconButton:
                icon: "send"
                theme_icon_color: "Custom"
                icon_color: (0.165, 0.671, 0.933, 1)
                on_release: root.answer_clicked()

<FilesScreen>:
    MDBoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "10dp"
        md_bg_color: BG

        MDIconButton:
            icon: "arrow-left"
            theme_icon_color: "Custom"
            icon_color: (1, 1, 1, 1)
            on_release: root.go_to("interpreter")

        ScrollView:
            MDBoxLayout:
                id: files_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: "10dp"

<PasswordScreen>:
    on_pre_enter: root.load_state()

    MDBoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "10dp"
        md_bg_color: BG

        MDIconButton:
            icon: "arrow-left"
            theme_icon_color: "Custom"
            icon_color: (1, 1, 1, 1)
            on_release: root.go_to("menu")

        ScrollView:
            do_scroll_x: False

            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                spacing: "10dp"

                MDLabel:
                    text: "Галочка слева: сохранять это поле в файл"
                    adaptive_height: True
                    theme_text_color: "Custom"
                    text_color: (0.7, 0.7, 0.7, 1)

                MDBoxLayout:
                    size_hint_y: None
                    height: "64dp"
                    spacing: "8dp"

                    MDCheckbox:
                        id: salt_check
                        size_hint: None, None
                        size: "48dp", "48dp"
                        pos_hint: {"center_y": 0.5}
                        on_active: root.save_state()

                    MDTextField:
                        id: salt_field
                        text: "FolyanApp"
                        MDTextFieldHintText:
                            text: "Соль"

                MDBoxLayout:
                    size_hint_y: None
                    height: "64dp"
                    spacing: "8dp"

                    MDCheckbox:
                        id: master_check
                        size_hint: None, None
                        size: "48dp", "48dp"
                        pos_hint: {"center_y": 0.5}
                        on_active: root.on_master_check(self.active)

                    MDTextField:
                        id: master_field
                        password: True
                        MDTextFieldHintText:
                            text: "Мастер-пароль"

                MDLabel:
                    id: master_warn
                    text: "Внимание: мастер-пароль сохранится в файле открытым текстом. Это небезопасно!"
                    size_hint_y: None
                    height: "0dp"
                    opacity: 0
                    theme_text_color: "Custom"
                    text_color: (1, 0.4, 0.4, 1)

                MDBoxLayout:
                    size_hint_y: None
                    height: "64dp"
                    spacing: "8dp"

                    MDCheckbox:
                        id: site_check
                        size_hint: None, None
                        size: "48dp", "48dp"
                        pos_hint: {"center_y": 0.5}
                        on_active: root.save_state()

                    MDTextField:
                        id: site_field
                        MDTextFieldHintText:
                            text: "Сайт"

                MDBoxLayout:
                    size_hint_y: None
                    height: "64dp"
                    spacing: "8dp"

                    MDCheckbox:
                        id: iterations_check
                        size_hint: None, None
                        size: "48dp", "48dp"
                        pos_hint: {"center_y": 0.5}
                        on_active: root.save_state()

                    MDTextField:
                        id: iterations_field
                        input_filter: "int"
                        text: "500000"
                        MDTextFieldHintText:
                            text: "Итерации"

                MenuButton:
                    id: gen_btn
                    caption: "Сгенерировать"
                    on_release: root.generate()

                MDLabel:
                    id: result_label
                    text: "Результат:"
                    halign: "center"
                    adaptive_height: True
                    theme_text_color: "Custom"
                    text_color: (1, 1, 1, 1)

                MenuButton:
                    caption: "Копировать"
                    on_release: root.copy_result()
"""


class OutputPipe:
    def __init__(self, callback):
        self.callback = callback

    def write(self, text):
        if text.strip():
            self.callback(text.strip(), "left")

    def flush(self):
        pass


class BaseScreen(MDScreen):
    def go_to(self, name):
        self.manager.current = name


class MenuScreen(BaseScreen):
    def on_enter(self):
        layout = self.ids.menu_layout
        layout.clear_widgets()

        apps = [
            ("Камень, Ножницы, Бумага", "rps"),
            ("Интерпретатор", "interpreter"),
            ("Менеджер паролей", "passwords"),
            ("Выход", "exit"),
        ]

        apps.sort(key=lambda x: len(x[0]), reverse=True)

        for name, target in apps:
            btn = MDButton(
                MDButtonText(text=name),
                style="filled",
                pos_hint={"center_x": 0.5},
            )
            if target == "exit":
                btn.bind(on_release=lambda x: MDApp.get_running_app().stop())
            else:
                btn.bind(on_release=lambda x, t=target: self.go_to(t))
            layout.add_widget(btn)


class RockPaperScissorsScreen(BaseScreen):
    def on_image_click(self, choice):
        result = check_win(choice)
        results = {"tie": "Ничья!", "win": "Ты выиграл!", "lose": "Ты проиграл!"}
        self.ids.label.text = results.get(result, results["lose"])


class Bubble(MDBoxLayout):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text_value = text
        self.hold_event = None
        self.held = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.held = False
            self.hold_event = Clock.schedule_once(self.on_hold, 0.5)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.hold_event:
                self.hold_event.cancel()
                self.hold_event = None
            return True
        return super().on_touch_up(touch)

    def on_hold(self):
        self.held = True
        self.hold_event = None
        Clipboard.copy(self.text_value)


class InterpreterScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_code = ""
        self.current_name = ""
        self.running = False
        self.answer = None
        self.pending = None
        self.event = threading.Event()

    def on_touch_down(self, touch):
        card = self.ids.file_card
        if card.opacity and card.collide_point(*touch.pos):
            self.clear_file()
            return True
        return super().on_touch_down(touch)

    def load_file(self, path):
        with open(path, encoding="utf-8") as f:
            self.current_code = f.read()
        self.current_name = os.path.basename(path)
        self.set_card(self.current_name)

    def clear_file(self):
        self.current_code = ""
        self.current_name = ""
        self.set_card("")

    def set_card(self, name):
        shown = bool(name)
        self.ids.file_name.text = name
        self.ids.file_card.opacity = 1 if shown else 0
        self.ids.file_card.height = "48dp" if shown else "0dp"
        self.ids.file_box.height = "56dp" if shown else "0dp"

    def answer_clicked(self):
        text = self.ids.answer_field.text.strip()

        if self.running:
            if text:
                self.ids.answer_field.text = ""
                self.add_bubble(text, "right")
                self.answer = text
                self.event.set()
            return

        if self.current_code:
            code = self.current_code
            self.ids.chat_box.clear_widgets()
            self.add_bubble(self.current_name, "right")
            self.pending = text or None
            if text:
                self.add_bubble(text, "right")
        elif text:
            code = text
            self.pending = None
            self.ids.chat_box.clear_widgets()
            self.add_bubble(text, "right")
        else:
            self.add_bubble("Напиши код или выбери файл.", "left")
            return

        self.ids.answer_field.text = ""
        self.running = True
        threading.Thread(target=self.run_code, args=(code,), daemon=True).start()

    def fake_input(self, prompt=""):
        if prompt:
            self.add_bubble(str(prompt), "left")
        if self.pending is not None:
            answer, self.pending = self.pending, None
            return answer
        self.event.clear()
        self.event.wait()
        return self.answer

    def run_code(self, code):
        pipe = OutputPipe(self.add_bubble)
        env = {"__builtins__": __builtins__, "input": self.fake_input}
        try:
            with contextlib.redirect_stdout(pipe):
                exec(code, env)
        except (Exception, SystemExit) as e:
            self.add_bubble(f"Ошибка: {e}", "left")
        self.running = False

    @mainthread
    def add_bubble(self, text, side):
        max_bubble_w = min(Window.width * 0.78, dp(480))
        pad_x = dp(24)
        pad_y = dp(14)
        max_text_w = max_bubble_w - pad_x

        font = "font.ttf" if os.path.exists("font.ttf") else "Roboto"
        font_sz = sp(15)

        core = CoreLabel(text=text, font_size=font_sz, font_name=font)
        core.refresh()
        tw, th = core.texture.size

        if tw > max_text_w:
            is_wrapped = True
            core = CoreLabel(
                text=text,
                font_size=font_sz,
                font_name=font,
                text_size=(max_text_w, None),
            )
            core.refresh()
            tw, th = core.texture.size
            final_tw = max_text_w
            final_th = th
        else:
            is_wrapped = False
            final_tw = tw
            final_th = th

        bubble_w = max(final_tw + pad_x, dp(52))
        bubble_h = max(final_th + pad_y, dp(36))

        radii = (
            [dp(16), dp(16), dp(3), dp(16)]
            if side == "right"
            else [dp(16), dp(16), dp(16), dp(3)]
        )
        color = (
            (0.169, 0.322, 0.471, 1)
            if side == "right"
            else (0.137, 0.161, 0.196, 1)
        )

        bubble = Bubble(
            text,
            size_hint=(None, None),
            size=(bubble_w, bubble_h),
            padding=[dp(12), dp(7), dp(12), dp(7)],
            md_bg_color=color,
            radius=radii,
            pos_hint={"right": 1} if side == "right" else {"x": 0},
        )

        label = Label(
            text=text,
            font_name=font,
            font_size=font_sz,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(final_tw, final_th),
            text_size=(max_text_w, None) if is_wrapped else (None, None),
            halign="left",
            valign="middle",
        )

        bubble.add_widget(label)
        self.ids.chat_box.add_widget(bubble)
        Clock.schedule_once(
            lambda dt: setattr(self.ids.scroll_view, "scroll_y", 0), 0.05
        )


files_screen_code = FilesScreen = type(
    "FilesScreen",
    (BaseScreen,),
    {
        "on_enter": lambda self: [
            self.ids.files_box.clear_widgets(),
            os.makedirs(SCRIPTS_DIR, exist_ok=True),
            [
                self.ids.files_box.add_widget(
                    MDButton(
                        MDButtonText(text=name),
                        on_release=lambda btn, p=os.path.join(SCRIPTS_DIR, name): [
                            self.manager.get_screen("interpreter").load_file(p),
                            setattr(self.manager, "current", "interpreter"),
                        ],
                    )
                )
                for name in sorted(os.listdir(SCRIPTS_DIR))
                if name.endswith(".py")
            ],
        ]
    },
)


class PasswordScreen(BaseScreen):
    FIELDS = ("salt", "master", "site", "iterations")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.busy = False
        self.loading = False
        self.result = ""

    def state_path(self):
        return os.path.join(userdata_dir(), "passwords.json")

    def load_state(self):
        self.loading = True
        try:
            with open(self.state_path(), encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        for name in self.FIELDS:
            check = self.ids[f"{name}_check"]
            field = self.ids[f"{name}_field"]
            if name in data:
                field.text = str(data[name])
                check.active = True
            else:
                check.active = False
        if not self.ids.salt_field.text:
            self.ids.salt_field.text = DEFAULT_SALT
        if not self.ids.iterations_field.text:
            self.ids.iterations_field.text = str(DEFAULT_ITERATIONS)
        self.show_master_warning(self.ids.master_check.active)
        self.loading = False

    def save_state(self):
        if self.loading:
            return
        data = {
            name: self.ids[f"{name}_field"].text
            for name in self.FIELDS
            if self.ids[f"{name}_check"].active
        }
        try:
            with open(self.state_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except OSError:
            pass

    def show_master_warning(self, on):
        self.ids.master_warn.opacity = 1 if on else 0
        self.ids.master_warn.height = dp(64) if on else 0

    def on_master_check(self, active):
        self.show_master_warning(active)
        self.save_state()

    def generate(self):
        if self.busy:
            return
        salt = self.ids.salt_field.text
        master = self.ids.master_field.text
        site = self.ids.site_field.text
        if not (salt and master and site):
            self.ids.result_label.text = "Заполни все поля!"
            return
        try:
            iterations = int(self.ids.iterations_field.text)
        except ValueError:
            iterations = 0
        if iterations < 1:
            self.ids.result_label.text = "Итерации: целое число от 1"
            return

        self.save_state()
        self.busy = True
        self.ids.gen_btn.disabled = True
        self.ids.result_label.text = "Считаю..."
        threading.Thread(
            target=self._worker,
            args=(master, salt, site, iterations),
            daemon=True,
        ).start()

    def _worker(self, master, salt, site, iterations):
        start = time.perf_counter()
        try:
            res = generate_password(master, salt, site, iterations)
        except Exception as e:
            self._finish("", str(e))
            return
        elapsed = time.perf_counter() - start
        self._finish(res, None, elapsed)

    @mainthread
    def _finish(self, res, error, elapsed=0.0):
        self.busy = False
        self.ids.gen_btn.disabled = False
        if error:
            self.result = ""
            self.ids.result_label.text = f"Ошибка: {error}"
        else:
            self.result = res
            self.ids.result_label.text = f"Результат: {res}\n({elapsed:.2f} с)"

    def copy_result(self):
        if self.result:
            Clipboard.copy(self.result)


class FolyanApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        Window.softinput_mode = "below_target"
        Builder.load_string(KV)
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(RockPaperScissorsScreen(name="rps"))
        sm.add_widget(InterpreterScreen(name="interpreter"))
        sm.add_widget(FilesScreen(name="files"))
        sm.add_widget(PasswordScreen(name="passwords"))
        return sm
