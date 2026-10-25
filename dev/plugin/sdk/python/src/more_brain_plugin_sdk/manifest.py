"""只读取静态 Manifest 的校验器；此处绝不导入插件代码。"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import PurePosixPath
from collections import defaultdict
from typing import Any, Mapping, Sequence


_PLUGIN_ID = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_CLIENT_COMMAND_ID = re.compile(r"^[a-z][a-z0-9-]{0,62}(?:\.[a-z][a-z0-9-]{0,62})*$")
_SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
_HOST_API_CLAUSE = re.compile(r"^(>=|<=|>|<|==|=)?\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?$")
HOST_API_VERSION = "1.0.0"
_HOST_API_TUPLE = (1, 0, 0)
CLIENT_SDK_API_VERSION = "1.0.0"
_CLIENT_SDK_API_TUPLE = (1, 0, 0)
_CLIENT_SLOTS = frozenset({
    "global.navigation", "global.workspace", "right-dock.tabs", "right-dock.panel", "global-overlay",
    # 回合「执行明细」表面：插件按 Runtime 认领，宿主只做匹配与挂载。
    "execution-detail.panel",
    "roundtable.workbench",
})


class ManifestError(ValueError):
    """Manifest 不能安全参与 inventory 或 activation。"""


@dataclass(frozen=True, slots=True)
class CapabilityDeclaration:
    kind: str
    name: str
    api: int
    exclusive: bool = False
    optional: bool = False


@dataclass(frozen=True, slots=True)
class ClientManifest:
    """同源、可信 React 客户端制品的静态声明。"""

    entry: str
    styles: tuple[str, ...]
    sdk_api: str
    renderer: str
    slots: tuple[str, ...]
    commands: tuple[str, ...]
    requires: tuple[str, ...] = ()
    optional_requires: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    entrypoint: str
    host_api: str
    enabled_by_default: bool
    isolation: str
    description: str
    provides: tuple[CapabilityDeclaration, ...] = ()
    requires: tuple[CapabilityDeclaration, ...] = ()
    client: ClientManifest | None = None


def _text(value: object, field: str) -> str:
    result = str(value).strip()
    if not result:
        raise ManifestError(f"{field} 不能为空")
    return result


def _entrypoint(value: object) -> str:
    entrypoint = _text(value, "entrypoint")
    if entrypoint.count(":") != 1:
        raise ManifestError("entrypoint 必须是 file.py:object")
    file_name, object_name = entrypoint.split(":", 1)
    path = PurePosixPath(file_name)
    if (
        not file_name.endswith(".py")
        or not object_name.isidentifier()
        or path.is_absolute()
        or ".." in path.parts
        or "." in path.parts
    ):
        raise ManifestError("entrypoint 必须指向制品内的 Python 对象")
    return entrypoint


def _compatible_version_range(
    value: object, field: str, *, current: tuple[int, int, int], display: str,
) -> str:
    specification = _text(value, field)
    clauses = [part.strip() for part in specification.split(",")]
    if not clauses or any(not clause for clause in clauses):
        raise ManifestError(f"{field} 必须是以逗号分隔的版本范围")
    for clause in clauses:
        match = _HOST_API_CLAUSE.fullmatch(clause)
        if match is None:
            raise ManifestError(f"{field} 版本范围非法")
        operator = match.group(1) or "="
        version = tuple(int(part or 0) for part in match.groups()[1:])
        if operator in {"=", "=="}:
            compatible = current == version
        elif operator == ">=":
            compatible = current >= version
        elif operator == "<=":
            compatible = current <= version
        elif operator == ">":
            compatible = current > version
        else:
            compatible = current < version
        if not compatible:
            raise ManifestError(f"{field} 与当前 {display} 不兼容")
    return specification


def _host_api(value: object) -> str:
    return _compatible_version_range(
        value, "host_api", current=_HOST_API_TUPLE, display=f"Host {HOST_API_VERSION}",
    )


def _capabilities(value: object, field: str) -> tuple[CapabilityDeclaration, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ManifestError(f"{field} 必须是数组")
    result: list[CapabilityDeclaration] = []
    seen: set[tuple[str, str, int]] = set()
    for item in value:
        if not isinstance(item, Mapping):
            raise ManifestError(f"{field} 项必须是对象")
        kind = _text(item.get("kind"), f"{field}.kind")
        name = _text(item.get("name"), f"{field}.name")
        api = item.get("api")
        if not isinstance(api, int) or api < 1:
            raise ManifestError(f"{field}.api 必须是正整数")
        key = (kind, name, api)
        if key in seen:
            raise ManifestError(f"{field} 中 Capability 重复：{kind}/{name}/{api}")
        seen.add(key)
        result.append(CapabilityDeclaration(
            kind, name, api, bool(item.get("exclusive", False)), bool(item.get("optional", False)),
        ))
    return tuple(result)


def _client_artifact_path(value: object, field: str, *, suffix: str) -> str:
    text = _text(value, field)
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or len(path.parts) < 2
        or path.parts[0] != "dist"
        or ".." in path.parts
        or "." in path.parts
        or not text.endswith(suffix)
    ):
        raise ManifestError(f"{field} 必须是制品内 dist/ 下的 {suffix} 文件")
    return path.as_posix()


def _client_plugin_ids(value: object, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ManifestError(f"{field} 必须是 plugin id 数组")
    result = tuple(item.strip() for item in value)
    if len(result) != len(set(result)) or any(not _PLUGIN_ID.fullmatch(item) for item in result):
        raise ManifestError(f"{field} 包含重复或非法 plugin id")
    return result


def _client_manifest(value: object) -> ClientManifest | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ManifestError("[client] 必须是对象")
    renderer = _text(value.get("renderer", "react"), "client.renderer")
    if renderer != "react":
        raise ManifestError("client.renderer 目前只能是 react")
    slots = value.get("slots", [])
    if not isinstance(slots, list) or not all(isinstance(item, str) and item in _CLIENT_SLOTS for item in slots):
        raise ManifestError("client.slots 包含不支持的 Slot")
    if len(slots) != len(set(slots)):
        raise ManifestError("client.slots 不能重复")
    commands = value.get("commands", [])
    if not isinstance(commands, list) or not all(isinstance(item, str) and _CLIENT_COMMAND_ID.fullmatch(item) for item in commands):
        raise ManifestError("client.commands 包含非法 Command id")
    if len(commands) != len(set(commands)):
        raise ManifestError("client.commands 不能重复")
    styles = value.get("styles", value.get("css", []))
    if not isinstance(styles, list):
        raise ManifestError("client.styles 必须是数组")
    parsed_styles = tuple(_client_artifact_path(item, "client.styles", suffix=".css") for item in styles)
    if len(parsed_styles) != len(set(parsed_styles)):
        raise ManifestError("client.styles 不能重复")
    requires = _client_plugin_ids(value.get("requires"), "client.requires")
    optional_requires = _client_plugin_ids(value.get("optional_requires"), "client.optional_requires")
    if set(requires) & set(optional_requires):
        raise ManifestError("client.requires 与 client.optional_requires 不能重复")
    return ClientManifest(
        entry=_client_artifact_path(value.get("entry"), "client.entry", suffix=".js"),
        styles=parsed_styles,
        sdk_api=_compatible_version_range(
            value.get("sdk_api", ">=1.0,<2.0"), "client.sdk_api",
            current=_CLIENT_SDK_API_TUPLE, display=f"Client SDK {CLIENT_SDK_API_VERSION}",
        ),
        renderer=renderer,
        slots=tuple(slots),
        commands=tuple(commands),
        requires=requires,
        optional_requires=optional_requires,
    )


def parse_manifest(data: Mapping[str, Any]) -> PluginManifest:
    """将 TOML 根对象转成不可变 Manifest。"""
    plugin = data.get("plugin")
    if not isinstance(plugin, Mapping):
        raise ManifestError("缺少 [plugin]")
    plugin_id = _text(plugin.get("id"), "plugin.id")
    if not _PLUGIN_ID.fullmatch(plugin_id):
        raise ManifestError("plugin.id 必须是小写字母开头的 kebab-case")
    version = _text(plugin.get("version"), "plugin.version")
    if not _SEMVER.fullmatch(version):
        raise ManifestError("plugin.version 必须是 SemVer")
    isolation = str(plugin.get("isolation", "in-process"))
    if isolation not in {"in-process", "process"}:
        raise ManifestError("plugin.isolation 只能是 in-process 或 process")
    return PluginManifest(
        plugin_id=plugin_id,
        name=_text(plugin.get("name", plugin_id), "plugin.name"),
        version=version,
        entrypoint=_entrypoint(plugin.get("entrypoint", "plugin.py:create_plugin")),
        host_api=_host_api(plugin.get("host_api", ">=1.0,<2.0")),
        enabled_by_default=bool(plugin.get("enabled_by_default", True)),
        isolation=isolation,
        description=str(plugin.get("description", "")).strip(),
        provides=_capabilities(data.get("provides"), "provides"),
        requires=_capabilities(data.get("requires"), "requires"),
        client=_client_manifest(data.get("client")),
    )


def parse_manifest_toml(text: str) -> PluginManifest:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ManifestError(f"TOML 格式错误：{exc}") from exc
    return parse_manifest(data)


def resolve_manifest_order(manifests: Sequence[PluginManifest], *, provided=()) -> tuple[str, ...]:
    """在 import 前验证 Capability 依赖，并给出确定性的 prepare 顺序。"""
    by_id = {manifest.plugin_id: manifest for manifest in manifests}
    if len(by_id) != len(manifests):
        raise ManifestError("plugin.id 重复")
    providers: dict[tuple[str, str, int], list[str]] = defaultdict(list)
    exclusive: set[tuple[str, str, int]] = set()
    for manifest in manifests:
        for declaration in manifest.provides:
            key = (declaration.kind, declaration.name, declaration.api)
            if key in provided:
                raise ManifestError(f"插件不能覆盖宿主 Capability：{key}")
            if declaration.exclusive and key in providers:
                raise ManifestError(f"exclusive Capability 冲突：{declaration.kind}/{declaration.name}/{declaration.api}")
            if key in exclusive:
                raise ManifestError(f"exclusive Capability 冲突：{declaration.kind}/{declaration.name}/{declaration.api}")
            providers[key].append(manifest.plugin_id)
            if declaration.exclusive:
                exclusive.add(key)

    dependencies: dict[str, set[str]] = {plugin_id: set() for plugin_id in by_id}
    for manifest in manifests:
        for declaration in manifest.requires:
            key = (declaration.kind, declaration.name, declaration.api)
            supplied_by = providers.get(key, [])
            if not supplied_by and key not in provided and not declaration.optional:
                raise ManifestError(
                    f"缺少 Capability：{manifest.plugin_id} 需要 "
                    f"{declaration.kind}/{declaration.name}/{declaration.api}"
                )
            dependencies[manifest.plugin_id].update(provider for provider in supplied_by if provider != manifest.plugin_id)

    remaining = {plugin_id: set(required) for plugin_id, required in dependencies.items()}
    ordered: list[str] = []
    while remaining:
        ready = sorted(plugin_id for plugin_id, required in remaining.items() if not required)
        if not ready:
            raise ManifestError(f"插件 Capability 依赖环：{', '.join(sorted(remaining))}")
        for plugin_id in ready:
            ordered.append(plugin_id)
            del remaining[plugin_id]
        ready_ids = set(ready)
        for required in remaining.values():
            required.difference_update(ready_ids)
    return tuple(ordered)
