from dataclasses import dataclass

import configparser

CONFIG_VERSION = 1

TTS_COMMAND = "!tts"

MODE_ALL = "all"
MODE_COMMAND = "command"
MODE_MENTION_ONLY = "mentiononly"
MODES = {MODE_ALL, MODE_COMMAND, MODE_MENTION_ONLY}


@dataclass
class Config:
    version: int
    access_token: str
    channel_name: str
    mode: str
    ignore_urls: bool
    ignore_bot_commands: bool
    excluded_users: set[str]
    volume: float
    fallback_language: str


class ConfigParser:
    def read(self, filename) -> Config:
        config_file = configparser.ConfigParser()
        config_file.read(filename, "utf-8")

        version = config_file["General"].getint("Version", -1)

        if version == -1:
            raise RuntimeError("Invalid config version")

        if version > CONFIG_VERSION:
            raise RuntimeError(f"Unsupported config version: {version}")

        config_twitch = config_file["Twitch"]
        access_token = config_twitch["AccessToken"]
        channel_name = config_twitch["ChannelName"]

        config_settings = config_file["Settings"]

        mode = config_settings.get("Mode", MODE_ALL)
        if mode not in MODES:
            raise RuntimeError(f"Invalid filter mode: {mode}")

        ignore_urls = config_settings.getboolean("IgnoreUrls", True)
        ignore_bot_commands = config_settings.getboolean("IgnoreBotCommands", True)
        excluded_users = set(config_settings["ExcludedUsers"].split(","))

        volume = max(0.0, min(1.0, config_settings.getfloat("Volume", 1.0)))
        fallback_language = config_settings.get("FallbackLanguage", "en")

        return Config(
            version=version,
            access_token=access_token,
            channel_name=channel_name,
            mode=mode,
            ignore_urls=ignore_urls,
            ignore_bot_commands=ignore_bot_commands,
            excluded_users=excluded_users,
            volume=volume,
            fallback_language=fallback_language,
        )

    def write(self, config: Config, filename):
        config_file = configparser.ConfigParser()

        config_file["General"] = {"Version": config.version}

        config_file["Twitch"] = {
            "AccessToken": config.access_token,
            "ChannelName": config.channel_name,
        }

        config_file["Settings"] = {
            "Mode": config.mode,
            "IgnoreUrls": config.ignore_urls,
            "IgnoreBotCommands": config.ignore_bot_commands,
            "ExcludedUsers": ", ".join(config.excluded_users),
            "Volume": config.volume,
            "FallbackLanguage": config.fallback_language,
        }

        with open(filename, "w", encoding="utf-8") as file:
            config_file.write(file)
