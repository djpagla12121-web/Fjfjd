import os
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock

try:
    from kivy.core.clipboard import Clipboard
except Exception:
    Clipboard = None

from fb_login import login_wbloks


class FBToolUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 20
        self.spacing = 12
        Window.clearcolor = (0.05, 0.07, 0.09, 1)

        self.add_widget(Label(
            text="[b]FB LOGIN TOOL[/b]",
            markup=True, size_hint_y=None, height=50,
            color=(0, 1, 0, 1), font_size="22sp",
        ))

        self.phone = TextInput(
            hint_text="Phone number", multiline=False,
            size_hint_y=None, height=50,
            background_color=(0.15, 0.18, 0.22, 1),
            foreground_color=(0, 1, 0, 1),
            cursor_color=(0, 1, 0, 1),
            font_size="15sp", padding=[10, 12, 10, 12],
        )
        self.add_widget(self.phone)

        self.password = TextInput(
            hint_text="Password", password=True, multiline=False,
            size_hint_y=None, height=50,
            background_color=(0.15, 0.18, 0.22, 1),
            foreground_color=(0, 1, 0, 1),
            cursor_color=(0, 1, 0, 1),
            font_size="15sp", padding=[10, 12, 10, 12],
        )
        self.add_widget(self.password)

        row = BoxLayout(size_hint_y=None, height=52, spacing=10)
        self.login_btn = Button(
            text="LOGIN",
            background_color=(0, 0.6, 0.2, 1),
            background_normal="",
            font_size="16sp", bold=True,
        )
        self.login_btn.bind(on_press=self.do_login)
        row.add_widget(self.login_btn)

        clear_btn = Button(
            text="CLEAR",
            background_color=(0.3, 0.3, 0.3, 1),
            background_normal="",
            font_size="16sp",
        )
        clear_btn.bind(on_press=self.clear_all)
        row.add_widget(clear_btn)
        self.add_widget(row)

        scroll = ScrollView()
        self.output = Label(
            text="[color=00ffff]Ready[/color]",
            markup=True, size_hint_y=None,
            halign="left", valign="top",
            color=(0.8, 0.9, 0.85, 1), font_size="13sp",
        )
        self.output.bind(
            texture_size=lambda *x: setattr(self.output, "height", self.output.texture_size[1])
        )
        self.output.bind(
            width=lambda *x: setattr(self.output, "text_size", (self.output.width, None))
        )
        scroll.add_widget(self.output)
        self.add_widget(scroll)

        self.copy_btn = Button(
            text="COPY COOKIE",
            size_hint_y=None, height=44,
            background_color=(0.15, 0.4, 0.7, 1),
            background_normal="",
            font_size="14sp", disabled=True,
        )
        self.copy_btn.bind(on_press=self.copy_cookie)
        self.add_widget(self.copy_btn)

        self.status = Label(
            text="Ready",
            size_hint_y=None, height=30,
            color=(0, 1, 1, 1), font_size="12sp",
        )
        self.add_widget(self.status)
        self._last_cookie = ""

    def do_login(self, instance):
        phone = self.phone.text.strip()
        pwd = self.password.text.strip()
        if not phone or not pwd:
            self.status.text = "❌ Empty number or password"
            self.status.color = (1, 0.3, 0.3, 1)
            return
        self.login_btn.disabled = True
        self.status.text = "Logging in..."
        self.status.color = (1, 1, 0.3, 1)
        self.output.text = "[color=ffff00]Sending request...[/color]"
        threading.Thread(target=self._run, args=(phone, pwd), daemon=True).start()

    def _run(self, phone, pwd):
        try:
            result = login_wbloks(phone, pwd)
        except Exception as e:
            result = {"status": "EXCEPTION", "message": str(e)}
        Clock.schedule_once(lambda dt: self._show(result, phone, pwd), 0)

    def _show(self, result, phone, pwd):
        self.login_btn.disabled = False
        s = result.get("status", "")
        if s == "SUCCESS":
            uid = result.get("uid", "?")
            cookie = result.get("cookie", "")
            self._last_cookie = cookie
            self.copy_btn.disabled = False
            self.output.text = (
                f"[color=00ff00][b]✔ LOGIN SUCCESSFUL[/b][/color]\n\n"
                f"[color=ffff00]UID:[/color] [color=00ff00]{uid}[/color]\n"
                f"[color=ffff00]Phone:[/color] {phone}\n"
                f"[color=ffff00]Password:[/color] {pwd}\n\n"
                f"[color=00ffff][b]🔐 COOKIE:[/b][/color]\n"
                f"[color=cccccc]{cookie}[/color]"
            )
            self.status.text = "✅ Success"
            self.status.color = (0, 1, 0, 1)
            self._save(uid, pwd, cookie, phone)
        else:
            msg = result.get("message", "unknown")
            label = {
                "WRONG_PASS": "WRONG PASSWORD",
                "CHECKPOINT": "CHECKPOINT REQUIRED",
                "FAIL": "LOGIN FAILED",
                "EXCEPTION": "EXCEPTION",
            }.get(s, "FAILED")
            self.output.text = (
                f"[color=ff5555][b]✘ {label}[/b][/color]\n\n"
                f"[color=ffff00]Phone:[/color] {phone}\n"
                f"[color=ffff00]Reason:[/color] [color=ff5555]{msg}[/color]"
            )
            self.status.text = f"❌ {label}"
            self.status.color = (1, 0.3, 0.3, 1)

    def _save(self, uid, pwd, cookie, phone):
        line = f"{uid}|{pwd}|{cookie}|{phone}\n"
        candidates = [
            "/sdcard/Login_Accounts.txt",
            os.path.join(App.get_running_app().user_data_dir, "Login_Accounts.txt"),
            "Login_Accounts.txt",
        ]
        for c in candidates:
            try:
                with open(c, "a") as f:
                    f.write(line)
                self.status.text = f"✅ Saved: {os.path.basename(c)}"
                return
            except Exception:
                continue

    def copy_cookie(self, instance):
        if not self._last_cookie or Clipboard is None:
            return
        try:
            Clipboard.copy(self._last_cookie)
            self.status.text = "📋 Copied"
            self.status.color = (0, 1, 0, 1)
        except Exception:
            pass

    def clear_all(self, instance):
        self.phone.text = ""
        self.password.text = ""
        self.output.text = "[color=00ffff]Ready[/color]"
        self.status.text = "Ready"
        self.status.color = (0, 1, 1, 1)
        self.copy_btn.disabled = True
        self._last_cookie = ""


class FBApp(App):
    def build(self):
        self.title = "FB Login Tool"
        return FBToolUI()


if __name__ == "__main__":
    FBApp().run()
