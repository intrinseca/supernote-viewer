import pathlib

import toml
from platformdirs import user_config_dir

config_path = pathlib.Path(user_config_dir()) / "supernote_viewer.toml"
config = toml.load(config_path)
