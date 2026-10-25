"""插件调用方可捕获的公共错误。"""

class PluginUnavailable(RuntimeError):
    pass


class PluginGenerationMismatch(PluginUnavailable):
    """浏览器仍持有旧 generation 时的可恢复调用错误。"""

    def __init__(self, plugin_id: str, expected_generation: int, actual_generation: int | None) -> None:
        self.plugin_id = plugin_id
        self.expected_generation = expected_generation
        self.actual_generation = actual_generation
        super().__init__(f"插件 generation 已变化：{plugin_id}")


