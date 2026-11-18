#!/usr/bin/env python3
"""Idempotently patch Quickshell ii Ai.qml to add Antigravity (agy) as the default no-key model."""

import pathlib
import sys


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write("Kullanim: patch-agy-ai.py <quickshell-ii-dir>\n")
        return 2
    ai_path = pathlib.Path(sys.argv[1]) / "services/Ai.qml"
    if not ai_path.exists():
        sys.stderr.write(f"  UYARI: {ai_path} bulunamadi.\n")
        return 1

    src = ai_path.read_text(encoding="utf-8")
    if '"antigravity": aiModelComponent.createObject' in src:
        print("  Ai.qml: zaten yamali (antigravity)")
        return 0

    edits = [
        (
            '        "gemini-2.5-flash": aiModelComponent.createObject(this, {',
            '        "antigravity": aiModelComponent.createObject(this, {\n'
            '            "name": "Antigravity (agy)",\n'
            '            "icon": "google-gemini-symbolic",\n'
            '            "description": Translation.tr("Local CLI | Antigravity agent (no API key needed)"),\n'
            '            "homepage": "https://antigravity.google",\n'
            '            "endpoint": "agy",\n'
            '            "model": "antigravity",\n'
            '            "requires_key": false,\n'
            '            "api_format": "agy",\n'
            '        }),\n'
            '        "gemini-2.5-flash": aiModelComponent.createObject(this, {',
        ),
        (
            '            // Fetch API keys if needed\n'
            '            if (model?.requires_key && !KeyringStorage.loaded) KeyringStorage.fetchKeyringData();',
            '            if (model?.api_format === "agy") {\n'
            '                const messageArray = root.messageIDs.map(id => root.messageByID[id]);\n'
            '                const filtered = messageArray.filter(m => m.role !== Ai.interfaceRole);\n'
            '                const recent = filtered.slice(-10);\n'
            '                let promptText = "";\n'
            '                if (recent.length <= 1) {\n'
            '                    promptText = recent[0]?.rawContent ?? recent[0]?.content ?? "";\n'
            '                } else {\n'
            '                    promptText = recent.map(m => (m.role === "user" ? "User: " : "Assistant: ") + (m.rawContent || m.content)).join("\\n\\n");\n'
            '                }\n'
            '                if (root.pendingFilePath && root.pendingFilePath.length > 0) {\n'
            '                    promptText += "\\n\\n[Attached file: " + root.pendingFilePath + "]";\n'
            '                }\n'
            '                requester.message = root.aiMessageComponent.createObject(root, {\n'
            '                    "role": "assistant",\n'
            '                    "model": currentModelId,\n'
            '                    "content": "",\n'
            '                    "rawContent": "",\n'
            '                    "thinking": true,\n'
            '                    "done": false,\n'
            '                });\n'
            '                if (root.pendingFilePath && root.pendingFilePath.length > 0) {\n'
            '                    requester.message.localFilePath = root.pendingFilePath;\n'
            '                    root.pendingFilePath = "";\n'
            '                }\n'
            '                const id = idForMessage(requester.message);\n'
            '                root.messageIDs = [...root.messageIDs, id];\n'
            '                root.messageByID[id] = requester.message;\n'
            '                const agyBin = FileUtils.trimFileProtocol(`${Directories.home}/.local/bin/agy`);\n'
            '                requester.command = [agyBin, "-p", promptText, "--output-format", "text", "--disable-slash-commands"];\n'
            '                requester.running = true;\n'
            '                return;\n'
            '            }\n\n'
            '            // Fetch API keys if needed\n'
            '            if (model?.requires_key && !KeyringStorage.loaded) KeyringStorage.fetchKeyringData();',
        ),
        (
            '                // Handle response line\n'
            '                try {',
            '                if (models[requester.message.model]?.api_format === "agy") {\n'
            '                    const line = (requester.message.rawContent.length > 0 ? "\\n" : "") + data;\n'
            '                    requester.message.rawContent += line;\n'
            '                    requester.message.content += line;\n'
            '                    return;\n'
            '                }\n\n'
            '                // Handle response line\n'
            '                try {',
        ),
        (
            '        onExited: (exitCode, exitStatus) => {\n'
            '            const result = requester.currentStrategy.onRequestFinished(requester.message);',
            '        onExited: (exitCode, exitStatus) => {\n'
            '            if (models[requester.message.model]?.api_format === "agy") {\n'
            '                if (requester.message.thinking) requester.message.thinking = false;\n'
            '                if (exitCode !== 0 && requester.message.content.trim().length === 0) {\n'
            '                    requester.message.content = "agy CLI error (exit " + exitCode + ")";\n'
            '                }\n'
            '                requester.markDone();\n'
            '                return;\n'
            '            }\n'
            '            const result = requester.currentStrategy.onRequestFinished(requester.message);',
        ),
    ]

    for old, new in edits:
        if old not in src:
            sys.stderr.write(f"  UYARI: Ai.qml icinde beklenen blok bulunamadi.\n")
            return 1
        src = src.replace(old, new, 1)

    ai_path.write_text(src, encoding="utf-8")
    print("  Ai.qml: Antigravity (agy) yamasi uygulandi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
