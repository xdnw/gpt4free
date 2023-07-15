# my_app/config.py
from typedconfig import Config, key, section, group_key
from typedconfig.source import EnvironmentConfigSource, IniFileConfigSource

@section('openai')
class OpenAIConfig(Config):
    api_key = key(cast=str)

class ParentConfig(Config):
    open_ai = group_key(OpenAIConfig)

config = ParentConfig()
config.add_source(IniFileConfigSource("config/config.ini"))
config.read()