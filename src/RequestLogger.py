# %%
import json
from pathlib import Path

from mitmproxy import ctx
from mitmproxy.http import HTTPFlow


class RequestLogger:
    def __init__(self, config_path):
        self.config_path = config_path

    def request(self, flow: HTTPFlow):
        if (
            "jsapp.jussyun.com" in flow.request.pretty_host
            and "auth" not in flow.request.pretty_url
        ):
            headers = flow.request.headers
            if headers.get("token"):
                with open(self.config_path, "w+") as f:
                    if f.read() == "":
                        json_dict = {}
                    else:
                        json_dict = json.load(f)
                    json_dict["token"] = headers["token"]
                    json.dump(json_dict, f)
                    ctx.master.shutdown()


config_path = Path(__file__).parents[1] / "assets" / "config.json"
addons = [RequestLogger(config_path)]
