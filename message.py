from gtts import gTTS


class TTSMessage:
    MAX_CHARS = gTTS.GOOGLE_TTS_MAX_CHARS

    def __init__(self, text, lang):
        self._text = text
        self._lang = lang

    def write_to_fp(self, fp):
        gTTS(self._text, lang=self._lang, tld="com.au", lang_check=False).write_to_fp(fp)

    def __str__(self):
        return f"{{ lang: {self._lang}, text: {self._text} }}"
