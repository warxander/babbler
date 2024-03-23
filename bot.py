import asyncio

from googletrans import Translator
import gtts.lang
from twitchio.ext import commands
from twitchio.message import Message

from config import Config, MODE_COMMAND, MODE_MENTION_ONLY, TTS_COMMAND
from message import TTSMessage


class _Translator:
    def __init__(self, config: Config, langs: dict):
        self._config = config
        self._langs = langs
        self._translator = Translator()

    def detect(self, text) -> str:
        lang = self._translator.detect(text).lang

        if not lang in self._langs:
            lang = self._config.fallback_language

        return lang


class _Filter:
    _TTS_COMMAND_PREFIX = f"{TTS_COMMAND} "
    _TTS_COMMAND_PREFIX_LENGTH = len(_TTS_COMMAND_PREFIX)

    def __init__(self, config: Config):
        self._config = config
        self._mention_word = f"@{self._config.channel_name}".lower()
        self._last_message = None

    def apply(self, message: Message) -> str | None:
        if message.echo:
            return None

        if message.author.display_name in self._config.excluded_users:
            return None

        message_text: str = message.content

        if self._config.mode == MODE_COMMAND:
            if message_text.startswith(_Filter._TTS_COMMAND_PREFIX):
                message_text = message_text[_Filter._TTS_COMMAND_PREFIX_LENGTH :]
            else:
                return None

        if self._config.mode == MODE_MENTION_ONLY:
            if (
                next(
                    (
                        word
                        for word in message_text.split()
                        if (word.lower() == self._mention_word)
                    ),
                    None,
                )
                is None
            ):
                return None

        if self._config.ignore_urls:
            message_text = " ".join(
                filter(lambda word: not word.startswith("http"), message_text.split())
            )

        if self._config.ignore_bot_commands and message_text.startswith("!"):
            return None

        message_text = message_text.replace("@", "").strip()[: TTSMessage.MAX_CHARS]
        if len(message_text) == 0 or self._last_message == message_text:
            return None

        self._last_message = message_text
        return message_text


class TwitchBot(commands.Bot):
    def __init__(self, config: Config):
        asyncio.set_event_loop(asyncio.new_event_loop())

        super().__init__(
            token=config.access_token,
            prefix="?",
            initial_channels=[config.channel_name],
        )

        self._filter = _Filter(config)
        self._translator = _Translator(config, gtts.lang.tts_langs())
        self._messages = asyncio.Queue()

    async def event_message(self, message: Message):
        try:
            await self._process_message(message)
        except Exception as ex:
            print(f"[ERROR] Failed to process message:\n{ex}")

        await self.handle_commands(message)

    async def get_message(self):
        return await self._messages.get()

    async def _process_message(self, message: Message):
        message_log = f"{message.author.display_name}: {message.content}"

        message_text = self._filter.apply(message)
        if message_text is None:
            print(f"[SKIPPED_MSG] {message_log}")
            return

        print(f"[MSG] {message_log}")
        await self._messages.put(
            TTSMessage(message_text, self._translator.detect(message_text))
        )
