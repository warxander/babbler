import threading
import miniaudio

from config import Config


class AudioPlayer:
    def __init__(self, config: Config):
        self._device = miniaudio.PlaybackDevice()
        self._device._device.masterVolumeFactor = config.volume
        self._lock = threading.RLock()
        self._stop_event = threading.Event()

    def play(self, data: bytes):
        with self._lock:
            if self._device.running:
                self.stop()

            self._stop_event.clear()

            stream = miniaudio.stream_with_callbacks(
                miniaudio.stream_memory(data), None, None, self._on_stream_end
            )
            next(stream)

            self._device.start(stream)

        self._stop_event.wait()

    def stop(self):
        self._stop_event.set()

        with self._lock:
            self._device.stop()

    def _on_stream_end(self):
        self._stop_event.set()
