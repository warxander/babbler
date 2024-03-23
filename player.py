import asyncio
import miniaudio

from config import Config


class AudioPlayer:
    def __init__(self, config: Config):
        self._device = miniaudio.PlaybackDevice()
        self._device._device.masterVolumeFactor = config.volume
        self._stop_event = asyncio.Event()

    async def play(self, data: bytes):
        if self._device.running:
            self.stop()

        self._stop_event.clear()

        stream = miniaudio.stream_with_callbacks(
            miniaudio.stream_memory(data), None, None, self._on_stream_end
        )
        next(stream)

        self._device.start(stream)
        await self._stop_event.wait()

    def stop(self):
        self._device.stop()
        self._stop_event.set()

    def _on_stream_end(self):
        self._stop_event.set()
