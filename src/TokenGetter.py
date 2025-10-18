# %%
import json
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


class TokenGetter:
    def __init__(self):
        self.port = 8012
        self.assets_path = Path(__file__).parent / "assets"
        self.src_path = Path(__file__).parent

    def run_mitmproxy(self):
        subprocess.run(
            args=[
                (self.assets_path / "mitmdump").as_posix(),
                "-s",
                (self.src_path / "RequestLogger.py").as_posix(),
                "-q",
                "-p",
                str(self.port),
            ]
        )

    def get_token(self):
        logger.info("准备获取 token, 请稍等...")
        proxy = self.back_up_proxy()
        self.set_proxy()

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.run_mitmproxy)
                if not self.check_cert():
                    if not self.install_cert():
                        self.restore_proxy(proxy)
                        executor.shutdown(wait=False)
                        return False

                logger.info("请打开久事体育APP小程序并登录")
                future.result()
                logger.info("成功获取到 token, 可以退出小程序了")
                return True
        except Exception as e:
            logger.info("获取 token 过程中出现错误")
            logger.debug(e, exc_info=True)
            return False
        finally:
            self.restore_proxy(proxy)

    def read_token(self):
        config_path = self.assets_path / "config.json"
        if not config_path.exists():
            with open(config_path, "w") as f:
                pass
            logger.info("配置文件不存在，请先登录")
            return None

        with open(config_path, "r+") as f:
            try:
                data: dict = json.load(f)
            except json.JSONDecodeError:
                logger.info("配置文件格式错误，初始化配置文件")
                data = {}
                f.truncate(0)
                f.seek(0)
                json.dump(data, f)
                return None

            token = data.get("token", {})
            if token == {}:
                logger.info("配置文件中不存在 token，请先登录")
                return None
            logger.debug(f"读取 token: {token}")
            return token

    def clear_token(self):
        config_path = self.assets_path / "config.json"
        if config_path.exists():
            logger.info("清除 token")
            with open(config_path, "r+") as f:
                try:
                    json_dict = json.load(f)
                except json.JSONDecodeError:
                    logger.info("配置文件格式错误，初始化配置文件")
                    json_dict = {}

                if "token" in json_dict:
                    del json_dict["token"]
                f.truncate(0)
                f.seek(0)
                json.dump(json_dict, f)
        else:
            logger.info("配置文件不存在")

    def check_cert(self):
        try:
            cert_info = subprocess.run(
                ["certutil", "-store", "root"],
                capture_output=True,
                check=True,
                encoding="gb2312",
            ).stdout
        except Exception as e:
            logger.info(f"无法自动检测证书，请确保证书已安装")
            logger.debug(e, exc_info=True)
            return True

        if "mitmproxy" in cert_info:
            return True
        else:
            logger.info(
                "检测到证书未安装，将自动安装证书。请确保使用管理员权限运行此程序"
            )
            return False

    def install_cert(self):
        logger.info("正在下载证书...")
        cert_url = "http://mitm.it/cert/cer"

        try:
            response = httpx.get(cert_url)
            response.raise_for_status()
        except Exception as e:
            logger.info("证书下载失败，请检查网络连接")
            logger.debug(e, exc_info=True)
            return False

        with open(self.assets_path / "mitmproxy-ca-cert.cer", "wb") as f:
            f.write(response.content)

        logger.info("证书下载成功，正在安装证书...")

        try:
            subprocess.run(
                [
                    "certutil",
                    "-addstore",
                    "root",
                    (self.assets_path / "mitmproxy-ca-cert.cer").as_posix(),
                ],
                capture_output=True,
                check=True,
            )
        except Exception as e:
            logger.info("证书安装失败，第一次使用请确保使用管理员权限运行此程序")
            logger.debug(e, exc_info=True)

            output = subprocess.run(
                ["certutil", "-addstore", "root", "mitmproxy-ca-cert.cer"],
                capture_output=True,
                encoding="gb2312",
            ).stdout
            logger.debug(output)
            return False

        logger.info("证书安装成功")
        return True

    def back_up_proxy(self):
        proxy = {
            "ProxyEnable": "",
            "ProxyServer": "",
            "ProxyOverride": "",
        }

        for name in proxy.keys():
            cmd = rf'(Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings").{name}'
            result = subprocess.run(
                ["powershell", "-Command", cmd], capture_output=True, text=True
            ).stdout
            proxy[name] = result.strip()

        return proxy

    def restore_proxy(self, proxy: dict):
        for name, value in proxy.items():
            cmd = rf'Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name {name} -Value "{value}"'
            subprocess.run(["powershell", "-Command", cmd])

    def set_proxy(self):
        proxy = {
            "ProxyEnable": "1",
            "ProxyServer": f"127.0.0.1:{self.port}",
            "ProxyOverride": "<local>",
        }
        for name, value in proxy.items():
            cmd = rf'Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name {name} -Value "{value}"'
            subprocess.run(["powershell", "-Command", cmd])


# %%
