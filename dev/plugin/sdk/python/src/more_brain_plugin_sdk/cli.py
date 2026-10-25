"""不依赖宿主服务的开发命令。"""

import argparse
from pathlib import Path

from .manifest import ManifestError
from .validation import validate_plugin_directory


def main() -> int:
    parser = argparse.ArgumentParser(description="More Brain Python 插件开发工具")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="静态检查插件目录，不执行插件代码")
    validate.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        manifest = validate_plugin_directory(args.directory)
    except (ManifestError, OSError, UnicodeError) as exc:
        parser.exit(1, f"校验失败：{exc}\n")
    print(f"校验通过：{manifest.plugin_id} {manifest.version}（Host API {manifest.host_api}）")
    return 0
