"""把开发资料和真实 SDK 导出为公开仓库可直接使用的自包含目录。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess


KIT = Path(__file__).resolve().parents[1]
REPO = KIT.parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="不存在的输出目录")
    args = parser.parse_args()
    output = args.output.resolve()
    python_sdk = REPO / "sdk/python"
    client_sdk = REPO / "frontend/packages/plugin-sdk/src"
    if not (python_sdk / "pyproject.toml").is_file() or not client_sdk.is_dir():
        parser.error("只在 Host 源码仓库中导出；公开包已经附带 SDK，不需要再次导出")
    if output.exists() or output.is_relative_to(KIT):
        parser.error("输出目录必须尚不存在，且不能位于开发中心内部")
    target = output / "dev/plugin"
    shutil.copytree(KIT, target, ignore=shutil.ignore_patterns(
        "node_modules", "__pycache__", ".venv", "out", "dist"))
    sdk_target = target / "sdk/python"
    sdk_target.mkdir(parents=True)
    shutil.copy2(python_sdk / "pyproject.toml", sdk_target / "pyproject.toml")
    shutil.copytree(python_sdk / "src", sdk_target / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (sdk_target / "README.md").write_text(
        "# More Brain Python SDK\n\n版本 1.0.0，Python 3.11+，无第三方运行依赖。"
        "使用 `python -m pip install -e .` 安装。完整手册见 [开发中心](../../README.md)。\n",
        encoding="utf-8")
    shutil.copytree(client_sdk, target / "sdk/client")
    (target / "sdk/client/package.json").write_text(json.dumps({
        "name": "more-brain-plugin-sdk-source", "private": True, "type": "module",
        "dependencies": {"@types/react": "19.0.8", "react": "19.1.0"},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (target / "sdk/README.md").write_text(
        "# 公共 SDK\n\n"
        "- [Python SDK](python/)：Python 3.11+ 公共契约与静态校验 CLI。\n"
        "- [浏览器 SDK](client/)：TypeScript / React 公共类型、协作工具与状态辅助。\n\n"
        "安装、版本和使用方式见 [SDK 说明](../SDK.md)。\n", encoding="utf-8")
    (target / "sdk/client/README.md").write_text(
        "# 浏览器 TypeScript / React SDK\n\n"
        "源码入口 `index.ts`，运行时模块标识 `@more-brain/plugin-sdk`。"
        "先运行 `npm install` 安装源码的类型依赖。插件编译时读取本目录类型，"
        "React / React DOM / SDK 保持 external，由 More Brain 的 import map 提供运行模块。\n\n"
        "这不是 Node 服务端 SDK，也尚未承诺发布到 npm。"
        "完整 API 与接入见 [SDK 说明](../../SDK.md) 和 [React demo](../../demos/hello-react/)。\n",
        encoding="utf-8")
    (target / "demos/hello-react/client/sdk.d.ts").write_text(
        'export * from "../../../sdk/client/index";\n', encoding="utf-8")
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                              capture_output=True, text=True, check=True).stdout.strip()
    (target / "SDK-SOURCE.md").write_text(
        f"# SDK 来源\n\n导出时 Host 基线 commit：`{revision}`。\n\n"
        "文件取自导出时工作区；如工作区有未提交改动，commit 不是完整内容标识。"
        "公开发布前应复核目标 Host 和本包的一致性。SDK API 1.0.0。\n", encoding="utf-8")
    print(f"已导出：{target}")
    print("未提交或推送 Git；请在仓外安装 SDK、构建 React、检查并打包后发布。")


if __name__ == "__main__":
    main()
