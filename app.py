from ctypes import windll
import io
import sys
import tkinter
import tkinter.messagebox
from tkinter import ttk
import threading
import webbrowser

from bot import TwitchBot
from config import (
    Config,
    ConfigParser,
    MODE_ALL,
    MODE_COMMAND,
    MODE_MENTION_ONLY,
    TTS_COMMAND,
)
from player import AudioPlayer


async def tts_worker(player: AudioPlayer, bot: TwitchBot):
    while True:
        try:
            message = await bot.get_message()

            data = io.BytesIO()
            message.write_to_fp(data)

            player.play(data.getvalue())
        except Exception as ex:
            print(f"[ERROR] Failed to play message:\n{ex}")


def bot_worker(config, player):
    bot = TwitchBot(config)

    bot.loop.create_task(tts_worker(player, bot))

    try:
        bot.run()
    except Exception as ex:
        print(f"[ERROR] Failed to run Twitch bot:\n{ex}")


class _VariableStorage:
    def __init__(self):
        self.access_token = tkinter.StringVar()
        self.channel_name = tkinter.StringVar()
        self.mode = tkinter.StringVar()
        self.ignore_urls = tkinter.BooleanVar()
        self.ignore_bot_commands = tkinter.BooleanVar()
        self.excluded_users = tkinter.StringVar()
        self.volume = tkinter.DoubleVar()

    def load_from_config(self, config: Config):
        self.access_token.set(config.access_token)
        self.channel_name.set(config.channel_name)
        self.mode.set(config.mode)
        self.ignore_urls.set(config.ignore_urls)
        self.ignore_bot_commands.set(config.ignore_bot_commands)
        self.excluded_users.set(", ".join(config.excluded_users))
        self.volume.set(config.volume)

    def write_to_config(self, config: Config):
        config.access_token = self.access_token.get()
        config.channel_name = self.channel_name.get()
        config.mode = self.mode.get()
        config.ignore_urls = self.ignore_urls.get()
        config.ignore_bot_commands = self.ignore_bot_commands.get()

        config.excluded_users.clear()
        for user in self.excluded_users.get().split(","):
            config.excluded_users.add(user)

        config.volume = self.volume.get()


class _StdoutPrinter:
    def __init__(self, text: tkinter.Text):
        self._text = text

    def write(self, text):
        self._text.configure(state=tkinter.NORMAL)
        self._text.insert(tkinter.END, text)
        self._text.see(tkinter.END)
        self._text.configure(state=tkinter.DISABLED)

    def flush(self):
        pass


