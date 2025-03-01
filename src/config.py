from pathlib import Path

from pydantic_settings import BaseSettings

DATA_FOLDER = Path(__file__).parent / "data"

class Config(BaseSettings):
    first_player_name: str = "default"
    data_folder: Path = DATA_FOLDER
    bot_token: str = "default"
    rank_up_channel_id: int = 0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"