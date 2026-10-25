"""More Brain Python 插件 SDK；导入时不加载 Host 或第三方依赖。"""

from .capabilities import CapabilityKey
from .contracts import PluginContext, RuntimePlugin
from .effects import EffectScope
from .errors import PluginGenerationMismatch, PluginUnavailable
from .events import LiveEvent
from .manifest import (
    CLIENT_SDK_API_VERSION,
    HOST_API_VERSION,
    CapabilityDeclaration,
    ClientManifest,
    ManifestError,
    PluginManifest,
    parse_manifest,
    parse_manifest_toml,
    resolve_manifest_order,
)
from .validation import validate_plugin_directory

__version__ = "1.0.0"

__all__ = [
    "CapabilityKey", "PluginContext", "RuntimePlugin", "EffectScope", "LiveEvent",
    "PluginUnavailable", "PluginGenerationMismatch", "PluginManifest", "ClientManifest",
    "CapabilityDeclaration", "ManifestError", "HOST_API_VERSION", "CLIENT_SDK_API_VERSION",
    "parse_manifest", "parse_manifest_toml", "resolve_manifest_order", "validate_plugin_directory",
]
