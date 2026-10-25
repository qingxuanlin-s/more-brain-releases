"""打包开发示例或相同布局的插件；不安装依赖，不启动 Host。"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import tempfile
import zipfile

from more_brain_plugin_sdk import validate_plugin_directory


KIT = Path(__file__).resolve().parents[1]
DEFAULT_FILES = ("plugin.toml", "plugin.py", "dist", "src", "templates", "assets",
                 "vendor", "README.md", "LICENSE", "requirements-vendor.txt")
EXCLUDED = {"node_modules", "__pycache__", ".git", ".venv", ".releases",
            ".active-release", ".active-release.tmp", "config.json"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, default=KIT / "out")
    parser.add_argument("--include", action="append", default=[], help="额外制品相对路径，可重复")
    args = parser.parse_args()
    root = args.directory.resolve()
    manifest = validate_plugin_directory(root)
    selected: dict[str, Path] = {}
    for name in (*DEFAULT_FILES, *args.include):
        candidate = root / name
        if candidate.is_symlink() or not candidate.resolve().is_relative_to(root):
            parser.error(f"制品不能是软链接或越界路径：{name}")
        if not candidate.exists():
            if name in args.include:
                parser.error(f"额外制品不存在：{name}")
            continue
        paths = candidate.rglob("*") if candidate.is_dir() else [candidate]
        for path in paths:
            if path.is_symlink():
                parser.error(f"制品不能包含软链接：{path.relative_to(root)}")
            relative = path.relative_to(root)
            if any(part in EXCLUDED or part.startswith(".") for part in relative.parts):
                continue
            if path.is_file() and path.suffix not in {".pyc", ".log", ".db", ".sqlite", ".sqlite3"}:
                selected[relative.as_posix()] = path
    if len(selected) > 1000 or sum(path.stat().st_size for path in selected.values()) > 100 * 1024 * 1024:
        parser.error("制品超过安装器的 1000 文件或解压 100 MiB 限制")
    # 先验证临时 ZIP，避免生成无法安装或缺入口的正式制品。
    with tempfile.TemporaryDirectory(prefix="more-brain-plugin-pack-") as temporary:
        staged = Path(temporary)
        archive = staged / "plugin.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
            for relative, path in sorted(selected.items()):
                output.write(path, relative)
        if archive.stat().st_size > 50 * 1024 * 1024:
            parser.error("ZIP 超过安装器的 50 MiB 限制")
        extracted = staged / "unpacked"
        with zipfile.ZipFile(archive) as package:
            package.extractall(extracted)
        validate_plugin_directory(extracted)
        destination = args.output.resolve()
        destination.mkdir(parents=True, exist_ok=True)
        target = destination / f"{manifest.plugin_id}-{manifest.version}.zip"
        content = archive.read_bytes()
        target.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        target.with_suffix(".zip.sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
    print(f"已打包：{target}（{len(selected)} 个文件）")
    print(f"SHA256：{digest}")


if __name__ == "__main__":
    main()
