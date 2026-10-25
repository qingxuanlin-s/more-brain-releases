"""仅静态检查插件制品；从不 import 或执行插件入口。"""

from pathlib import Path

from .manifest import ManifestError, PluginManifest, parse_manifest_toml


def _artifact_file(root: Path, relative: str) -> Path:
    path = root / relative
    if root not in path.resolve().parents or not path.is_file():
        raise ManifestError(f"文件不存在或越出插件目录：{relative}")
    return path


def validate_plugin_directory(root: str | Path) -> PluginManifest:
    """检查 Manifest、入口 Python 语法与已声明客户端文件，不解析外部依赖。"""
    directory = Path(root).resolve()
    manifest = parse_manifest_toml(_artifact_file(directory, "plugin.toml").read_text("utf-8"))
    entry = _artifact_file(directory, manifest.entrypoint.split(":", 1)[0])
    try:
        compile(entry.read_bytes(), str(entry), "exec")
    except SyntaxError as exc:
        raise ManifestError(f"入口 Python 语法错误：{entry.name}:{exc.lineno}") from exc
    if manifest.client is not None:
        for relative in (manifest.client.entry, *manifest.client.styles):
            _artifact_file(directory, relative)
    return manifest