class App(tkinter.Tk):
    def __init__(self, config_filename):
        dpi_error_code = windll.shcore.SetProcessDpiAwareness(1)
        if dpi_error_code != 0:
            self.withdraw()
            tkinter.messagebox.showerror(
                "Error",
                f"SetProcessDpiAwareness() failed:\nError code {dpi_error_code}",
            )
            sys.exit()

        super().__init__()
        self.title("Babbler")
        self.resizable(False, False)

        self._config_filename = config_filename

        try:
            self._config = ConfigParser().read(self._config_filename)
        except Exception as ex:
            self.withdraw()
            tkinter.messagebox.showerror(
                "Error", f"Failed to read {self._config_filename}:\n{ex}"
            )
            sys.exit()

        self._player = AudioPlayer(self._config)

        self._variable_storage = _VariableStorage()
        self._variable_storage.load_from_config(self._config)

        frame = ttk.Frame(padding=5)
        frame.pack(fill=tkinter.BOTH, expand=True)

        self._notebook = ttk.Notebook(frame)
        self._notebook.pack(fill=tkinter.BOTH, expand=True)

        self._notebook.add(self._init_twitch_tab(), text=" Twitch ")
        self._notebook.add(self._init_settings_tab(), text=" Settings ")
        self._notebook.add(self._init_logs_tab(), text=" Logs ")

        tkinter.Frame(frame, width=30, height=5).pack()

        self._skip_message_button = ttk.Button(
            frame,
            text="Skip Message",
            width=15,
            command=self._on_skip_message_button_clicked,
        )

        self._start_button = ttk.Button(
            frame, text="Start", width=10, command=self._on_start_button_clicked
        )
        self._start_button.pack()

    def _init_twitch_tab(self) -> ttk.Frame:
        frame = ttk.Frame(self._notebook, padding=5)
        frame.pack(fill=tkinter.BOTH, expand=True)

        ttk.Label(frame, text="Channel Name:").pack(anchor=tkinter.CENTER)
        ttk.Entry(
            frame,
            textvariable=self._variable_storage.channel_name,
            width=30,
            justify=tkinter.CENTER,
        ).pack(anchor=tkinter.CENTER)

        ttk.Frame(frame, height=20).pack()

        ttk.Label(frame, text="Access Token:").pack(anchor=tkinter.CENTER)

        ttk.Entry(
            frame,
            textvariable=self._variable_storage.access_token,
            width=30,
            show="*",
            justify=tkinter.CENTER,
        ).pack(anchor=tkinter.CENTER)

        access_token_label = ttk.Label(
            frame, text="twitchtokengenerator.com", foreground="blue"
        )
        access_token_label.pack(anchor=tkinter.CENTER)
        access_token_label.bind(
            "<Button-1>", lambda _: webbrowser.open("https://twitchtokengenerator.com/")
        )

        return frame

    def _init_settings_tab(self) -> ttk.Frame:
        frame = ttk.Frame(self._notebook, padding=5)
        frame.pack(fill=tkinter.BOTH, expand=True)

        ttk.Label(frame, text="Mode:").pack(anchor=tkinter.NW)

        mode_frame = ttk.Frame(frame)
        mode_frame.pack(anchor=tkinter.NW)
        ttk.Radiobutton(
            mode_frame, text="All", value=MODE_ALL, variable=self._variable_storage.mode
        ).pack(side=tkinter.LEFT)
        ttk.Radiobutton(
            mode_frame,
            text=f"Command ({TTS_COMMAND})",
            value=MODE_COMMAND,
            variable=self._variable_storage.mode,
        ).pack(side=tkinter.LEFT, padx=5)
        ttk.Radiobutton(
            mode_frame,
            text="Mention Only",
            value=MODE_MENTION_ONLY,
            variable=self._variable_storage.mode,
        ).pack(side=tkinter.LEFT, padx=5)

        ttk.Frame(frame, height=20).pack()

        ttk.Checkbutton(
            frame, variable=self._variable_storage.ignore_urls, text="Ignore URLs"
        ).pack(anchor=tkinter.NW)

        ttk.Frame(frame, height=10).pack()

        ttk.Checkbutton(
            frame,
            variable=self._variable_storage.ignore_bot_commands,
            text="Ignore bot commands",
        ).pack(anchor=tkinter.NW)

        ttk.Frame(frame, height=20).pack()

        ttk.Label(frame, text="Users to exclude:").pack(anchor=tkinter.NW)
        ttk.Entry(
            frame, textvariable=self._variable_storage.excluded_users, width=50
        ).pack(anchor=tkinter.NW)
        ttk.Label(frame, text="Comma-separated list of users", foreground="grey").pack(
            anchor=tkinter.NW
        )

        ttk.Frame(frame, height=20).pack()

        ttk.Label(frame, text="Volume:").pack(anchor=tkinter.NW)
        ttk.Scale(
            frame,
            variable=self._variable_storage.volume,
            from_=0.1,
            to=1.0,
            orient=tkinter.HORIZONTAL,
        ).pack(anchor=tkinter.NW, side=tkinter.LEFT, padx=5)

        return frame

    def _init_logs_tab(self) -> ttk.Frame:
        frame = ttk.Frame(self._notebook, padding=5)
        frame.pack(fill=tkinter.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame)

        text = tkinter.Text(frame, yscrollcommand=scrollbar.set, state=tkinter.DISABLED)
        text.pack(fill=tkinter.BOTH, side=tkinter.LEFT, expand=True)

        scrollbar.configure(command=text.yview)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)

        sys.stdout = _StdoutPrinter(text)
        sys.stderr = _StdoutPrinter(text)

        return frame

    def _on_start_button_clicked(self):
        if len(self._variable_storage.channel_name.get()) == 0:
            tkinter.messagebox.showerror("Error", "Channel Name must be specified.")
            return

        if len(self._variable_storage.access_token.get()) == 0:
            tkinter.messagebox.showerror("Error", "Access Token must be specified.")
            return

        self._start_button.pack_forget()

        self._disable_widgets(self._notebook)

        self._variable_storage.write_to_config(self._config)
        ConfigParser().write(self._config, self._config_filename)
        print("[INFO] Settings were saved")

        threading.Thread(
            target=bot_worker, args=(self._config, self._player), daemon=True
        ).start()

        self._skip_message_button.pack()
        print("[INFO] Bot has been started")

    def _on_skip_message_button_clicked(self):
        self._player.stop()

    def _disable_widgets(self, widget: tkinter.Widget):
        for child in widget.winfo_children():
            child_class = child.winfo_class()
            if child_class in ("Frame", "TFrame"):
                self._disable_widgets(child)
            elif child_class != "TScrollbar":
                child.configure(state=tkinter.DISABLED)
