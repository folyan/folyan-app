import os
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

from RockScissorsPaper import check_win
from PasswordManager import generate_password

SCRIPTS_DIR = "/storage/emulated/0/Folyan/FolyanApp/UserScripts/"

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

        MDLabel:
            text: "Нажми на приложение, которое хочешь запустить"
            halign: "center"
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1)

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
    MDBoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "15dp"
        md_bg_color: BG

        MDIconButton:
            icon: "arrow-left"
            theme_icon_color: "Custom"
            icon_color: (1, 1, 1, 1)
            on_release: root.go_to("menu")

        MDTextField:
            id: salt_field
            hint_text: "Соль"

        MDTextField:
            id: master_field
            hint_text: "Мастер-пароль"
            password: True

        MDTextField:
            id: site_field
            hint_text: "Сайт"

        MenuButton:
            caption: "Сгенерировать"
            on_release: root.generate()

        MDLabel:
            id: result_label
            text: "Результат:"
            halign: "center"
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

        layout.add_widget(
            MDLabel(
                text="Нажми на приложение, которое хочешь запустить",
                halign="center",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
            )
        )

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
    def generate(self):
        salt = self.ids.salt_field.text
        master = self.ids.master_field.text
        site = self.ids.site_field.text
        if salt and master and site:
            res = generate_password(master, salt, site)
            self.ids.result_label.text = f"Результат: {res}"
        else:
            self.ids.result_label.text = "Заполни все поля!"

    def copy_result(self):
        text = self.ids.result_label.text
        if "Результат: " in text:
            res = text.split("Результат: ")[1]
            Clipboard.copy(res)


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
