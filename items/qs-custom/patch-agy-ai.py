#!/usr/bin/env python3
"""Idempotently patch Quickshell ii Ai.qml & AiChat.qml for native Antigravity (agy) CLI integration."""

import os
import pathlib
import sys

_FEATS = os.environ.get("DOTSYNC_FEATURES", "all")
_FEAT_SET = {x.strip() for x in _FEATS.split(",") if x.strip()}

def has_feat(name: str) -> bool:
    return _FEATS == "all" or name in _FEAT_SET


def patch_file(path: pathlib.Path, edits: list[tuple[str, str, str]]) -> bool:
    if not path.exists():
        sys.stderr.write(f"  UYARI: {path} bulunamadi.\n")
        return False
    src = path.read_text(encoding="utf-8")
    changed = False
    for edit in edits:
        guard, target, replacement = edit[:3]
        optional = len(edit) > 3 and edit[3] == "optional"
        if guard in src:
            continue
        if target not in src and optional:
            continue  # alternative path for another base version; a later edit handles it
        if target not in src:
            sys.stderr.write(f"  UYARI: {path.name} icinde hedef bulunamadi ({guard}).\n")
            return False
        new_src = src.replace(target, replacement, 1)
        if new_src != src:
            src = new_src
            changed = True
    if changed:
        path.write_text(src, encoding="utf-8")
        print(f"  {path.name}: Antigravity (agy) yamasi uygulandi")
    else:
        print(f"  {path.name}: zaten yamali (antigravity)")
    return True


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write("Kullanim: patch-agy-ai.py <quickshell-ii-dir>\n")
        return 2
    ii = pathlib.Path(sys.argv[1])
    ok = True

    if has_feat("ai-sidebar"):
        # 1. Ai.qml: dynamic agy models + persistent agyConversationId + stream-json requester
        ok &= patch_file(
            ii / "services/Ai.qml",
            [
                (
                    '"antigravity": aiModelComponent.createObject',
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
                    "property string agyConversationId:",
                    "    property var modelList: Object.keys(root.models)",
                    "    property var modelList: Object.keys(root.models)\n"
                    "    property var agyFamilies: []\n"
                    "    property var agyCommands: []\n"
                    "    property string agyConversationId: \"\"\n\n"
                    "    function refreshAgyModels() {\n"
                    "        getAgyModelsProc.running = false;\n"
                    "        getAgyModelsProc.running = true;\n"
                    "    }\n\n"
                    "    Process {\n"
                    "        id: getAgyCommandsProc\n"
                    "        command: [\"python3\", CF.FileUtils.trimFileProtocol(`${Directories.scriptPath}/ai/fetch-agy-commands.py`)]\n"
                    "        running: true\n"
                    "        stdout: StdioCollector {\n"
                    "            onStreamFinished: {\n"
                    "                try {\n"
                    "                    const list = JSON.parse(text);\n"
                    "                    if (Array.isArray(list) && list.length > 0)\n"
                    "                        root.agyCommands = list;\n"
                    "                } catch (e) {\n"
                    "                    console.log(\"[AI] Could not fetch agy commands:\", e);\n"
                    "                }\n"
                    "            }\n"
                    "        }\n"
                    "    }\n\n"
                    "    Process {\n"
                    "        id: getAgyModelsProc\n"
                    "        command: [\"python3\", CF.FileUtils.trimFileProtocol(`${Directories.scriptPath}/ai/fetch-agy-models.py`)]\n"
                    "        running: true\n"
                    "        stdout: StdioCollector {\n"
                    "            onStreamFinished: {\n"
                    "                try {\n"
                    "                    const payload = JSON.parse(text);\n"
                    "                    const list = payload.models ?? [];\n"
                    "                    const updated = {};\n"
                    "                    for (let i = 0; i < list.length; i++) {\n"
                    "                        const m = list[i];\n"
                    "                        updated[m.id] = aiModelComponent.createObject(root, {\n"
                    "                            \"name\": m.name,\n"
                    "                            \"icon\": \"google-gemini-symbolic\",\n"
                    "                            \"description\": Translation.tr(\"Local CLI | Antigravity agent (no API key needed)\"),\n"
                    "                            \"homepage\": \"https://antigravity.google\",\n"
                    "                            \"endpoint\": \"agy\",\n"
                    "                            \"model\": m.id,\n"
                    "                            \"requires_key\": false,\n"
                    "                            \"api_format\": \"agy\",\n"
                    "                        });\n"
                    "                    }\n"
                    "                    if (list.length > 0) {\n"
                    "                        root.models = updated;\n"
                    "                        root.modelList = Object.keys(root.models);\n"
                    "                        root.agyFamilies = payload.families ?? [];\n"
                    "                        if (!root.currentModelId || !(root.currentModelId in root.models)) {\n"
                    "                            const pref = updated[\"gemini-4-hydrogen-medium\"] ? \"gemini-4-hydrogen-medium\" : list[0].id;\n"
                    "                            root.setModel(pref, false);\n"
                    "                        }\n"
                    "                    }\n"
                    "                } catch (e) {\n"
                    "                    console.log(\"[AI] Could not fetch agy models:\", e);\n"
                    "                }\n"
                    "            }\n"
                    "        }\n"
                    "    }",
                ),
                (
                    "function stopGeneration()",
                    "    function clearMessages() {",
                    "    readonly property bool isGenerating: requester.running\n\n"
                    "    function stopGeneration() {\n"
                    "        if (!requester.running) return;\n"
                    "        requester.running = false;\n"
                    "        if (requester.message) {\n"
                    "            requester.message.thinking = false;\n"
                    "            requester.markDone();\n"
                    "        }\n"
                    "    }\n\n"
                    "    function clearMessages() {\n"
                    "        root.agyConversationId = \"\";",
                ),
                (
                    'model?.api_format === "agy"',
                    '            // Fetch API keys if needed\n'
                    '            if (model?.requires_key && !KeyringStorage.loaded) KeyringStorage.fetchKeyringData();',
                    '            if (model?.api_format === "agy") {\n'
                    '                const messageArray = root.messageIDs.map(id => root.messageByID[id]);\n'
                    '                const filtered = messageArray.filter(m => m.role !== Ai.interfaceRole);\n'
                    '                const lastUser = filtered[filtered.length - 1];\n'
                    '                let promptText = lastUser?.rawContent ?? lastUser?.content ?? "";\n'
                    '                if (!root.agyConversationId && filtered.length > 1) {\n'
                    '                    promptText = filtered.slice(-10).map(m => (m.role === "user" ? "User: " : "Assistant: ") + (m.rawContent || m.content)).join("\\n\\n");\n'
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
                    '                const agyBin = CF.FileUtils.trimFileProtocol(`${Directories.home}/.local/bin/agy`);\n'
                    '                const modelArgs = (model.model && model.model !== "antigravity") ? ["--model", model.model] : [];\n'
                    '                const convArgs = root.agyConversationId ? ["--conversation", root.agyConversationId] : [];\n'
                    '                const slashArgs = promptText.trim().startsWith("/") ? [] : ["--disable-slash-commands"];\n'
                    '                requester.command = [agyBin, "-p", promptText, ...modelArgs, ...convArgs, "--output-format", "stream-json", ...slashArgs];\n'
                    '                requester.running = true;\n'
                    '                return;\n'
                    '            }\n\n'
                    '            // Fetch API keys if needed\n'
                    '            if (model?.requires_key && !KeyringStorage.loaded) KeyringStorage.fetchKeyringData();',
                ),
                (
                    'models[requester.message.model]?.api_format === "agy"',
                    '                // Handle response line\n'
                    '                try {',
                    '                if (models[requester.message.model]?.api_format === "agy") {\n'
                    '                    try {\n'
                    '                        const ev = JSON.parse(data);\n'
                    '                        if (ev.conversation_id) root.agyConversationId = ev.conversation_id;\n'
                    '                        if (ev.event === "step_update" && ev.step_update?.step_type === "agent_response") {\n'
                    '                            if (ev.step_update.conversation_id) root.agyConversationId = ev.step_update.conversation_id;\n'
                    '                            if (ev.step_update.text_delta) {\n'
                    '                                requester.message.rawContent += ev.step_update.text_delta;\n'
                    '                                requester.message.content += ev.step_update.text_delta;\n'
                    '                            }\n'
                    '                            if (ev.step_update.usage) {\n'
                    '                                root.tokenCount.input = ev.step_update.usage.input_tokens ?? -1;\n'
                    '                                root.tokenCount.output = ev.step_update.usage.output_tokens ?? -1;\n'
                    '                                root.tokenCount.total = ev.step_update.usage.total_tokens ?? -1;\n'
                    '                            }\n'
                    '                        } else if (ev.event === "result" && ev.result) {\n'
                    '                            if (ev.result.conversation_id) root.agyConversationId = ev.result.conversation_id;\n'
                    '                            if (ev.result.response && requester.message.rawContent.length === 0) {\n'
                    '                                requester.message.rawContent = ev.result.response;\n'
                    '                                requester.message.content = ev.result.response;\n'
                    '                            }\n'
                    '                            if (ev.result.usage) {\n'
                    '                                root.tokenCount.input = ev.result.usage.input_tokens ?? -1;\n'
                    '                                root.tokenCount.output = ev.result.usage.output_tokens ?? -1;\n'
                    '                                root.tokenCount.total = ev.result.usage.total_tokens ?? -1;\n'
                    '                            }\n'
                    '                        }\n'
                    '                    } catch (e) {}\n'
                    '                    return;\n'
                    '                }\n\n'
                    '                // Handle response line\n'
                    '                try {',
                ),
                (
                    "function addUserModels() { return; }",
                    "    function addUserModels() {\n        (Config?.options.ai?.extraModels ?? []).forEach(model => {",
                    "    function addUserModels() { return; }\n"
                    "    function _unusedAddUserModels() {\n        (Config?.options.ai?.extraModels ?? []).forEach(model => {",
                ),
                (
                    'if (models[requester.message.model]?.api_format === "agy") {\n                if (requester.message.thinking)',
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
                (
                    'models["antigravity"] ?? models[modelList[0]]',
                    '    function getModel() {\n'
                    '        return models[currentModelId];\n'
                    '    }',
                    '    function getModel() {\n'
                    '        return models[currentModelId] ?? models["antigravity"] ?? models[modelList[0]];\n'
                    '    }',
                ),
                (
                    "?? {})\n    property var toolDescriptions",
                    "    property list<var> availableTools: Object.keys(root.tools[models[currentModelId]?.api_format])\n",
                    "    property list<var> availableTools: Object.keys(root.tools[models[currentModelId]?.api_format] ?? {})\n",
                ),
                (
                    'apiStrategies[models[currentModelId]?.api_format || "openai"] ?? ',
                    '    property ApiStrategy currentApiStrategy: apiStrategies[models[currentModelId]?.api_format || "openai"]\n',
                    '    property ApiStrategy currentApiStrategy: apiStrategies[models[currentModelId]?.api_format || "openai"] ?? apiStrategies["openai"]\n',
                ),
            ],
        )

        # 2. AiChat.qml: hide useless key/temp/tool pills for agy, native CLI-style / popup, clickable model picker
        ok &= patch_file(
            ii / "modules/ii/sidebarLeft/AiChat.qml",
            [
                (
                    'property bool agyLoggedIn: true',
                    '    property string commandPrefix: "/"',
                    '    property string commandPrefix: "/"\n'
                    '    property bool modelPickerOpen: false\n'
                    '    property bool configPickerOpen: false\n'
                    '    property bool agyLoggedIn: true\n\n'
                    '    function refreshAgyAuth() {\n'
                    '        agyAuthProc.running = false;\n'
                    '        agyAuthProc.running = true;\n'
                    '    }\n\n'
                    '    function openAgyLogin() {\n'
                    '        const agyBin = FileUtils.trimFileProtocol(`${Directories.home}/.local/bin/agy`);\n'
                    '        agyLoginProc.command = ["bash", "-c", `${Config.options.apps.terminal} -e bash -c \'"$1" -i /login; echo; read -p "Press Enter to close..."\' _ "$1"`, "_", agyBin];\n'
                    '        agyLoginProc.running = false;\n'
                    '        agyLoginProc.running = true;\n'
                    '    }\n\n'
                    '    Process {\n'
                    '        id: agyAuthProc\n'
                    '        command: ["bash", "-c", "if [ -s \\"$HOME/.gemini/antigravity-cli/antigravity-oauth-token\\" ]; then echo 1; else d=$(mktemp -d); printf \'#!/bin/sh\\\\nexit 0\\\\n\' > \\"$d/xdg-open\\"; chmod +x \\"$d/xdg-open\\"; PATH=\\"$d:$PATH\\" BROWSER=true timeout 4 \\"$HOME/.local/bin/agy\\" models >/dev/null 2>&1 && echo 1 || echo 0; rm -rf \\"$d\\"; fi"]\n'
                    '        stdout: StdioCollector {\n'
                    '            onStreamFinished: root.agyLoggedIn = (text.trim() === "1")\n'
                    '        }\n'
                    '    }\n\n'
                    '    Process {\n'
                    '        id: agyLoginProc\n'
                    '        onExited: {\n'
                    '            root.refreshAgyAuth();\n'
                    '            Ai.refreshAgyModels();\n'
                    '        }\n'
                    '    }\n\n'
                    '    Component.onCompleted: root.refreshAgyAuth()\n'
                    '    onVisibleChanged: {\n'
                    '        if (visible) {\n'
                    '            root.refreshAgyAuth();\n'
                    '            if (Ai.agyFamilies.length === 0) Ai.refreshAgyModels();\n'
                    '        }\n'
                    '    }',
                ),
                (
                    'root.openAgyLogin()',
                    '        if (inputText.startsWith(root.commandPrefix)) {',
                    '        if (Ai.getModel()?.api_format === "agy" && inputText.startsWith(root.commandPrefix)) {\n'
                    '            const parts = inputText.trim().split(/\\s+/);\n'
                    '            const cmd = parts[0].substring(1);\n'
                    '            if (cmd === "model" || cmd === "effort") { root.configPickerOpen = false; root.modelPickerOpen = true; return; }\n'
                    '            if (cmd === "config" || cmd === "settings") { root.modelPickerOpen = false; root.configPickerOpen = true; return; }\n'
                    '            if (cmd === "login") {\n'
                    '                root.openAgyLogin();\n'
                    '                return;\n'
                    '            }\n'
                    '            if (cmd === "clear") { Ai.clearMessages(); return; }\n'
                    '            Ai.sendUserMessage(inputText);\n'
                    '            return;\n'
                    '        }\n'
                    '        if (inputText.startsWith(root.commandPrefix)) {',
                ),
                (
                    "visible: (Ai.getModel()?.api_format !== \"agy\") || Ai.tokenCount.total > 0",
                    '            Rectangle {\n                id: statusBg\n',
                    '            Rectangle {\n                id: statusBg\n                visible: (Ai.getModel()?.api_format !== "agy") || Ai.tokenCount.total > 0\n',
                ),
                (
                    "visible: Ai.getModel()?.requires_key ?? true",
                    '                    StatusItem {\n                        icon: Ai.currentModelHasApiKey ? "key" : "key_off"',
                    '                    StatusItem {\n                        visible: Ai.getModel()?.requires_key ?? true\n                        icon: Ai.currentModelHasApiKey ? "key" : "key_off"',
                ),
                (
                    'visible: Ai.getModel()?.api_format !== "agy"\n                        icon: "device_thermostat"',
                    '                    StatusSeparator {}\n                    StatusItem {\n                        icon: "device_thermostat"',
                    '                    StatusSeparator { visible: Ai.getModel()?.requires_key ?? true }\n                    StatusItem {\n                        visible: Ai.getModel()?.api_format !== "agy"\n                        icon: "device_thermostat"',
                ),
                (
                    'const isAgy = Ai.getModel()?.api_format === "agy";',
                    '                                root.suggestionList = root.allCommands.filter(cmd => cmd.name.startsWith(messageInputField.text.substring(1))).map(cmd => {',
                    '                                const isAgy = Ai.getModel()?.api_format === "agy";\n'
                    '                                if (isAgy) {\n'
                    '                                    const q = messageInputField.text.substring(1).toLowerCase();\n'
                    '                                    root.suggestionList = Ai.agyCommands.filter(cmd => cmd.name.startsWith(q)).map(cmd => ({\n'
                    '                                        name: `${root.commandPrefix}${cmd.name}`,\n'
                    '                                        description: cmd.description,\n'
                    '                                        instant: cmd.instant,\n'
                    '                                    }));\n'
                    '                                    return;\n'
                    '                                }\n'
                    '                                root.suggestionList = root.allCommands.filter(cmd => cmd.name.startsWith(messageInputField.text.substring(1))).map(cmd => {',
                ),
                (
                    "if (isInstant && Ai.getModel()?.api_format === \"agy\")",
                    '            function acceptSuggestion(word) {\n'
                    '                const words = messageInputField.text.trim().split(/\\s+/);',
                    '            function acceptSuggestion(word, isInstant = false) {\n'
                    '                if (isInstant && Ai.getModel()?.api_format === "agy") {\n'
                    '                    messageInputField.clear();\n'
                    '                    root.handleInput(word);\n'
                    '                    return;\n'
                    '                }\n'
                    '                const words = messageInputField.text.trim().split(/\\s+/);',
                ),
                (
                    "// Native CLI-style command & suggestion palette",
                    "        FlowButtonGroup { // Suggestions\n"
                    "            id: suggestions\n"
                    "            visible: root.suggestionList.length > 0 && messageInputField.text.length > 0\n"
                    "            property int selectedIndex: 0\n"
                    "            Layout.fillWidth: true\n"
                    "            spacing: 5\n\n"
                    "            Repeater {\n"
                    "                id: suggestionRepeater\n"
                    "                model: {\n"
                    "                    suggestions.selectedIndex = 0;\n"
                    "                    return root.suggestionList.slice(0, 10);\n"
                    "                }\n"
                    "                delegate: ApiCommandButton {\n"
                    "                    id: commandButton\n"
                    "                    colBackground: suggestions.selectedIndex === index ? Appearance.colors.colSecondaryContainerHover : Appearance.colors.colSecondaryContainer\n"
                    "                    bounce: false\n"
                    "                    contentItem: StyledText {\n"
                    "                        font.pixelSize: Appearance.font.pixelSize.small\n"
                    "                        color: Appearance.m3colors.m3onSurface\n"
                    "                        horizontalAlignment: Text.AlignHCenter\n"
                    "                        text: modelData.displayName ?? modelData.name\n"
                    "                    }\n\n"
                    "                    onHoveredChanged: {\n"
                    "                        if (commandButton.hovered) {\n"
                    "                            suggestions.selectedIndex = index;\n"
                    "                        }\n"
                    "                    }\n"
                    "                    onClicked: {\n"
                    "                        suggestions.acceptSuggestion(modelData.name);\n"
                    "                    }\n"
                    "                }\n"
                    "            }",
                    "        Rectangle { // Native CLI-style command & suggestion palette\n"
                    "            id: suggestions\n"
                    "            visible: root.suggestionList.length > 0 && messageInputField.text.length > 0\n"
                    "            property int selectedIndex: 0\n"
                    "            Layout.fillWidth: true\n"
                    "            implicitHeight: Math.min(220, suggestionListView.contentHeight + 12)\n"
                    "            clip: true\n"
                    "            radius: Appearance.rounding.normal\n"
                    "            color: Appearance.colors.colLayer2\n"
                    "            border.width: 1\n"
                    "            border.color: Appearance.colors.colOutlineVariant\n\n"
                    "            ListView {\n"
                    "                id: suggestionListView\n"
                    "                anchors.fill: parent\n"
                    "                anchors.margins: 6\n"
                    "                clip: true\n"
                    "                spacing: 2\n"
                    "                currentIndex: suggestions.selectedIndex\n"
                    "                highlightFollowsCurrentItem: true\n"
                    "                onCurrentIndexChanged: positionViewAtIndex(currentIndex, ListView.Contain)\n"
                    "                model: {\n"
                    "                    suggestions.selectedIndex = 0;\n"
                    "                    return root.suggestionList;\n"
                    "                }\n"
                    "                delegate: RippleButton {\n"
                    "                    id: commandButton\n"
                    "                    required property var modelData\n"
                    "                    required property int index\n"
                    "                    readonly property bool active: suggestions.selectedIndex === index\n"
                    "                    width: suggestionListView.width\n"
                    "                    implicitHeight: 32\n"
                    "                    buttonRadius: Appearance.rounding.small\n"
                    "                    colBackground: active ? Appearance.colors.colPrimaryContainer : \"transparent\"\n"
                    "                    colBackgroundHover: active ? Appearance.colors.colPrimaryContainer : Appearance.colors.colSurfaceContainerHigh\n"
                    "                    onHoveredChanged: {\n"
                    "                        if (commandButton.hovered)\n"
                    "                            suggestions.selectedIndex = index;\n"
                    "                    }\n"
                    "                    onClicked: suggestions.acceptSuggestion(modelData.name, modelData.instant ?? false)\n\n"
                    "                    contentItem: RowLayout {\n"
                    "                        anchors.fill: parent\n"
                    "                        anchors.leftMargin: 8\n"
                    "                        anchors.rightMargin: 8\n"
                    "                        spacing: 10\n"
                    "                        StyledText {\n"
                    "                            font.pixelSize: Appearance.font.pixelSize.small\n"
                    "                            font.family: Appearance.font.family.monospace\n"
                    "                            font.weight: Font.Medium\n"
                    "                            color: commandButton.active ? Appearance.colors.colPrimary : Appearance.m3colors.m3onSurface\n"
                    "                            text: modelData.displayName ?? modelData.name\n"
                    "                        }\n"
                    "                        StyledText {\n"
                    "                            Layout.fillWidth: true\n"
                    "                            font.pixelSize: Appearance.font.pixelSize.smaller\n"
                    "                            color: commandButton.active ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colSubtext\n"
                    "                            horizontalAlignment: Text.AlignRight\n"
                    "                            maximumLineCount: 1\n"
                    "                            elide: Text.ElideRight\n"
                    "                            text: (modelData.description ?? \"\").replace(/\\n+/g, \" · \")\n"
                    "                        }\n"
                    "                    }\n"
                    "                }\n"
                    "            }",
                ),
                (
                    "id: agyAuthRow",
                    "        Rectangle { // Input area",
                    "        Rectangle {\n"
                    "            visible: (Ai.getModel()?.api_format === \"agy\") && (!root.agyLoggedIn || agyLoginProc.running)\n"
                    "            Layout.fillWidth: true\n"
                    "            implicitHeight: agyAuthCol.implicitHeight + 16\n"
                    "            radius: Appearance.rounding.normal\n"
                    "            color: Appearance.colors.colLayer2\n"
                    "            border.width: 1\n"
                    "            border.color: Appearance.colors.colOutlineVariant\n\n"
                    "            ColumnLayout {\n"
                    "                id: agyAuthCol\n"
                    "                anchors.fill: parent\n"
                    "                anchors.margins: 8\n"
                    "                spacing: 6\n\n"
                    "                RowLayout {\n"
                    "                    id: agyAuthRow\n"
                    "                    Layout.fillWidth: true\n"
                    "                    spacing: 8\n"
                    "                    MaterialLoadingIndicator {\n"
                    "                        visible: agyLoginProc.running\n"
                    "                        implicitSize: 18\n"
                    "                    }\n"
                    "                    MaterialSymbol {\n"
                    "                        visible: !agyLoginProc.running\n"
                    "                        text: \"passkey\"\n"
                    "                        iconSize: 20\n"
                    "                        color: Appearance.colors.colPrimary\n"
                    "                    }\n"
                    "                    StyledText {\n"
                    "                        Layout.fillWidth: true\n"
                    "                        font.pixelSize: Appearance.font.pixelSize.smaller\n"
                    "                        color: Appearance.m3colors.m3onSurface\n"
                    "                        elide: Text.ElideRight\n"
                    "                        text: agyLoginProc.running\n"
                    "                            ? Translation.tr(\"Signing in to Agy...\")\n"
                    "                            : Translation.tr(\"Sign in required to use Agy\")\n"
                    "                    }\n"
                    "                    RippleButton {\n"
                    "                        implicitWidth: agyLoginBtnTxt.implicitWidth + 20\n"
                    "                        implicitHeight: 28\n"
                    "                        buttonRadius: Appearance.rounding.full\n"
                    "                        enabled: !agyLoginProc.running\n"
                    "                        colBackground: Appearance.colors.colPrimary\n"
                    "                        onClicked: root.openAgyLogin()\n"
                    "                        contentItem: StyledText {\n"
                    "                            id: agyLoginBtnTxt\n"
                    "                            anchors.centerIn: parent\n"
                    "                            font.pixelSize: Appearance.font.pixelSize.smaller\n"
                    "                            font.weight: Font.Medium\n"
                    "                            color: Appearance.m3colors.m3onPrimary\n"
                    "                            text: agyLoginProc.running ? Translation.tr(\"Waiting...\") : Translation.tr(\"Sign in\")\n"
                    "                        }\n"
                    "                    }\n"
                    "                    RippleButton {\n"
                    "                        implicitWidth: 28\n"
                    "                        implicitHeight: 28\n"
                    "                        buttonRadius: Appearance.rounding.full\n"
                    "                        onClicked: root.refreshAgyAuth()\n"
                    "                        contentItem: MaterialSymbol {\n"
                    "                            anchors.centerIn: parent\n"
                    "                            text: \"refresh\"\n"
                    "                            iconSize: 16\n"
                    "                            color: Appearance.m3colors.m3onSurface\n"
                    "                        }\n"
                    "                    }\n"
                    "                }\n\n"
                    "            }\n"
                    "        }\n\n"
                    "        AgyModelPicker {\n"
                    "            visible: root.modelPickerOpen\n"
                    "            Layout.fillWidth: true\n"
                    "            onCloseRequested: root.modelPickerOpen = false\n"
                    "        }\n\n"
                    "        AgyConfigPicker {\n"
                    "            visible: root.configPickerOpen\n"
                    "            Layout.fillWidth: true\n"
                    "            onCloseRequested: root.configPickerOpen = false\n"
                    "        }\n\n"
                    "        Rectangle { // Input area",
                ),
                (
                    "root.modelPickerOpen = !root.modelPickerOpen",
                    '                ApiInputBoxIndicator {\n'
                    '                    // Model indicator\n'
                    '                    icon: "api"\n'
                    '                    text: Ai.getModel().name\n'
                    '                    tooltipText: Translation.tr("Current model: %1\\nSet it with %2model MODEL").arg(Ai.getModel().name).arg(root.commandPrefix)\n'
                    '                }',
                    '                ApiInputBoxIndicator {\n'
                    '                    // Model indicator (clickable -> AgyModelPicker)\n'
                    '                    icon: "api"\n'
                    '                    text: Ai.getModel()?.name ?? ""\n'
                    '                    tooltipText: Translation.tr("Current model: %1\\nSet it with %2model MODEL").arg(Ai.getModel()?.name ?? "").arg(root.commandPrefix)\n'
                    '                    MouseArea {\n'
                    '                        z: 10\n'
                    '                        anchors.fill: parent\n'
                    '                        cursorShape: Qt.PointingHandCursor\n'
                    '                        onClicked: root.modelPickerOpen = !root.modelPickerOpen\n'
                    '                    }\n'
                    '                }',
                ),
                (
                    "root.modelPickerOpen = false;\n                                    root.configPickerOpen = false;",
                    '                            } else if (event.key === Qt.Key_Escape) {\n'
                    '                                // Esc to detach file\n'
                    '                                if (Ai.pendingFilePath.length > 0) {',
                    '                            } else if (event.key === Qt.Key_Escape) {\n'
                    '                                if (root.modelPickerOpen || root.configPickerOpen) {\n'
                    '                                    root.modelPickerOpen = false;\n'
                    '                                    root.configPickerOpen = false;\n'
                    '                                    event.accepted = true;\n'
                    '                                } else if (suggestions.visible) {\n'
                    '                                    messageInputField.clear();\n'
                    '                                    event.accepted = true;\n'
                    '                                } else if (Ai.pendingFilePath.length > 0) {',
                ),
                (
                    "onActiveFocusChanged: if (activeFocus) { root.modelPickerOpen = false; root.configPickerOpen = false; }",
                    '                    StyledTextArea { // The actual TextArea (inside ScrollView to enable scrolling)\n                        id: messageInputField',
                    '                    StyledTextArea { // The actual TextArea (inside ScrollView to enable scrolling)\n                        id: messageInputField\n                        onActiveFocusChanged: if (activeFocus) { root.modelPickerOpen = false; root.configPickerOpen = false; }',
                ),
                (
                    "suggestions.acceptSuggestion(sel.name, sel.instant ?? false);",
                    '                            } else if ((event.key === Qt.Key_Enter || event.key === Qt.Key_Return)) {\n'
                    '                                if (event.modifiers & Qt.ShiftModifier) {\n'
                    '                                    // Insert newline\n'
                    '                                    messageInputField.insert(messageInputField.cursorPosition, "\\n");\n'
                    '                                    event.accepted = true;\n'
                    '                                } else {',
                    '                            } else if ((event.key === Qt.Key_Enter || event.key === Qt.Key_Return)) {\n'
                    '                                if (event.modifiers & Qt.ShiftModifier) {\n'
                    '                                    // Insert newline\n'
                    '                                    messageInputField.insert(messageInputField.cursorPosition, "\\n");\n'
                    '                                    event.accepted = true;\n'
                    '                                } else if (suggestions.visible && root.suggestionList.length > 0 && Ai.getModel()?.api_format === "agy") {\n'
                    '                                    const sel = root.suggestionList[suggestions.selectedIndex] ?? root.suggestionList[0];\n'
                    '                                    if (sel) {\n'
                    '                                        suggestions.acceptSuggestion(sel.name, sel.instant ?? false);\n'
                    '                                        event.accepted = true;\n'
                    '                                        return;\n'
                    '                                    }\n'
                    '                                } else {',
                ),
                (
                    "Ai.stopGeneration()",
                    '                    enabled: messageInputField.text.length > 0\n'
                    '                    toggled: enabled\n\n'
                    '                    MouseArea {\n'
                    '                        anchors.fill: parent\n'
                    '                        cursorShape: sendButton.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor\n'
                    '                        onClicked: {\n'
                    '                            const inputText = messageInputField.text;\n'
                    '                            root.handleInput(inputText);\n'
                    '                            messageInputField.clear();\n'
                    '                        }\n'
                    '                    }\n\n'
                    '                    contentItem: MaterialSymbol {\n'
                    '                        anchors.centerIn: parent\n'
                    '                        horizontalAlignment: Text.AlignHCenter\n'
                    '                        iconSize: 22\n'
                    '                        color: sendButton.enabled ? Appearance.m3colors.m3onPrimary : Appearance.colors.colOnLayer2Disabled\n'
                    '                        text: "arrow_upward"\n'
                    '                    }',
                    '                    enabled: Ai.isGenerating || messageInputField.text.length > 0\n'
                    '                    toggled: enabled\n\n'
                    '                    MouseArea {\n'
                    '                        anchors.fill: parent\n'
                    '                        cursorShape: sendButton.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor\n'
                    '                        onClicked: {\n'
                    '                            if (Ai.isGenerating) {\n'
                    '                                Ai.stopGeneration();\n'
                    '                            } else {\n'
                    '                                const inputText = messageInputField.text;\n'
                    '                                root.handleInput(inputText);\n'
                    '                                messageInputField.clear();\n'
                    '                            }\n'
                    '                        }\n'
                    '                    }\n\n'
                    '                    contentItem: MaterialSymbol {\n'
                    '                        anchors.centerIn: parent\n'
                    '                        horizontalAlignment: Text.AlignHCenter\n'
                    '                        iconSize: 22\n'
                    '                        color: sendButton.enabled ? Appearance.m3colors.m3onPrimary : Appearance.colors.colOnLayer2Disabled\n'
                    '                        text: Ai.isGenerating ? "stop" : "arrow_upward"\n'
                    '                    }',
                ),
                (
                    "if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_C && Ai.isGenerating",
                    '                            } else if ((event.key === Qt.Key_Enter || event.key === Qt.Key_Return)) {',
                    '                            } else if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_C && Ai.isGenerating && messageInputField.selectedText.length === 0) {\n'
                    '                                Ai.stopGeneration();\n'
                    '                                event.accepted = true;\n'
                    '                            } else if ((event.key === Qt.Key_Enter || event.key === Qt.Key_Return)) {',
                ),
                (
                    "visible: root.modelPickerOpen || root.configPickerOpen\n                z: 5",
                    "            StyledListView { // Message list",
                    "            MouseArea {\n"
                    "                anchors.fill: parent\n"
                    "                visible: root.modelPickerOpen || root.configPickerOpen\n"
                    "                z: 5\n"
                    "                onPressed: mouse => {\n"
                    "                    root.modelPickerOpen = false;\n"
                    "                    root.configPickerOpen = false;\n"
                    "                    mouse.accepted = false;\n"
                    "                }\n"
                    "            }\n"
                    "            StyledListView { // Message list",
                ),
                (
                    'visible: Ai.getModel()?.api_format !== "agy"\n                    // Tool indicator',
                    '                ApiInputBoxIndicator {\n                    // Tool indicator',
                    '                ApiInputBoxIndicator {\n                    visible: Ai.getModel()?.api_format !== "agy"\n                    // Tool indicator',
                ),
            ],
        )

        # 3. AiMessage.qml: clean Claude Code / CLI flat style for agy messages
        ok &= patch_file(
            ii / "modules/ii/sidebarLeft/aiChat/AiMessage.qml",
            [
                (
                    "readonly property bool cliStyle:",
                    "    property bool editing: false",
                    "    property bool editing: false\n"
                    "    readonly property bool cliStyle: (Ai.models[root.messageData?.model]?.api_format === \"agy\") || (Ai.getModel()?.api_format === \"agy\")",
                ),
                (
                    "color: root.cliStyle ?",
                    "    radius: Appearance.rounding.normal\n"
                    "    color: Appearance.colors.colLayer1",
                    "    radius: root.cliStyle ? Appearance.rounding.small : Appearance.rounding.normal\n"
                    "    color: root.cliStyle ? (messageData?.role === \"user\" ? ColorUtils.transparentize(Appearance.colors.colLayer2, 0.45) : \"transparent\") : Appearance.colors.colLayer1",
                ),
                (
                    "color: root.cliStyle ? \"transparent\" : Appearance.colors.colSecondaryContainer",
                    "        Rectangle {\n"
                    "            Layout.fillWidth: true\n"
                    "            implicitWidth: headerRowLayout.implicitWidth + 4 * 2\n"
                    "            implicitHeight: headerRowLayout.implicitHeight + 4 * 2\n"
                    "            color: Appearance.colors.colSecondaryContainer",
                    "        Rectangle {\n"
                    "            Layout.fillWidth: true\n"
                    "            implicitWidth: headerRowLayout.implicitWidth + 4 * 2\n"
                    "            implicitHeight: root.cliStyle ? (headerRowLayout.implicitHeight + 2) : (headerRowLayout.implicitHeight + 4 * 2)\n"
                    "            color: root.cliStyle ? \"transparent\" : Appearance.colors.colSecondaryContainer",
                ),
                (
                    "id: editButton\n                        visible: !root.cliStyle",
                    "                    AiMessageControlButton {\n                        id: editButton",
                    "                    AiMessageControlButton {\n                        id: editButton\n                        visible: !root.cliStyle",
                ),
                (
                    "id: toggleMarkdownButton\n                        visible: !root.cliStyle",
                    "                    AiMessageControlButton {\n                        id: toggleMarkdownButton",
                    "                    AiMessageControlButton {\n                        id: toggleMarkdownButton\n                        visible: !root.cliStyle",
                ),
            ],
        )

        # 4. MessageCodeBlock.qml: green/red diff highlighting for diff blocks
        ok &= patch_file(
            ii / "modules/ii/sidebarLeft/aiChat/MessageCodeBlock.qml",
            [
                (
                    "function formatDiffHtml(raw)",
                    "                        text: segmentContent",
                    "                        function formatDiffHtml(raw) {\n"
                    "                            const esc = s => s.replace(/&/g, \"&amp;\").replace(/</g, \"&lt;\").replace(/>/g, \"&gt;\");\n"
                    "                            return raw.split(\"\\n\").map(ln => {\n"
                    "                                if (ln.startsWith(\"+\") && !ln.startsWith(\"+++\")) return `<font color=\"#a6e3a1\">${esc(ln)}</font>`;\n"
                    "                                if (ln.startsWith(\"-\") && !ln.startsWith(\"---\")) return `<font color=\"#f38ba8\">${esc(ln)}</font>`;\n"
                    "                                if (ln.startsWith(\"@@\")) return `<font color=\"#89b4fa\">${esc(ln)}</font>`;\n"
                    "                                return esc(ln);\n"
                    "                            }).join(\"<br>\");\n"
                    "                        }\n"
                    "                        readonly property bool isDiffBlock: !editing && (segmentLang === \"diff\" || (/^\\+[^+]/m.test(segmentContent) && /^-[^-]/m.test(segmentContent)))\n"
                    "                        textFormat: isDiffBlock ? TextEdit.RichText : TextEdit.PlainText\n"
                    "                        text: isDiffBlock ? formatDiffHtml(segmentContent) : segmentContent",
                ),
            ],
        )

        # 5. SidebarLeftContent.qml: tabs Claude | Agy | Codex | Anime
        ok &= patch_file(
            ii / "modules/ii/sidebarLeft/SidebarLeftContent.qml",
            [
                (
                    '"name": "Codex"',
                    '        ...(root.aiChatEnabled ? [{"icon": "neurology", "name": Translation.tr("Intelligence")}] : []),',
                    '        ...(root.aiChatEnabled ? [\n'
                    '            {"icon": "neurology", "name": "Claude"},\n'
                    '            {"icon": "auto_awesome", "name": "Agy"},\n'
                    '            {"icon": "terminal", "name": "Codex"}\n'
                    '        ] : []),',
                ),
                (
                    "claudeChat.createObject()",
                    "                    ...(root.aiChatEnabled ? [aiChat.createObject()] : []),",
                    "                    ...(root.aiChatEnabled ? [claudeChat.createObject(), aiChat.createObject(), codexChat.createObject()] : []),",
                ),
                (
                    "id: claudeChat",
                    "        Component {\n            id: aiChat",
                    "        Component {\n"
                    "            id: claudeChat\n"
                    "            CliChatPanel { backend: \"claude\" }\n"
                    "        }\n"
                    "        Component {\n"
                    "            id: codexChat\n"
                    "            CliChatPanel { backend: \"codex\" }\n"
                    "        }\n"
                    "        Component {\n            id: aiChat",
                ),
                (
                    "(!root.aiChatEnabled && !root.translatorEnabled && !root.animeEnabled)",
                    "                    ...((root.tabButtonList.length === 0 || (!root.aiChatEnabled && !root.translatorEnabled && root.animeCloset)) ? [placeholder.createObject()] : []),",
                    "                    ...(((!root.aiChatEnabled && !root.translatorEnabled && !root.animeEnabled) || (!root.aiChatEnabled && !root.translatorEnabled && root.animeCloset)) ? [placeholder.createObject()] : []),",
                ),
                (
                    "SwipeView.isCurrentItem",
                    "        Component {\n"
                    "            id: claudeChat\n"
                    "            CliChatPanel { backend: \"claude\" }\n"
                    "        }\n"
                    "        Component {\n"
                    "            id: codexChat\n"
                    "            CliChatPanel { backend: \"codex\" }\n"
                    "        }\n"
                    "        Component {\n"
                    "            id: aiChat\n"
                    "            AiChat {}\n"
                    "        }\n"
                    "        Component {\n"
                    "            id: translator\n"
                    "            Translator {}\n"
                    "        }\n"
                    "        Component {\n"
                    "            id: anime\n"
                    "            Anime {}\n"
                    "        }",
                    "        Component {\n"
                    "            id: claudeChat\n"
                    "            CliChatPanel {\n"
                    "                backend: \"claude\"\n"
                    "                visible: SwipeView.isCurrentItem || (swipeView.contentItem?.moving ?? false)\n"
                    "                enabled: SwipeView.isCurrentItem\n"
                    "            }\n"
                    "        }\n"
                    "        Component {\n"
                    "            id: codexChat\n"
                    "            CliChatPanel {\n"
                    "                backend: \"codex\"\n"
                    "                visible: SwipeView.isCurrentItem || (swipeView.contentItem?.moving ?? false)\n"
                    "                enabled: SwipeView.isCurrentItem\n"
                    "            }\n"
                    "        }\n"
                    "        Component {\n"
                    "            id: aiChat\n"
                    "            AiChat {\n"
                    "                visible: SwipeView.isCurrentItem || (swipeView.contentItem?.moving ?? false)\n"
                    "                enabled: SwipeView.isCurrentItem\n"
                    "            }\n"
                    "        }\n"
                    "        Component {\n"
                    "            id: translator\n"
                    "            Translator {\n"
                    "                visible: SwipeView.isCurrentItem || (swipeView.contentItem?.moving ?? false)\n"
                    "                enabled: SwipeView.isCurrentItem\n"
                    "            }\n"
                    "        }\n"
                    "        Component {\n"
                    "            id: anime\n"
                    "            Anime {\n"
                    "                visible: SwipeView.isCurrentItem || (swipeView.contentItem?.moving ?? false)\n"
                    "                enabled: SwipeView.isCurrentItem\n"
                    "            }\n"
                    "        }",
                ),
            ],
        )

        # 6. Anime.qml: clickable provider picker, / button instead of /mode, shared CliSlashList + Esc/click-outside
        ok &= patch_file(
            ii / "modules/ii/sidebarLeft/Anime.qml",
            [
                (
                    "property bool providerPickerOpen: false",
                    '    property string commandPrefix: "/"',
                    '    property string commandPrefix: "/"\n    property bool providerPickerOpen: false',
                ),
                (
                    "CliSlashList {",
                    "        FlowButtonGroup { // Tag suggestions\n"
                    "            id: tagSuggestions\n"
                    "            visible: root.suggestionList.length > 0 && tagInputField.text.length > 0\n"
                    "            property int selectedIndex: 0\n"
                    "            Layout.fillWidth: true\n"
                    "            spacing: 5\n\n"
                    "            Repeater {\n"
                    "                id: tagSuggestionRepeater\n"
                    "                model: {\n"
                    "                    tagSuggestions.selectedIndex = 0\n"
                    "                    return root.suggestionList.slice(0, 10)\n"
                    "                }\n"
                    "                delegate: ApiCommandButton {\n"
                    "                    id: tagButton\n"
                    "                    colBackground: tagSuggestions.selectedIndex === index ? Appearance.colors.colSecondaryContainerHover : Appearance.colors.colSecondaryContainer\n"
                    "                    bounce: false\n"
                    "                    contentItem: RowLayout {\n"
                    "                        anchors.centerIn: parent\n"
                    "                        spacing: 5\n"
                    "                        StyledText {\n"
                    "                            Layout.fillWidth: false\n"
                    "                            font.pixelSize: Appearance.font.pixelSize.small\n"
                    "                            color: Appearance.colors.colOnSecondaryContainer\n"
                    "                            horizontalAlignment: Text.AlignRight\n"
                    "                            text: modelData.displayName ?? modelData.name\n"
                    "                        }\n"
                    "                        StyledText {\n"
                    "                            Layout.fillWidth: false\n"
                    "                            visible: modelData.count !== undefined\n"
                    "                            font.pixelSize: Appearance.font.pixelSize.smaller\n"
                    "                            color: Appearance.colors.colOnSecondaryContainer\n"
                    "                            horizontalAlignment: Text.AlignLeft\n"
                    "                            text: modelData.count ?? \"\"\n"
                    "                        }\n"
                    "                    }\n\n"
                    "                    onHoveredChanged: {\n"
                    "                        if (tagButton.hovered) {\n"
                    "                            tagSuggestions.selectedIndex = index;\n"
                    "                        }\n"
                    "                    }\n"
                    "                    onClicked: {\n"
                    "                        tagSuggestions.acceptTag(modelData.name)\n"
                    "                    }\n"
                    "                }\n"
                    "            }",
                    "        CliSlashList {\n"
                    "            id: tagSuggestions\n"
                    "            visible: root.suggestionList.length > 0 && tagInputField.text.length > 0\n"
                    "            Layout.fillWidth: true\n"
                    "            model: root.suggestionList\n"
                    "            onItemAccepted: item => tagSuggestions.acceptTag(item.name)",
                ),
                (
                    "const sel = tagSuggestions.currentItem();",
                    "                if (tagSuggestions.selectedIndex >= 0 && tagSuggestions.selectedIndex < tagSuggestionRepeater.count) {\n"
                    "                    const tag = root.suggestionList[tagSuggestions.selectedIndex].name;\n"
                    "                    tagSuggestions.acceptTag(tag);\n"
                    "                }",
                    "                const sel = tagSuggestions.currentItem();\n"
                    "                if (sel) tagSuggestions.acceptTag(sel.name);",
                ),
                (
                    "id: animeClickDismiss",
                    "        ScrollEdgeFade {",
                    "        MouseArea {\n"
                    "            id: animeClickDismiss\n"
                    "            anchors.fill: parent\n"
                    "            visible: root.providerPickerOpen\n"
                    "            z: 5\n"
                    "            onPressed: mouse => {\n"
                    "                root.providerPickerOpen = false;\n"
                    "                mouse.accepted = false;\n"
                    "            }\n"
                    "        }\n"
                    "        ScrollEdgeFade {",
                ),
                (
                    "id: animeProviderPicker",
                    "        Rectangle { // Tag input area",
                    "        Rectangle { // Inline Anime Provider Picker\n"
                    "            id: animeProviderPicker\n"
                    "            visible: root.providerPickerOpen\n"
                    "            Layout.fillWidth: true\n"
                    "            implicitHeight: Math.min(240, provCol.implicitHeight + 14)\n"
                    "            clip: true\n"
                    "            radius: Appearance.rounding.normal\n"
                    "            color: Appearance.colors.colLayer2\n"
                    "            border.width: 1\n"
                    "            border.color: Appearance.colors.colOutlineVariant\n\n"
                    "            ColumnLayout {\n"
                    "                id: provCol\n"
                    "                anchors.left: parent.left\n"
                    "                anchors.right: parent.right\n"
                    "                anchors.top: parent.top\n"
                    "                anchors.margins: 8\n"
                    "                spacing: 4\n"
                    "                StyledText {\n"
                    "                    Layout.leftMargin: 6\n"
                    "                    font.pixelSize: Appearance.font.pixelSize.smaller\n"
                    "                    font.weight: Font.Medium\n"
                    "                    color: Appearance.colors.colSubtext\n"
                    "                    text: Translation.tr(\"Providers\")\n"
                    "                }\n"
                    "                ListView {\n"
                    "                    id: provList\n"
                    "                    Layout.fillWidth: true\n"
                    "                    implicitHeight: Math.min(190, contentHeight)\n"
                    "                    clip: true\n"
                    "                    spacing: 2\n"
                    "                    model: Booru.providerList\n"
                    "                    delegate: RippleButton {\n"
                    "                        required property string modelData\n"
                    "                        readonly property bool active: Booru.currentProvider === modelData\n"
                    "                        width: provList.width\n"
                    "                        implicitHeight: 30\n"
                    "                        buttonRadius: Appearance.rounding.small\n"
                    "                        colBackground: active ? Appearance.colors.colPrimaryContainer : \"transparent\"\n"
                    "                        colBackgroundHover: active ? Appearance.colors.colPrimaryContainer : Appearance.colors.colSurfaceContainerHigh\n"
                    "                        onClicked: {\n"
                    "                            Booru.setProvider(modelData);\n"
                    "                            root.providerPickerOpen = false;\n"
                    "                        }\n"
                    "                        contentItem: RowLayout {\n"
                    "                            anchors.fill: parent\n"
                    "                            anchors.leftMargin: 8\n"
                    "                            anchors.rightMargin: 8\n"
                    "                            StyledText {\n"
                    "                                Layout.fillWidth: true\n"
                    "                                font.pixelSize: Appearance.font.pixelSize.small\n"
                    "                                color: active ? Appearance.colors.colOnPrimaryContainer : Appearance.m3colors.m3onSurface\n"
                    "                                text: Booru.providers[modelData]?.name ?? modelData\n"
                    "                            }\n"
                    "                            MaterialSymbol {\n"
                    "                                visible: active\n"
                    "                                text: \"check\"\n"
                    "                                iconSize: 16\n"
                    "                                color: Appearance.colors.colPrimary\n"
                    "                            }\n"
                    "                        }\n"
                    "                    }\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        Rectangle { // Tag input area",
                ),
                (
                    "onActiveFocusChanged: if (activeFocus) root.providerPickerOpen = false;",
                    "                StyledTextArea { // The actual TextArea\n"
                    "                    id: tagInputField",
                    "                StyledTextArea { // The actual TextArea\n"
                    "                    id: tagInputField\n"
                    "                    onActiveFocusChanged: if (activeFocus) root.providerPickerOpen = false;",
                ),
                (
                    "tagSuggestions.moveUp()",
                    "                        } else if (event.key === Qt.Key_Up) {\n"
                    "                            tagSuggestions.selectedIndex = Math.max(0, tagSuggestions.selectedIndex - 1);\n"
                    "                            event.accepted = true;\n"
                    "                        } else if (event.key === Qt.Key_Down) {\n"
                    "                            tagSuggestions.selectedIndex = Math.min(root.suggestionList.length - 1, tagSuggestions.selectedIndex + 1);\n"
                    "                            event.accepted = true;\n"
                    "                        }",
                    "                        } else if (event.key === Qt.Key_Up) {\n"
                    "                            tagSuggestions.moveUp();\n"
                    "                            event.accepted = true;\n"
                    "                        } else if (event.key === Qt.Key_Down) {\n"
                    "                            tagSuggestions.moveDown();\n"
                    "                            event.accepted = true;\n"
                    "                        }",
                ),
                (
                    "if (root.providerPickerOpen) { root.providerPickerOpen = false; event.accepted = true; return; }",
                    "                        } else if (event.key === Qt.Key_Up) {",
                    "                        } else if (event.key === Qt.Key_Escape) {\n"
                    "                            if (root.providerPickerOpen) { root.providerPickerOpen = false; event.accepted = true; return; }\n"
                    "                            if (tagSuggestions.visible) { tagInputField.clear(); event.accepted = true; return; }\n"
                    "                        } else if (event.key === Qt.Key_Up) {",
                ),
                (
                    'dontAddSpace: true\n                    },',
                    '                    {\n'
                    '                        name: "mode",\n'
                    '                        sendDirectly: false,\n'
                    '                    },',
                    '                    {\n'
                    '                        name: "",\n'
                    '                        sendDirectly: false,\n'
                    '                        dontAddSpace: true\n'
                    '                    },',
                ),
                (
                    "enter sends selected",
                    "                        } else if ((event.key === Qt.Key_Enter || event.key === Qt.Key_Return)) {\n"
                    "                            if (event.modifiers & Qt.ShiftModifier) {\n"
                    "                                // Insert newline\n"
                    "                                tagInputField.insert(tagInputField.cursorPosition, \"\\n\")\n"
                    "                                event.accepted = true\n"
                    "                            } else { // Accept text\n"
                    "                                const inputText = tagInputField.text\n"
                    "                                root.handleInput(inputText)\n"
                    "                                tagInputField.clear()\n"
                    "                                event.accepted = true\n"
                    "                            }\n"
                    "                        }",
                    "                        } else if ((event.key === Qt.Key_Enter || event.key === Qt.Key_Return)) {\n"
                    "                            if (event.modifiers & Qt.ShiftModifier) {\n"
                    "                                // Insert newline\n"
                    "                                tagInputField.insert(tagInputField.cursorPosition, \"\\n\")\n"
                    "                                event.accepted = true\n"
                    "                            } else if (tagSuggestions.visible) { // enter sends selected\n"
                    "                                tagSuggestions.acceptSelectedTag();\n"
                    "                                const inputText = tagInputField.text.trim();\n"
                    "                                if (inputText.length > 0) root.handleInput(inputText);\n"
                    "                                tagInputField.clear();\n"
                    "                                event.accepted = true;\n"
                    "                            } else { // Accept text\n"
                    "                                const inputText = tagInputField.text\n"
                    "                                root.handleInput(inputText)\n"
                    "                                tagInputField.clear()\n"
                    "                                event.accepted = true\n"
                    "                            }\n"
                    "                        }",
                ),
                (
                    "root.suggestionList = []; // clear after accept",
                    "                const updatedText = words.join(\" \") + \" \";\n"
                    "                tagInputField.text = updatedText;\n"
                    "                tagInputField.cursorPosition = tagInputField.text.length;\n"
                    "                tagInputField.forceActiveFocus();",
                    "                const updatedText = words.join(\" \") + \" \";\n"
                    "                tagInputField.text = updatedText;\n"
                    "                root.suggestionList = []; // clear after accept\n"
                    "                tagInputField.cursorPosition = tagInputField.text.length;\n"
                    "                tagInputField.forceActiveFocus();",
                ),
                (
                    "root.providerPickerOpen = !root.providerPickerOpen",
                    '                ApiInputBoxIndicator { // Tool indicator\n'
                    '                    icon: "api"\n'
                    '                    text: Booru.providers[Booru.currentProvider].name\n'
                    '                    tooltipText: Translation.tr("Current API endpoint: %1\\nSet it with %2mode PROVIDER")\n'
                    '                        .arg(Booru.providers[Booru.currentProvider].url)\n'
                    '                        .arg(root.commandPrefix)\n'
                    '                }',
                    '                ApiInputBoxIndicator { // Tool indicator (clickable)\n'
                    '                    icon: "api"\n'
                    '                    text: Booru.providers[Booru.currentProvider].name\n'
                    '                    tooltipText: Translation.tr("Current API endpoint: %1\\nSet it with %2mode PROVIDER")\n'
                    '                        .arg(Booru.providers[Booru.currentProvider].url)\n'
                    '                        .arg(root.commandPrefix)\n'
                    '                    MouseArea {\n'
                    '                        z: 10\n'
                    '                        anchors.fill: parent\n'
                    '                        cursorShape: Qt.PointingHandCursor\n'
                    '                        onClicked: root.providerPickerOpen = !root.providerPickerOpen\n'
                    '                    }\n'
                    '                }',
                ),
            ],
        )

        # 7. BooruImage.qml: clicking an anime image opens a floating full-size viewer
        ok &= patch_file(
            ii / "modules/ii/sidebarLeft/anime/BooruImage.qml",
            [
                (
                    "property bool viewerOpen: false",
                    "    property bool showActions: false",
                    "    property bool showActions: false\n"
                    "    property bool viewerOpen: false",
                ),
                (
                    "sampleUrl: root.imageData.sample_url",
                    "    padding: 0\n"
                    "    implicitWidth: root.rowHeight * modelData.aspect_ratio",
                    "    onClicked: root.viewerOpen = true\n\n"
                    "    PointingHandInteraction {}\n\n"
                    "    Loader {\n"
                    "        active: root.viewerOpen\n"
                    "        sourceComponent: AnimeImageViewer {\n"
                    "            sourceUrl: root.imageData.file_url ?? root.imageData.sample_url ?? root.imageData.preview_url ?? \"\"\n"
                    "            sampleUrl: root.imageData.sample_url ?? \"\"\n"
                    "            previewUrl: root.imageData.preview_url ?? \"\"\n"
                    "            tags: root.imageData.tags ?? \"\"\n"
                    "            onCloseRequested: root.viewerOpen = false\n"
                    "        }\n"
                    "    }\n\n"
                    "    padding: 0\n"
                    "    implicitWidth: root.rowHeight * modelData.aspect_ratio",
                ),
            ],
        )

        # 8. GlobalStates.qml: track animeViewerOpen so SidebarLeft ignores Esc/focus-grab while viewing
        ok &= patch_file(
            ii / "GlobalStates.qml",
            [
                (
                    "property bool animeViewerOpen: false",
                    "    property bool sidebarLeftOpen: false",
                    "    property bool sidebarLeftOpen: false\n"
                    "    property bool animeViewerOpen: false",
                ),
            ],
        )

        # 9. SidebarLeft.qml: don't dismiss SidebarLeft when AnimeImageViewer takes focus or Esc is pressed
        ok &= patch_file(
            ii / "modules/ii/sidebarLeft/SidebarLeft.qml",
            [
                (
                    "if (!GlobalStates.animeViewerOpen) panelWindow.hide();",
                    "            Connections {\n"
                    "                target: GlobalFocusGrab\n"
                    "                function onDismissed() {\n"
                    "                    panelWindow.hide();\n"
                    "                }\n"
                    "            }",
                    "            Connections {\n"
                    "                target: GlobalFocusGrab\n"
                    "                function onDismissed() {\n"
                    "                    if (!GlobalStates.animeViewerOpen) panelWindow.hide();\n"
                    "                }\n"
                    "            }\n"
                    "            Connections {\n"
                    "                target: GlobalStates\n"
                    "                function onAnimeViewerOpenChanged() {\n"
                    "                    if (!GlobalStates.animeViewerOpen && panelWindow.visible) {\n"
                    "                        GlobalFocusGrab.addDismissable(panelWindow);\n"
                    "                    }\n"
                    "                }\n"
                    "            }",
                ),
                (
                    "if (event.key === Qt.Key_Escape && !GlobalStates.animeViewerOpen)",
                    "                Keys.onPressed: (event) => {\n"
                    "                    if (event.key === Qt.Key_Escape) {\n"
                    "                        panelWindow.hide();\n"
                    "                    }",
                    "                Keys.onPressed: (event) => {\n"
                    "                    if (event.key === Qt.Key_Escape && !GlobalStates.animeViewerOpen) {\n"
                    "                        panelWindow.hide();\n"
                    "                    }",
                ),
            ],
        )

    if has_feat("workspace-split"):
        # 10. Config.qml: store splitByMonitor, leftMonitorCount & monitorSplits (M-1 boundaries for M monitors)
        ok &= patch_file(
            ii / "modules/common/Config.qml",
            [
                (
                    "property string defaultMonitor:",
                    "                property JsonObject workspaces: JsonObject {\n"
                    "                    property bool monochromeIcons: true",
                    "                property JsonObject workspaces: JsonObject {\n"
                    "                    property bool splitByMonitor: true\n"
                    "                    property int leftMonitorCount: 5\n"
                    "                    property list<int> monitorSplits: [5]\n"
                    "                    property string defaultMonitor: \"\"\n"
                    "                    property bool monochromeIcons: true",
                ),
            ],
        )

        # 11. BarConfig.qml: On/Off switch + M-1 live sliders for M monitors
        ok &= patch_file(
            ii / "modules/settings/BarConfig.qml",
            [
                (
                    "import Quickshell.Io",
                    "import QtQuick\n"
                    "import QtQuick.Layouts\n"
                    "import qs.services",
                    "import QtQuick\n"
                    "import QtQuick.Layouts\n"
                    "import Quickshell\n"
                    "import Quickshell.Io\n"
                    "import qs.services",
                ),
                (
                    "function getMonitorSplits()",
                    "ContentPage {\n"
                    "    forceWidth: true",
                    "ContentPage {\n"
                    "    id: barConfigPage\n"
                    "    forceWidth: true\n"
                    "    readonly property int monitorCount: Quickshell.screens.length\n"
                    "    readonly property bool hasMultipleMonitors: monitorCount > 1\n\n"
                    "    function getMonitorSplits() {\n"
                    "        const needed = Math.max(0, monitorCount - 1);\n"
                    "        if (needed === 0) return [];\n"
                    "        let arr = Array.from(Config.options.bar.workspaces.monitorSplits ?? []);\n"
                    "        if (arr.length !== needed) {\n"
                    "            arr = [];\n"
                    "            for (let i = 0; i < needed; i++) {\n"
                    "                arr.push(Math.round(10 * (i + 1) / monitorCount));\n"
                    "            }\n"
                    "        }\n"
                    "        return arr;\n"
                    "    }\n\n"
                    "    function updateSplit(idx, val) {\n"
                    "        const needed = Math.max(0, monitorCount - 1);\n"
                    "        if (idx < 0 || idx >= needed) return;\n"
                    "        const arr = getMonitorSplits().slice();\n"
                    "        const minV = idx + 1;\n"
                    "        const maxV = 10 - (needed - idx);\n"
                    "        arr[idx] = Math.max(minV, Math.min(maxV, Math.round(val)));\n"
                    "        for (let j = idx - 1; j >= 0; j--) {\n"
                    "            if (arr[j] >= arr[j + 1]) arr[j] = arr[j + 1] - 1;\n"
                    "        }\n"
                    "        for (let j = idx + 1; j < needed; j++) {\n"
                    "            if (arr[j] <= arr[j - 1]) arr[j] = arr[j - 1] + 1;\n"
                    "        }\n"
                    "        Config.options.bar.workspaces.monitorSplits = arr;\n"
                    "        Config.options.bar.workspaces.leftMonitorCount = arr[0];\n"
                    "        wsSplitApplyTimer.restart();\n"
                    "    }\n\n"
                    "    Timer {\n"
                    "        id: wsSplitApplyTimer\n"
                    "        interval: 120\n"
                    "        repeat: false\n"
                    "        onTriggered: {\n"
                    "            wsSplitProc.running = false;\n"
                    "            wsSplitProc.running = true;\n"
                    "        }\n"
                    "    }\n\n"
                    "    Process {\n"
                    "        id: wsSplitProc\n"
                    "        command: [\n"
                    "            \"python3\",\n"
                    "            Quickshell.shellPath(\"scripts/apply-workspace-split.py\"),\n"
                    "            (barConfigPage.hasMultipleMonitors && Config.options.bar.workspaces.splitByMonitor)\n"
                    "                ? barConfigPage.getMonitorSplits().join(\",\")\n"
                    "                : \"0\"\n"
                    "        ]\n"
                    "    }",
                ),
                (
                    "Split workspaces by monitor",
                    "        ConfigSpinBox {\n"
                    "            icon: \"view_column\"\n"
                    "            text: Translation.tr(\"Workspaces shown\")",
                    "        RowLayout {\n"
                    "            Layout.fillWidth: true\n"
                    "            spacing: 8\n"
                    "            ConfigSwitch {\n"
                    "                Layout.fillWidth: true\n"
                    "                buttonIcon: \"splitscreen_left\"\n"
                    "                text: Translation.tr(\"Split workspaces by monitor\")\n"
                    "                enabled: barConfigPage.hasMultipleMonitors\n"
                    "                checked: barConfigPage.hasMultipleMonitors && Config.options.bar.workspaces.splitByMonitor\n"
                    "                onCheckedChanged: {\n"
                    "                    if (barConfigPage.hasMultipleMonitors && Config.options.bar.workspaces.splitByMonitor !== checked) {\n"
                    "                        Config.options.bar.workspaces.splitByMonitor = checked;\n"
                    "                        wsSplitApplyTimer.restart();\n"
                    "                    }\n"
                    "                }\n"
                    "            }\n"
                    "            RowLayout {\n"
                    "                visible: !barConfigPage.hasMultipleMonitors\n"
                    "                spacing: 4\n"
                    "                MaterialSymbol {\n"
                    "                    text: \"error\"\n"
                    "                    iconSize: 18\n"
                    "                    color: Appearance.colors.colError\n"
                    "                }\n"
                    "                StyledText {\n"
                    "                    text: Translation.tr(\"No 2nd monitor\")\n"
                    "                    color: Appearance.colors.colError\n"
                    "                    font.pixelSize: Appearance.font.pixelSize.small\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        Repeater {\n"
                    "            model: (barConfigPage.hasMultipleMonitors && Config.options.bar.workspaces.splitByMonitor)\n"
                    "                ? Math.max(0, barConfigPage.monitorCount - 1) : 0\n"
                    "            delegate: ConfigSlider {\n"
                    "                required property int index\n"
                    "                readonly property var splits: barConfigPage.getMonitorSplits()\n"
                    "                readonly property int prevEnd: index === 0 ? 0 : splits[index - 1]\n"
                    "                readonly property int curEnd: splits[index] ?? 5\n"
                    "                readonly property int nextEnd: (index + 1 < splits.length) ? splits[index + 1] : 10\n"
                    "                text: Translation.tr(\"M%1 %2–%3 | M%4 %5–%6\")\n"
                    "                    .arg(index + 1).arg(prevEnd + 1).arg(curEnd)\n"
                    "                    .arg(index + 2).arg(curEnd + 1).arg(nextEnd)\n"
                    "                value: curEnd\n"
                    "                usePercentTooltip: false\n"
                    "                buttonIcon: \"tune\"\n"
                    "                from: index + 1\n"
                    "                to: 10 - (barConfigPage.monitorCount - 1 - index)\n"
                    "                stopIndicatorValues: [Math.round(10 * (index + 1) / barConfigPage.monitorCount)]\n"
                    "                onValueChanged: {\n"
                    "                    const v = Math.round(value);\n"
                    "                    if (v !== curEnd) {\n"
                    "                        barConfigPage.updateSplit(index, v);\n"
                    "                    }\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        ContentSubsection {\n"
                    "            visible: barConfigPage.hasMultipleMonitors\n"
                    "            title: Translation.tr(\"Default monitor on startup\")\n"
                    "            ConfigSelectionArray {\n"
                    "                currentValue: Config.options.bar.workspaces.defaultMonitor ?? \"\"\n"
                    "                onSelected: newValue => Config.options.bar.workspaces.defaultMonitor = newValue\n"
                    "                options: [({ displayName: Translation.tr(\"Auto (Largest)\"), icon: \"auto_awesome\", value: \"\" })].concat(\n"
                    "                    Quickshell.screens.map((s, idx) => ({\n"
                    "                        displayName: \"%1 · %2\".arg(idx + 1).arg(s.name),\n"
                    "                        icon: \"desktop_windows\",\n"
                    "                        value: s.name\n"
                    "                    }))\n"
                    "                )\n"
                    "            }\n"
                    "        }\n\n"
                    "        ConfigSpinBox {\n"
                    "            icon: \"view_column\"\n"
                    "            text: Translation.tr(\"Workspaces shown\")",
                ),
            ],
        )

    if has_feat("icon-cache"):
        # 12. AppSearch.qml: map zen/dolphin/artcraft window classes -> desktop icon names
        ok &= patch_file(
            ii / "services/AppSearch.qml",
            [
                (
                    '"dolphin": "org.kde.dolphin"',
                    '        "footclient": "foot",\n    })',
                    '        "footclient": "foot",\n'
                    '        "zen": "zen-browser",\n'
                    '        "dolphin": "org.kde.dolphin",\n'
                    '        "artcraft-launcher": "ai.storyteller.artcraft-launcher",\n'
                    '        "artcraft": "ai.storyteller.artcraft-launcher",\n    })',
                    "optional",
                ),
                (
                    '"dolphin": "org.kde.dolphin"',
                    '        "footclient": "foot",\n        "zen": "zen-browser",',
                    '        "footclient": "foot",\n'
                    '        "zen": "zen-browser",\n'
                    '        "dolphin": "org.kde.dolphin",\n'
                    '        "artcraft-launcher": "ai.storyteller.artcraft-launcher",\n'
                    '        "artcraft": "ai.storyteller.artcraft-launcher",',
                    "optional",
                ),
            ],
        )

    if has_feat("ai-sidebar"):
        # 13. GoogleCloud.qml: don't trigger keyring password popup on boot before LockScreen unlocks keyring
        ok &= patch_file(
            ii / "services/GoogleCloud.qml",
            [
                (
                    "if (!Config.options.lock.launchOnStartup) KeyringStorage.fetchKeyringData();",
                    "        } else {\n"
                    "            KeyringStorage.fetchKeyringData();\n"
                    "        }",
                    "        } else {\n"
                    "            if (!Config.options.lock.launchOnStartup) KeyringStorage.fetchKeyringData();\n"
                    "        }",
                ),
            ],
        )

    if has_feat("screensaver") or has_feat("lock-power"):
        # 14. Config.qml: screensaver options
        ok &= patch_file(
            ii / "modules/common/Config.qml",
            [
                (
                    "property JsonObject screensaver:",
                    "            property JsonObject lock: JsonObject {",
                    "            property JsonObject screensaver: JsonObject {\n"
                    "                property bool enable: false\n"
                    "                property int timeoutMinutes: 3\n"
                    "                property bool perMonitor: false\n"
                    "                property var monitors: ({})\n"
                    "                property string mode: \"dvd\"\n"
                    "                property string color: \"#000000\"\n"
                    "                property string customPath: \"\"\n"
                    "                property var customItems: []\n"
                    "                property string imageAnimation: \"breathe\"\n"
                    "                property real speed: 1.0\n"
                    "            }\n\n"
                    "            property JsonObject lock: JsonObject {\n"
                    "                property JsonObject idle: JsonObject {\n"
                    "                    property bool enableLock: true\n"
                    "                    property int lockMinutes: 5\n"
                    "                    property bool enableDpms: true\n"
                    "                    property int dpmsMinutes: 10\n"
                    "                    property bool enableSuspend: false\n"
                    "                    property int suspendMinutes: 15\n"
                    "                }",
                ),
            ],
        )

    if has_feat("screensaver"):
        # 15. settings.qml: register Screensaver page in left navigation
        ok &= patch_file(
            ii / "settings.qml",
            [
                (
                    "ScreensaverConfig.qml",
                    '        {\n'
                    '            name: Translation.tr("Background"),\n'
                    '            icon: "texture",\n'
                    '            component: "modules/settings/BackgroundConfig.qml"\n'
                    '        },',
                    '        {\n'
                    '            name: Translation.tr("Background"),\n'
                    '            icon: "texture",\n'
                    '            component: "modules/settings/BackgroundConfig.qml"\n'
                    '        },\n'
                    '        {\n'
                    '            name: Translation.tr("Screensaver"),\n'
                    '            icon: "tv",\n'
                    '            component: "modules/settings/ScreensaverConfig.qml"\n'
                    '        },',
                ),
            ],
        )

        # 16. shell.qml: mount global ScreensaverOverlay + IPC handler
        ok &= patch_file(
            ii / "shell.qml",
            [
                (
                    '"modules/ii/screensaver"',
                    'import "modules/common"\n',
                    'import "modules/common"\nimport "modules/ii/screensaver"\n',
                ),
                (
                    "ScreensaverOverlay {}",
                    "    ReloadPopup {}\n",
                    "    ReloadPopup {}\n    ScreensaverOverlay {}\n",
                ),
            ],
        )

    if has_feat("lock-power"):
        # 17. GeneralConfig.qml: Lock section (Lock, DPMS, Suspend toggles + timeouts + Plymouth boot logo picker)
        ok &= patch_file(
            ii / "modules/settings/GeneralConfig.qml",
            [
                (
                    "import QtQuick.Dialogs",
                    "import QtQuick\n"
                    "import Quickshell",
                    "import QtQuick\n"
                    "import QtQuick.Dialogs\n"
                    "import Quickshell",
                ),
                (
                    "property bool plymouthXanaInstalled:",
                    "ContentPage {\n"
                    "    forceWidth: true",
                    "ContentPage {\n"
                    "    id: generalPage\n"
                    "    forceWidth: true\n"
                    "    property bool plymouthXanaInstalled: false\n\n"
                    "    Timer {\n"
                    "        id: generalIdleTimer\n"
                    "        interval: 200\n"
                    "        repeat: false\n"
                    "        onTriggered: {\n"
                    "            generalIdleProc.running = false;\n"
                    "            generalIdleProc.running = true;\n"
                    "        }\n"
                    "    }\n\n"
                    "    Process {\n"
                    "        id: generalIdleProc\n"
                    "        command: [\"python3\", Quickshell.shellPath(\"scripts/apply-screensaver-idle.py\")]\n"
                    "    }\n\n"
                    "    Process {\n"
                    "        id: plymouthCheckProc\n"
                    "        running: true\n"
                    "        command: [\"bash\", \"-c\", \"[ -f /usr/share/plymouth/themes/xana/xana.plymouth ] && echo 1 || echo 0\"]\n"
                    "        stdout: StdioCollector {\n"
                    "            onStreamFinished: generalPage.plymouthXanaInstalled = (text.trim() === \"1\")\n"
                    "        }\n"
                    "    }\n\n"
                    "    FileDialog {\n"
                    "        id: plymouthLogoPicker\n"
                    "        title: Translation.tr(\"Select boot splash logo\")\n"
                    "        nameFilters: [\"Images & Vector (*.png *.svg *.jpg *.jpeg *.webp *.pdf)\", \"All files (*)\"]\n"
                    "        onAccepted: {\n"
                    "            const p = selectedFile.toString().replace(/^file:\\/\\//, \"\");\n"
                    "            const script = Quickshell.shellPath(\"scripts/apply-plymouth-logo.sh\");\n"
                    "            Quickshell.execDetached([\"bash\", \"-c\", `${Config.options.apps.terminal} -e bash -c '\"${0}\" \"${1}\"; echo; read -p \"Press Enter to close...\"' \"${script}\" \"${p}\"`]);\n"
                    "        }\n"
                    "    }",
                ),
                (
                    'title: Translation.tr("Lock")',
                    "            onCheckedChanged: {\n"
                    "                Config.options.workSafety.enable.wallpaper = checked;\n"
                    "            }\n"
                    "        }\n"
                    "    }\n"
                    "}",
                    "            onCheckedChanged: {\n"
                    "                Config.options.workSafety.enable.wallpaper = checked;\n"
                    "            }\n"
                    "        }\n"
                    "    }\n\n"
                    "    ContentSection {\n"
                    "        icon: \"lock\"\n"
                    "        title: Translation.tr(\"Lock\")\n\n"
                    "        ConfigSwitch {\n"
                    "            buttonIcon: \"lock_clock\"\n"
                    "            text: Translation.tr(\"Lock screen on idle\")\n"
                    "            checked: Config.options.lock.idle.enableLock\n"
                    "            onCheckedChanged: {\n"
                    "                if (Config.options.lock.idle.enableLock !== checked) {\n"
                    "                    Config.options.lock.idle.enableLock = checked;\n"
                    "                    generalIdleTimer.restart();\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        ConfigSpinBox {\n"
                    "            visible: Config.options.lock.idle.enableLock\n"
                    "            icon: \"timer\"\n"
                    "            text: Translation.tr(\"Lock timeout (minutes)\")\n"
                    "            value: Config.options.lock.idle.lockMinutes\n"
                    "            from: 1\n"
                    "            to: 120\n"
                    "            stepSize: 1\n"
                    "            onValueChanged: {\n"
                    "                if (Config.options.lock.idle.lockMinutes !== value) {\n"
                    "                    Config.options.lock.idle.lockMinutes = value;\n"
                    "                    generalIdleTimer.restart();\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        ConfigSwitch {\n"
                    "            buttonIcon: \"monitor\"\n"
                    "            text: Translation.tr(\"Turn off display (DPMS)\")\n"
                    "            checked: Config.options.lock.idle.enableDpms\n"
                    "            onCheckedChanged: {\n"
                    "                if (Config.options.lock.idle.enableDpms !== checked) {\n"
                    "                    Config.options.lock.idle.enableDpms = checked;\n"
                    "                    generalIdleTimer.restart();\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        ConfigSpinBox {\n"
                    "            visible: Config.options.lock.idle.enableDpms\n"
                    "            icon: \"timer\"\n"
                    "            text: Translation.tr(\"Display off timeout (minutes)\")\n"
                    "            value: Config.options.lock.idle.dpmsMinutes\n"
                    "            from: 1\n"
                    "            to: 180\n"
                    "            stepSize: 1\n"
                    "            onValueChanged: {\n"
                    "                if (Config.options.lock.idle.dpmsMinutes !== value) {\n"
                    "                    Config.options.lock.idle.dpmsMinutes = value;\n"
                    "                    generalIdleTimer.restart();\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        ConfigSwitch {\n"
                    "            buttonIcon: \"bedtime\"\n"
                    "            text: Translation.tr(\"Deep sleep (Suspend)\")\n"
                    "            checked: Config.options.lock.idle.enableSuspend\n"
                    "            onCheckedChanged: {\n"
                    "                if (Config.options.lock.idle.enableSuspend !== checked) {\n"
                    "                    Config.options.lock.idle.enableSuspend = checked;\n"
                    "                    generalIdleTimer.restart();\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        ConfigSpinBox {\n"
                    "            visible: Config.options.lock.idle.enableSuspend\n"
                    "            icon: \"timer\"\n"
                    "            text: Translation.tr(\"Suspend timeout (minutes)\")\n"
                    "            value: Config.options.lock.idle.suspendMinutes\n"
                    "            from: 5\n"
                    "            to: 360\n"
                    "            stepSize: 5\n"
                    "            onValueChanged: {\n"
                    "                if (Config.options.lock.idle.suspendMinutes !== value) {\n"
                    "                    Config.options.lock.idle.suspendMinutes = value;\n"
                    "                    generalIdleTimer.restart();\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        RowLayout {\n"
                    "            visible: generalPage.plymouthXanaInstalled\n"
                    "            Layout.fillWidth: true\n"
                    "            spacing: 8\n"
                    "            MaterialSymbol {\n"
                    "                text: \"image\"\n"
                    "                iconSize: 20\n"
                    "                color: Appearance.m3colors.m3onSurface\n"
                    "            }\n"
                    "            StyledText {\n"
                    "                Layout.fillWidth: true\n"
                    "                text: Translation.tr(\"Boot splash logo (Plymouth)\")\n"
                    "                color: Appearance.m3colors.m3onSurface\n"
                    "                font.pixelSize: Appearance.font.pixelSize.small\n"
                    "            }\n"
                    "            RippleButton {\n"
                    "                implicitWidth: plymouthBtnTxt.implicitWidth + 24\n"
                    "                implicitHeight: 34\n"
                    "                buttonRadius: Appearance.rounding.full\n"
                    "                colBackground: Appearance.colors.colSecondaryContainer\n"
                    "                onClicked: plymouthLogoPicker.open()\n"
                    "                contentItem: StyledText {\n"
                    "                    id: plymouthBtnTxt\n"
                    "                    anchors.centerIn: parent\n"
                    "                    text: Translation.tr(\"Choose File\")\n"
                    "                    color: Appearance.colors.colOnSecondaryContainer\n"
                    "                    font.pixelSize: Appearance.font.pixelSize.small\n"
                    "                    font.weight: Font.Medium\n"
                    "                }\n"
                    "            }\n"
                    "        }\n"
                    "    }\n"
                    "}",
                ),
            ],
        )

    if has_feat("workspace-split"):
        # 18. Workspaces.qml: dim active workspace indicator on unfocused monitors
        ok &= patch_file(
            ii / "modules/ii/bar/Workspaces.qml",
            [
                (
                    "monitorIsFocused",
                    "    readonly property HyprlandMonitor monitor: Hyprland.monitorFor(root.QsWindow.window?.screen)",
                    "    readonly property HyprlandMonitor monitor: Hyprland.monitorFor(root.QsWindow.window?.screen)\n"
                    "    readonly property bool monitorIsFocused: (Hyprland.focusedMonitor?.id == monitor?.id)",
                ),
                (
                    "root.monitorIsFocused ? Appearance.colors.colPrimary",
                    "        TrailingIndicator {\n"
                    "            id: activeIndicator\n"
                    "            anchors.fill: parent\n"
                    "            z: 2\n\n"
                    "            index: root.workspaceIndexInGroup\n"
                    "        }",
                    "        TrailingIndicator {\n"
                    "            id: activeIndicator\n"
                    "            anchors.fill: parent\n"
                    "            z: 2\n\n"
                    "            index: root.workspaceIndexInGroup\n"
                    "            color: root.monitorIsFocused ? Appearance.colors.colPrimary : ColorUtils.transparentize(Appearance.colors.colSecondary, 0.55)\n"
                    "        }",
                ),
                (
                    "Behavior on color { ColorAnimation",
                    "            contentLayer: StyledRectangle.ContentLayer.Group\n"
                    "            radius: indicatorThickness / 2\n"
                    "            color: Appearance.colors.colPrimary",
                    "            contentLayer: StyledRectangle.ContentLayer.Group\n"
                    "            radius: indicatorThickness / 2\n"
                    "            color: Appearance.colors.colPrimary\n"
                    "            Behavior on color { ColorAnimation { duration: 150 } }",
                ),
            ],
        )

    if has_feat("startup-apps"):
        # 19. GeneralConfig.qml: Startup Apps grid below Language
        ok &= patch_file(
            ii / "modules/settings/GeneralConfig.qml",
            [
                (
                    "import QtQuick.Controls",
                    "import QtQuick\n",
                    "import QtQuick\nimport QtQuick.Controls\n",
                ),
                (
                    "property var startupApps:",
                    "ContentPage {\n"
                    "    id: generalPage\n"
                    "    forceWidth: true\n",
                    "ContentPage {\n"
                    "    id: generalPage\n"
                    "    forceWidth: true\n"
                    "    property var startupApps: []\n"
                    "    property var installedApps: []\n"
                    "    property string pickedStartupIcon: \"\"\n"
                    "    property bool startupGridMode: true\n"
                    "    property string startupSortBy: \"status\"\n"
                    "    property bool startupSortAsc: false\n\n"
                    "    readonly property var sortedStartupApps: {\n"
                    "        const arr = (generalPage.startupApps || []).slice();\n"
                    "        const dir = generalPage.startupSortAsc ? 1 : -1;\n"
                    "        arr.sort((a, b) => {\n"
                    "            if (generalPage.startupSortBy === \"name\") {\n"
                    "                return a.name.localeCompare(b.name) * (generalPage.startupSortAsc ? -1 : 1);\n"
                    "            }\n"
                    "            if (generalPage.startupSortBy === \"date\") {\n"
                    "                return ((a.mtime ?? 0) - (b.mtime ?? 0)) * dir;\n"
                    "            }\n"
                    "            if (a.enabled !== b.enabled) return (a.enabled ? 1 : -1) * dir;\n"
                    "            return a.name.localeCompare(b.name);\n"
                    "        });\n"
                    "        return arr;\n"
                    "    }\n\n"
                    "    function refreshStartupApps() {\n"
                    "        startupListProc.running = false;\n"
                    "        startupListProc.running = true;\n"
                    "    }\n\n"
                    "    Process {\n"
                    "        id: startupListProc\n"
                    "        command: [\"python3\", Quickshell.shellPath(\"scripts/startup-apps.py\"), \"list\"]\n"
                    "        running: true\n"
                    "        stdout: StdioCollector {\n"
                    "            onStreamFinished: {\n"
                    "                try {\n"
                    "                    generalPage.startupApps = JSON.parse(text);\n"
                    "                } catch (e) {}\n"
                    "            }\n"
                    "        }\n"
                    "    }\n\n"
                    "    Process {\n"
                    "        id: installedAppsProc\n"
                    "        command: [\"python3\", Quickshell.shellPath(\"scripts/startup-apps.py\"), \"apps\"]\n"
                    "        running: true\n"
                    "        stdout: StdioCollector {\n"
                    "            onStreamFinished: {\n"
                    "                try {\n"
                    "                    generalPage.installedApps = JSON.parse(text);\n"
                    "                } catch (e) {}\n"
                    "            }\n"
                    "        }\n"
                    "    }\n\n"
                    "    Process {\n"
                    "        id: startupActionProc\n"
                    "        onExited: generalPage.refreshStartupApps()\n"
                    "    }\n",
                ),
                (
                    'title: Translation.tr("Startup Apps")',
                    "                        translationProc.running = true;\n"
                    "                    }\n"
                    "                }\n"
                    "            }\n"
                    "        }\n"
                    "    }\n\n"
                    "    ContentSection {\n"
                    "        icon: \"rule\"\n"
                    "        title: Translation.tr(\"Policies\")",
                    "                        translationProc.running = true;\n"
                    "                    }\n"
                    "                }\n"
                    "            }\n"
                    "        }\n"
                    "    }\n\n"
                    "    ContentSection {\n"
                    "        icon: \"rocket_launch\"\n"
                    "        title: Translation.tr(\"Startup Apps\")\n\n"
                    "        RowLayout {\n"
                    "            Layout.fillWidth: true\n"
                    "            spacing: 8\n\n"
                    "            RippleButton {\n"
                    "                id: installedAppBtn\n"
                    "                Layout.fillWidth: true\n"
                    "                implicitHeight: 40\n"
                    "                buttonRadius: Appearance.rounding.normal\n"
                    "                colBackground: Appearance.colors.colLayer2\n"
                    "                colBackgroundHover: Appearance.colors.colSurfaceContainerHigh\n"
                    "                onClicked: installedAppPopup.opened ? installedAppPopup.close() : installedAppPopup.open()\n"
                    "                contentItem: RowLayout {\n"
                    "                    anchors.fill: parent\n"
                    "                    anchors.leftMargin: 12\n"
                    "                    anchors.rightMargin: 12\n"
                    "                    spacing: 8\n"
                    "                    MaterialSymbol {\n"
                    "                        text: \"apps\"\n"
                    "                        iconSize: 18\n"
                    "                        color: Appearance.m3colors.m3onSurface\n"
                    "                    }\n"
                    "                    StyledText {\n"
                    "                        Layout.fillWidth: true\n"
                    "                        text: Translation.tr(\"Select installed app...\")\n"
                    "                        color: Appearance.m3colors.m3onSurface\n"
                    "                        font.pixelSize: Appearance.font.pixelSize.small\n"
                    "                    }\n"
                    "                    MaterialSymbol {\n"
                    "                        text: installedAppPopup.opened ? \"expand_less\" : \"expand_more\"\n"
                    "                        iconSize: 20\n"
                    "                        color: Appearance.colors.colSubtext\n"
                    "                    }\n"
                    "                }\n\n"
                    "                Popup {\n"
                    "                    id: installedAppPopup\n"
                    "                    y: installedAppBtn.height + 6\n"
                    "                    width: installedAppBtn.width\n"
                    "                    height: Math.min(260, Math.max(96, installedAppsGrid.implicitHeight + 20))\n"
                    "                    padding: 10\n"
                    "                    modal: false\n"
                    "                    focus: true\n"
                    "                    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent\n\n"
                    "                    background: Rectangle {\n"
                    "                        radius: Appearance.rounding.normal\n"
                    "                        color: Qt.rgba(Appearance.m3colors.m3surfaceContainerLow.r, Appearance.m3colors.m3surfaceContainerLow.g, Appearance.m3colors.m3surfaceContainerLow.b, 1.0)\n"
                    "                        border.width: 1\n"
                    "                        border.color: Appearance.colors.colOutlineVariant\n"
                    "                    }\n\n"
                    "                    contentItem: Flickable {\n"
                    "                        id: installedAppsScroll\n"
                    "                        clip: true\n"
                    "                        contentWidth: width\n"
                    "                        contentHeight: installedAppsGrid.implicitHeight\n"
                    "                        boundsBehavior: Flickable.StopAtBounds\n"
                    "                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }\n\n"
                    "                        GridLayout {\n"
                    "                            id: installedAppsGrid\n"
                    "                            width: installedAppsScroll.width\n"
                    "                            columnSpacing: 8\n"
                    "                            rowSpacing: 8\n"
                    "                            columns: 2\n\n"
                    "                            Repeater {\n"
                    "                                model: generalPage.installedApps\n"
                    "                                delegate: Rectangle {\n"
                    "                                    required property var modelData\n"
                    "                                    Layout.fillWidth: true\n"
                    "                                    implicitHeight: 42\n"
                    "                                    radius: Appearance.rounding.normal\n"
                    "                                    color: pickArea.containsMouse ? Appearance.colors.colSurfaceContainerHigh : Appearance.colors.colLayer2\n"
                    "                                    border.width: 1\n"
                    "                                    border.color: Appearance.colors.colOutlineVariant\n\n"
                    "                                    MouseArea {\n"
                    "                                        id: pickArea\n"
                    "                                        anchors.fill: parent\n"
                    "                                        hoverEnabled: true\n"
                    "                                        cursorShape: Qt.PointingHandCursor\n"
                    "                                        onClicked: {\n"
                    "                                            startupNameInput.text = modelData.displayName;\n"
                    "                                            startupCmdInput.text = modelData.exec;\n"
                    "                                            generalPage.pickedStartupIcon = modelData.icon || \"\";\n"
                    "                                            installedAppPopup.close();\n"
                    "                                        }\n"
                    "                                    }\n\n"
                    "                                    RowLayout {\n"
                    "                                        anchors.fill: parent\n"
                    "                                        anchors.leftMargin: 10\n"
                    "                                        anchors.rightMargin: 10\n"
                    "                                        spacing: 8\n"
                    "                                        Image {\n"
                    "                                            width: 20\n"
                    "                                            height: 20\n"
                    "                                            sourceSize: Qt.size(20, 20)\n"
                    "                                            source: {\n"
                    "                                                const ic = modelData.icon || \"application-x-executable\";\n"
                    "                                                if (ic.startsWith(\"/\")) return \"file://\" + ic;\n"
                    "                                                return Quickshell.iconPath(ic, \"application-x-executable\");\n"
                    "                                            }\n"
                    "                                            fillMode: Image.PreserveAspectFit\n"
                    "                                        }\n"
                    "                                        StyledText {\n"
                    "                                            Layout.fillWidth: true\n"
                    "                                            text: modelData.displayName\n"
                    "                                            font.pixelSize: Appearance.font.pixelSize.small\n"
                    "                                            color: Appearance.m3colors.m3onSurface\n"
                    "                                            elide: Text.ElideRight\n"
                    "                                        }\n"
                    "                                    }\n"
                    "                                }\n"
                    "                            }\n"
                    "                        }\n"
                    "                    }\n"
                    "                }\n"
                    "            }\n\n"
                    "            RippleButton {\n"
                    "                id: startupSortBtn\n"
                    "                implicitWidth: 40\n"
                    "                implicitHeight: 40\n"
                    "                buttonRadius: Appearance.rounding.normal\n"
                    "                colBackground: Appearance.colors.colLayer2\n"
                    "                colBackgroundHover: Appearance.colors.colSurfaceContainerHigh\n"
                    "                onClicked: startupSortPopup.opened ? startupSortPopup.close() : startupSortPopup.open()\n"
                    "                contentItem: MaterialSymbol {\n"
                    "                    anchors.centerIn: parent\n"
                    "                    text: \"sort\"\n"
                    "                    iconSize: 20\n"
                    "                    color: Appearance.m3colors.m3onSurface\n"
                    "                }\n\n"
                    "                Popup {\n"
                    "                    id: startupSortPopup\n"
                    "                    x: parent.width - width\n"
                    "                    y: parent.height + 6\n"
                    "                    width: 200\n"
                    "                    padding: 6\n"
                    "                    modal: false\n"
                    "                    focus: true\n"
                    "                    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent\n\n"
                    "                    background: Rectangle {\n"
                    "                        radius: Appearance.rounding.normal\n"
                    "                        color: Qt.rgba(Appearance.m3colors.m3surfaceContainerLow.r, Appearance.m3colors.m3surfaceContainerLow.g, Appearance.m3colors.m3surfaceContainerLow.b, 1.0)\n"
                    "                        border.width: 1\n"
                    "                        border.color: Appearance.colors.colOutlineVariant\n"
                    "                    }\n\n"
                    "                    contentItem: ColumnLayout {\n"
                    "                        spacing: 4\n"
                    "                        Repeater {\n"
                    "                            model: [\n"
                    "                                { id: \"name\", label: Translation.tr(\"Name\"), icon: \"sort_by_alpha\" },\n"
                    "                                { id: \"date\", label: Translation.tr(\"Date added\"), icon: \"schedule\" },\n"
                    "                                { id: \"status\", label: Translation.tr(\"Active status\"), icon: \"toggle_on\" }\n"
                    "                            ]\n"
                    "                            delegate: RippleButton {\n"
                    "                                required property var modelData\n"
                    "                                readonly property bool active: generalPage.startupSortBy === modelData.id\n"
                    "                                Layout.fillWidth: true\n"
                    "                                implicitHeight: 34\n"
                    "                                buttonRadius: Appearance.rounding.small\n"
                    "                                colBackground: active ? Appearance.colors.colPrimaryContainer : \"transparent\"\n"
                    "                                colBackgroundHover: Appearance.colors.colSurfaceContainerHigh\n"
                    "                                onClicked: {\n"
                    "                                    if (active) {\n"
                    "                                        generalPage.startupSortAsc = !generalPage.startupSortAsc;\n"
                    "                                    } else {\n"
                    "                                        generalPage.startupSortBy = modelData.id;\n"
                    "                                        generalPage.startupSortAsc = (modelData.id === \"name\");\n"
                    "                                    }\n"
                    "                                    startupSortPopup.close();\n"
                    "                                }\n"
                    "                                contentItem: RowLayout {\n"
                    "                                    anchors.fill: parent\n"
                    "                                    anchors.leftMargin: 10\n"
                    "                                    anchors.rightMargin: 10\n"
                    "                                    spacing: 8\n"
                    "                                    MaterialSymbol {\n"
                    "                                        text: modelData.icon\n"
                    "                                        iconSize: 16\n"
                    "                                        color: active ? Appearance.colors.colPrimary : Appearance.m3colors.m3onSurface\n"
                    "                                    }\n"
                    "                                    StyledText {\n"
                    "                                        Layout.fillWidth: true\n"
                    "                                        text: modelData.label\n"
                    "                                        font.pixelSize: Appearance.font.pixelSize.small\n"
                    "                                        color: active ? Appearance.colors.colOnPrimaryContainer : Appearance.m3colors.m3onSurface\n"
                    "                                    }\n"
                    "                                    MaterialSymbol {\n"
                    "                                        visible: active\n"
                    "                                        text: generalPage.startupSortAsc ? \"arrow_upward\" : \"arrow_downward\"\n"
                    "                                        iconSize: 14\n"
                    "                                        color: Appearance.colors.colPrimary\n"
                    "                                    }\n"
                    "                                }\n"
                    "                            }\n"
                    "                        }\n"
                    "                    }\n"
                    "                }\n"
                    "            }\n\n"
                    "            RippleButton {\n"
                    "                implicitWidth: 40\n"
                    "                implicitHeight: 40\n"
                    "                buttonRadius: Appearance.rounding.normal\n"
                    "                colBackground: Appearance.colors.colLayer2\n"
                    "                colBackgroundHover: Appearance.colors.colSurfaceContainerHigh\n"
                    "                onClicked: generalPage.startupGridMode = !generalPage.startupGridMode\n"
                    "                contentItem: MaterialSymbol {\n"
                    "                    anchors.centerIn: parent\n"
                    "                    text: generalPage.startupGridMode ? \"grid_view\" : \"view_headline\"\n"
                    "                    iconSize: 20\n"
                    "                    color: Appearance.m3colors.m3onSurface\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        RowLayout {\n"
                    "            Layout.fillWidth: true\n"
                    "            spacing: 8\n\n"
                    "            MaterialTextArea {\n"
                    "                id: startupNameInput\n"
                    "                Layout.preferredWidth: 140\n"
                    "                placeholderText: Translation.tr(\"App name\")\n"
                    "            }\n\n"
                    "            MaterialTextArea {\n"
                    "                id: startupCmdInput\n"
                    "                Layout.fillWidth: true\n"
                    "                placeholderText: Translation.tr(\"Command or path\")\n"
                    "            }\n\n"
                    "            RippleButton {\n"
                    "                id: addStartupBtn\n"
                    "                implicitWidth: addStartupTxt.implicitWidth + 24\n"
                    "                implicitHeight: 38\n"
                    "                buttonRadius: Appearance.rounding.full\n"
                    "                colBackground: enabled ? Appearance.colors.colPrimary : Appearance.colors.colSurfaceContainerHigh\n"
                    "                colBackgroundHover: Appearance.colors.colPrimaryHover\n"
                    "                enabled: startupNameInput.text.trim() !== \"\" && startupCmdInput.text.trim() !== \"\"\n"
                    "                onClicked: {\n"
                    "                    startupActionProc.command = [\n"
                    "                        \"python3\",\n"
                    "                        Quickshell.shellPath(\"scripts/startup-apps.py\"),\n"
                    "                        \"add\",\n"
                    "                        startupNameInput.text.trim(),\n"
                    "                        startupCmdInput.text.trim(),\n"
                    "                        generalPage.pickedStartupIcon\n"
                    "                    ];\n"
                    "                    startupActionProc.running = false;\n"
                    "                    startupActionProc.running = true;\n"
                    "                    startupNameInput.text = \"\";\n"
                    "                    startupCmdInput.text = \"\";\n"
                    "                    generalPage.pickedStartupIcon = \"\";\n"
                    "                }\n"
                    "                contentItem: StyledText {\n"
                    "                    id: addStartupTxt\n"
                    "                    anchors.centerIn: parent\n"
                    "                    text: Translation.tr(\"Add\")\n"
                    "                    color: addStartupBtn.enabled ? Appearance.m3colors.m3onPrimary : Appearance.colors.colSubtext\n"
                    "                    font.pixelSize: Appearance.font.pixelSize.small\n"
                    "                    font.weight: Font.Medium\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        Rectangle {\n"
                    "            Layout.fillWidth: true\n"
                    "            implicitHeight: 1\n"
                    "            color: Appearance.colors.colOutlineVariant\n"
                    "            opacity: 0.65\n"
                    "        }\n\n"
                    "        Flickable {\n"
                    "            id: startupScroll\n"
                    "            Layout.fillWidth: true\n"
                    "            implicitHeight: Math.min(Math.max(88, startupGrid.implicitHeight + 4), 260)\n"
                    "            contentWidth: width\n"
                    "            contentHeight: startupGrid.implicitHeight\n"
                    "            clip: true\n"
                    "            boundsBehavior: Flickable.StopAtBounds\n"
                    "            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }\n\n"
                    "            GridLayout {\n"
                    "                id: startupGrid\n"
                    "                width: startupScroll.width\n"
                    "                columnSpacing: 8\n"
                    "                rowSpacing: 8\n"
                    "                columns: generalPage.startupGridMode ? 2 : 1\n\n"
                    "                Repeater {\n"
                    "                    model: generalPage.sortedStartupApps\n"
                    "                    delegate: Rectangle {\n"
                    "                        required property var modelData\n"
                    "                        Layout.fillWidth: true\n"
                    "                        implicitHeight: 48\n"
                    "                        radius: Appearance.rounding.normal\n"
                    "                        color: Appearance.colors.colLayer2\n"
                    "                        border.width: 1\n"
                    "                        border.color: modelData.enabled ? Appearance.colors.colPrimaryContainer : Appearance.colors.colOutlineVariant\n\n"
                    "                        RowLayout {\n"
                    "                            anchors.fill: parent\n"
                    "                            anchors.leftMargin: 12\n"
                    "                            anchors.rightMargin: 10\n"
                    "                            spacing: 10\n\n"
                    "                            Image {\n"
                    "                                width: 22\n"
                    "                                height: 22\n"
                    "                                sourceSize: Qt.size(22, 22)\n"
                    "                                source: {\n"
                    "                                    const ic = modelData.icon || \"application-x-executable\";\n"
                    "                                    if (ic.startsWith(\"/\")) return \"file://\" + ic;\n"
                    "                                    return Quickshell.iconPath(ic, \"application-x-executable\");\n"
                    "                                }\n"
                    "                                fillMode: Image.PreserveAspectFit\n"
                    "                            }\n\n"
                    "                            StyledText {\n"
                    "                                Layout.fillWidth: true\n"
                    "                                text: modelData.name\n"
                    "                                font.pixelSize: Appearance.font.pixelSize.small\n"
                    "                                font.weight: Font.Medium\n"
                    "                                color: Appearance.m3colors.m3onSurface\n"
                    "                                elide: Text.ElideRight\n"
                    "                            }\n\n"
                    "                            RippleButton {\n"
                    "                                visible: modelData.removable\n"
                    "                                implicitWidth: 26\n"
                    "                                implicitHeight: 26\n"
                    "                                buttonRadius: Appearance.rounding.full\n"
                    "                                colBackground: \"transparent\"\n"
                    "                                colBackgroundHover: Appearance.colors.colSurfaceContainerHigh\n"
                    "                                onClicked: {\n"
                    "                                    startupActionProc.command = [\n"
                    "                                        \"python3\",\n"
                    "                                        Quickshell.shellPath(\"scripts/startup-apps.py\"),\n"
                    "                                        \"remove\",\n"
                    "                                        modelData.id\n"
                    "                                    ];\n"
                    "                                    startupActionProc.running = false;\n"
                    "                                    startupActionProc.running = true;\n"
                    "                                }\n"
                    "                                contentItem: MaterialSymbol {\n"
                    "                                    anchors.centerIn: parent\n"
                    "                                    text: \"delete\"\n"
                    "                                    iconSize: 16\n"
                    "                                    color: Appearance.colors.colError\n"
                    "                                }\n"
                    "                            }\n\n"
                    "                            StyledSwitch {\n"
                    "                                checked: modelData.enabled\n"
                    "                                onClicked: {\n"
                    "                                    startupActionProc.command = [\n"
                    "                                        \"python3\",\n"
                    "                                        Quickshell.shellPath(\"scripts/startup-apps.py\"),\n"
                    "                                        \"toggle\",\n"
                    "                                        modelData.id,\n"
                    "                                        checked ? \"1\" : \"0\"\n"
                    "                                    ];\n"
                    "                                    startupActionProc.running = false;\n"
                    "                                    startupActionProc.running = true;\n"
                    "                                }\n"
                    "                            }\n"
                    "                        }\n"
                    "                    }\n"
                    "                }\n"
                    "            }\n"
                    "        }\n\n"
                    "        Rectangle {\n"
                    "            Layout.fillWidth: true\n"
                    "            implicitHeight: 1\n"
                    "            color: Appearance.colors.colOutlineVariant\n"
                    "            opacity: 0.65\n"
                    "        }\n\n"
                    "        StyledText {\n"
                    "            visible: generalPage.startupApps.length === 0\n"
                    "            text: Translation.tr(\"No startup apps found\")\n"
                    "            color: Appearance.colors.colSubtext\n"
                    "            font.pixelSize: Appearance.font.pixelSize.small\n"
                    "        }\n"
                    "    }\n\n"
                    "    ContentSection {\n"
                    "        icon: \"rule\"\n"
                    "        title: Translation.tr(\"Policies\")",
                ),
            ],
        )

    # Per-monitor wallpaper support (QuickConfig + Config + Background + switchwall.sh)
    ok &= patch_file(
        ii / "modules/common/Config.qml",
        [
            (
                "property list<string> monitorOrder:",
                "                property string wallpaperPath: \"\"\n"
                "                property string thumbnailPath: \"\"\n",
                "                property string wallpaperPath: \"\"\n"
                "                property string thumbnailPath: \"\"\n"
                "                property bool perMonitor: false\n"
                "                property var monitors: ({})\n"
                "                property string selectedMonitor: \"\"\n"
                "                property list<string> monitorOrder: []\n"
                "                property JsonObject live: JsonObject {\n"
                "                    property real speed: 1.0\n"
                "                    property bool muted: true\n"
                "                    property real volume: 0.3\n"
                "                    property string fillMode: \"crop\"\n"
                "                    property int position: 50\n"
                "                    property bool pauseOnFullscreen: true\n"
                "                    property bool loop: true\n"
                "                }\n",
            ),
        ],
    )

    ok &= patch_file(
        ii / "modules/settings/QuickConfig.qml",
        [
            (
                "previewIsVideo",
                '            Item {\n                implicitWidth: 340\n                implicitHeight: 200\n                \n                StyledImage {\n                    id: wallpaperPreview\n                    anchors.fill: parent\n                    fillMode: Image.PreserveAspectCrop\n                    source: Config.options.background.wallpaperPath\n                    cache: false\n                    layer.enabled: true\n                    layer.effect: OpacityMask {\n                        maskSource: Rectangle {\n                            width: 360\n                            height: 200\n                            radius: Appearance.rounding.normal\n                        }\n                    }\n                }\n            }\n\n',
                '            Item {\n                id: previewFadeWrapper\n                implicitWidth: 340\n                implicitHeight: 200\n                readonly property bool previewIsVideo: /\\.(mp4|webm|mkv|avi|mov)$/i.test(quickPage.previewWallpaperPath)\n                readonly property bool previewIsGif: /\\.gif$/i.test(quickPage.previewWallpaperPath)\n                NumberAnimation on opacity {\n                    id: previewFadeAnim\n                    from: 0.25\n                    to: 1\n                    duration: 180\n                    easing.type: Easing.OutCubic\n                    running: false\n                }\n                Connections {\n                    target: quickPage\n                    function onPreviewWallpaperPathChanged() {\n                        previewFadeAnim.restart();\n                    }\n                }\n                Item {\n                    anchors.fill: parent\n                    layer.enabled: true\n                    layer.effect: OpacityMask {\n                        maskSource: Rectangle {\n                            width: 340\n                            height: 200\n                            radius: Appearance.rounding.normal\n                        }\n                    }\n                    StyledImage {\n                        id: wallpaperPreview\n                        anchors.fill: parent\n                        visible: !previewFadeWrapper.previewIsVideo && !previewFadeWrapper.previewIsGif\n                        fillMode: Image.PreserveAspectCrop\n                        source: visible ? quickPage.previewWallpaperPath : ""\n                        cache: true\n                    }\n                    AnimatedImage {\n                        anchors.fill: parent\n                        visible: previewFadeWrapper.previewIsGif\n                        source: visible ? ("file://" + quickPage.previewWallpaperPath.replace(/^file:\\/\\//, "")) : ""\n                        fillMode: Image.PreserveAspectCrop\n                        playing: visible && quickPage.visible\n                        asynchronous: true\n                    }\n                    Loader {\n                        id: livePreviewVideoLoader\n                        anchors.fill: parent\n                        // Two-phase teardown: stop + detach the player first, destroy the item\n                        // after a short delay so the render thread never samples a deleted video sink.\n                        readonly property bool wanted: previewFadeWrapper.previewIsVideo && quickPage.visible && quickPage.previewWallpaperPath !== ""\n                        property bool gate: false\n                        active: gate\n                        visible: active\n                        Component.onCompleted: gate = wanted\n                        onWantedChanged: {\n                            if (wanted) {\n                                quickPreviewGateTimer.stop();\n                                gate = true;\n                                if (item) item.resume();\n                            } else {\n                                if (item) item.shutdown();\n                                quickPreviewGateTimer.restart();\n                            }\n                        }\n                        Timer {\n                            id: quickPreviewGateTimer\n                            interval: 300\n                            onTriggered: livePreviewVideoLoader.gate = livePreviewVideoLoader.wanted\n                        }\n                        sourceComponent: Item {\n                            id: quickPreviewRoot\n                            anchors.fill: parent\n                            property bool shut: false\n                            function shutdown() { shut = true; previewVidPlayer.stop(); }\n                            function resume() { shut = false; previewVidPlayer.play(); }\n                            MediaPlayer {\n                                id: previewVidPlayer\n                                source: (quickPreviewRoot.shut || !previewFadeWrapper.previewIsVideo) ? "" : "file://" + quickPage.previewWallpaperPath.replace(/^file:\\/\\//, "")\n                                loops: MediaPlayer.Infinite\n                                audioOutput: AudioOutput { muted: true }\n                                videoOutput: quickPreviewRoot.shut ? null : previewVidOut\n                                Component.onCompleted: if (!quickPreviewRoot.shut && source.toString() !== "") play()\n                                onSourceChanged: {\n                                    stop();\n                                    if (!quickPreviewRoot.shut && source.toString() !== "") play();\n                                }\n                                onMediaStatusChanged: {\n                                    if (mediaStatus === MediaPlayer.LoadedMedia && !quickPreviewRoot.shut && playbackState !== MediaPlayer.PlayingState)\n                                        play();\n                                }\n                                onErrorOccurred: (error, errorString) => console.warn("[QuickConfig] preview MediaPlayer error:", error, errorString)\n                            }\n                            VideoOutput {\n                                id: previewVidOut\n                                anchors.fill: parent\n                                fillMode: VideoOutput.PreserveAspectCrop\n                            }\n                        }\n                    }\n                    Rectangle {\n                        visible: previewFadeWrapper.previewIsVideo || previewFadeWrapper.previewIsGif\n                        anchors.top: parent.top\n                        anchors.left: parent.left\n                        anchors.margins: 8\n                        radius: Appearance.rounding.full\n                        color: Qt.rgba(0, 0, 0, 0.65)\n                        implicitWidth: liveBadgeRow.implicitWidth + 14\n                        implicitHeight: 24\n                        RowLayout {\n                            id: liveBadgeRow\n                            anchors.centerIn: parent\n                            spacing: 4\n                            MaterialSymbol {\n                                text: "play_circle"\n                                iconSize: 14\n                                color: "#ffffff"\n                            }\n                            StyledText {\n                                text: previewFadeWrapper.previewIsGif ? "GIF" : "LIVE"\n                                color: "#ffffff"\n                                font.pixelSize: 11\n                                font.weight: Font.Medium\n                            }\n                        }\n                    }\n                }\n            }\n\n',
            ),
            (
                "property string selectedWallpaperMonitor:",
                "ContentPage {\n"
                "    forceWidth: true",
                "ContentPage {\n"
                "    id: quickPage\n"
                "    forceWidth: true\n\n"
                "    property string selectedWallpaperMonitor: Quickshell.screens.length > 0 ? Quickshell.screens[0].name : \"\"\n\n"
                "    readonly property string previewWallpaperPath: {\n"
                "        if (Config.options.background.perMonitor && quickPage.selectedWallpaperMonitor !== \"\") {\n"
                "            const entry = Config.options.background.monitors?.[quickPage.selectedWallpaperMonitor];\n"
                "            if (entry && entry.wallpaperPath && entry.wallpaperPath !== \"\")\n"
                "                return entry.wallpaperPath;\n"
                "        }\n"
                "        return Config.options.background.wallpaperPath;\n"
                "    }",
            ),
            (
                "II_TARGET_MONITOR",
                "                    onClicked: {\n"
                "                        randomWallProc.scriptPath = `${Directories.scriptPath}/colors/random/random_konachan_wall.sh`;\n"
                "                        randomWallProc.running = true;\n"
                "                    }",
                "                    onClicked: {\n"
                "                        const mon = (Config.options.background.perMonitor && quickPage.selectedWallpaperMonitor !== \"\") ? quickPage.selectedWallpaperMonitor : \"\";\n"
                "                        randomWallProc.command = [\"bash\", \"-c\", `II_TARGET_MONITOR=\"${mon}\" \"${FileUtils.trimFileProtocol(Directories.scriptPath)}/colors/random/random_konachan_wall.sh\"`];\n"
                "                        randomWallProc.running = true;\n"
                "                    }",
            ),
            (
                'II_TARGET_MONITOR="${mon}" "${FileUtils.trimFileProtocol(Directories.scriptPath)}/colors/random/random_osu_wall.sh"',
                "                    onClicked: {\n"
                "                        randomWallProc.scriptPath = `${Directories.scriptPath}/colors/random/random_osu_wall.sh`;\n"
                "                        randomWallProc.running = true;\n"
                "                    }",
                "                    onClicked: {\n"
                "                        const mon = (Config.options.background.perMonitor && quickPage.selectedWallpaperMonitor !== \"\") ? quickPage.selectedWallpaperMonitor : \"\";\n"
                "                        randomWallProc.command = [\"bash\", \"-c\", `II_TARGET_MONITOR=\"${mon}\" \"${FileUtils.trimFileProtocol(Directories.scriptPath)}/colors/random/random_osu_wall.sh\"`];\n"
                "                        randomWallProc.running = true;\n"
                "                    }",
            ),
            (
                "--monitor \"${quickPage.selectedWallpaperMonitor}\"",
                "                    onClicked: {\n"
                "                        Quickshell.execDetached(`${Directories.wallpaperSwitchScriptPath}`);\n"
                "                    }",
                "                    onClicked: {\n"
                "                        if (Config.options.background.perMonitor && quickPage.selectedWallpaperMonitor !== \"\") {\n"
                "                            Quickshell.execDetached([\"bash\", \"-c\", `${Directories.wallpaperSwitchScriptPath} --monitor \"${quickPage.selectedWallpaperMonitor}\"`]);\n"
                "                        } else {\n"
                "                            Quickshell.execDetached(`${Directories.wallpaperSwitchScriptPath}`);\n"
                "                        }\n"
                "                    }",
            ),
            (
                "import QtMultimedia",
                "import QtQuick\nimport QtQuick.Layouts",
                "import QtQuick\nimport QtMultimedia\nimport QtQuick.Layouts",
            ),
            (
                "quickLiveStoreDialog",
                "    property string selectedWallpaperMonitor: Quickshell.screens.length > 0 ? Quickshell.screens[0].name : \"\"\n",
                "    property string selectedWallpaperMonitor: Quickshell.screens.length > 0 ? Quickshell.screens[0].name : \"\"\n",
            ),
            (
                "quickLiveStoreBtn",
                "                    onClicked: {\n"
                "                        if (Config.options.background.perMonitor && quickPage.selectedWallpaperMonitor !== \"\") {\n"
                "                            Quickshell.execDetached([\"bash\", \"-c\", `${Directories.wallpaperSwitchScriptPath} --monitor \"${quickPage.selectedWallpaperMonitor}\"`]);\n"
                "                        } else {\n"
                "                            Quickshell.execDetached(`${Directories.wallpaperSwitchScriptPath}`);\n"
                "                        }\n"
                "                    }",
                "                    onClicked: {\n"
                "                        if (Config.options.background.perMonitor && quickPage.selectedWallpaperMonitor !== \"\") {\n"
                "                            Quickshell.execDetached([\"bash\", \"-c\", `${Directories.wallpaperSwitchScriptPath} --monitor \"${quickPage.selectedWallpaperMonitor}\"`]);\n"
                "                        } else {\n"
                "                            Quickshell.execDetached(`${Directories.wallpaperSwitchScriptPath}`);\n"
                "                        }\n"
                "                    }",
            ),
            (
                "previewIsVideo",
                "            Item {\n"
                "                id: previewFadeWrapper\n"
                "                implicitWidth: 340\n"
                "                implicitHeight: 200",
                "            Item {\n"
                "                id: previewFadeWrapper\n"
                "                implicitWidth: 340\n"
                "                implicitHeight: 200\n"
                "                readonly property bool previewIsVideo: /\\.(mp4|webm|mkv|avi|mov)$/i.test(quickPage.previewWallpaperPath)\n"
                "                readonly property bool previewIsGif: /\\.gif$/i.test(quickPage.previewWallpaperPath)",
            ),
            (
                "livePreviewVideoLoader",
                "                StyledImage {\n"
                "                    id: wallpaperPreview\n"
                "                    anchors.fill: parent\n"
                "                    fillMode: Image.PreserveAspectCrop\n"
                "                    source: quickPage.previewWallpaperPath\n"
                "                    cache: true\n"
                "                    layer.enabled: true\n"
                "                    layer.effect: OpacityMask {\n"
                "                        maskSource: Rectangle {\n"
                "                            width: 360\n"
                "                            height: 200\n"
                "                            radius: Appearance.rounding.normal\n"
                "                        }\n"
                "                    }\n"
                "                }",
                "                Item {\n"
                "                    anchors.fill: parent\n"
                "                    layer.enabled: true\n"
                "                    layer.effect: OpacityMask {\n"
                "                        maskSource: Rectangle {\n"
                "                            width: 340\n"
                "                            height: 200\n"
                "                            radius: Appearance.rounding.normal\n"
                "                        }\n"
                "                    }\n"
                "                    StyledImage {\n"
                "                        id: wallpaperPreview\n"
                "                        anchors.fill: parent\n"
                "                        visible: !previewFadeWrapper.previewIsVideo && !previewFadeWrapper.previewIsGif\n"
                "                        fillMode: Image.PreserveAspectCrop\n"
                "                        source: visible ? quickPage.previewWallpaperPath : \"\"\n"
                "                        cache: true\n"
                "                    }\n"
                "                    AnimatedImage {\n"
                "                        anchors.fill: parent\n"
                "                        visible: previewFadeWrapper.previewIsGif\n"
                "                        source: visible ? (\"file://\" + quickPage.previewWallpaperPath.replace(/^file:\\/\\//, \"\")) : \"\"\n"
                "                        fillMode: Image.PreserveAspectCrop\n"
                "                        playing: visible && quickPage.visible\n"
                "                        asynchronous: true\n"
                "                    }\n"
                "                    Loader {\n"
                "                        id: livePreviewVideoLoader\n"
                "                        anchors.fill: parent\n"
                "                        // Two-phase teardown: stop + detach the player first, destroy the item\n"
                "                        // after a short delay so the render thread never samples a deleted video sink.\n"
                "                        readonly property bool wanted: previewFadeWrapper.previewIsVideo && quickPage.visible && quickPage.previewWallpaperPath !== \"\"\n"
                "                        property bool gate: false\n"
                "                        active: gate\n"
                "                        visible: active\n"
                "                        Component.onCompleted: gate = wanted\n"
                "                        onWantedChanged: {\n"
                "                            if (wanted) {\n"
                "                                quickPreviewGateTimer.stop();\n"
                "                                gate = true;\n"
                "                                if (item) item.resume();\n"
                "                            } else {\n"
                "                                if (item) item.shutdown();\n"
                "                                quickPreviewGateTimer.restart();\n"
                "                            }\n"
                "                        }\n"
                "                        Timer {\n"
                "                            id: quickPreviewGateTimer\n"
                "                            interval: 300\n"
                "                            onTriggered: livePreviewVideoLoader.gate = livePreviewVideoLoader.wanted\n"
                "                        }\n"
                "                        sourceComponent: Item {\n"
                "                            id: quickPreviewRoot\n"
                "                            anchors.fill: parent\n"
                "                            property bool shut: false\n"
                "                            function shutdown() { shut = true; previewVidPlayer.stop(); }\n"
                "                            function resume() { shut = false; previewVidPlayer.play(); }\n"
                "                            MediaPlayer {\n"
                "                                id: previewVidPlayer\n"
                "                                source: (quickPreviewRoot.shut || !previewFadeWrapper.previewIsVideo) ? \"\" : \"file://\" + quickPage.previewWallpaperPath.replace(/^file:\\/\\//, \"\")\n"
                "                                loops: MediaPlayer.Infinite\n"
                "                                audioOutput: AudioOutput { muted: true }\n"
                "                                videoOutput: quickPreviewRoot.shut ? null : previewVidOut\n"
                "                                Component.onCompleted: if (!quickPreviewRoot.shut && source.toString() !== \"\") play()\n"
                "                                onSourceChanged: {\n"
                "                                    stop();\n"
                "                                    if (!quickPreviewRoot.shut && source.toString() !== \"\") play();\n"
                "                                }\n"
                "                                onMediaStatusChanged: {\n"
                "                                    if (mediaStatus === MediaPlayer.LoadedMedia && !quickPreviewRoot.shut && playbackState !== MediaPlayer.PlayingState)\n"
                "                                        play();\n"
                "                                }\n"
                "                                onErrorOccurred: (error, errorString) => console.warn(\"[QuickConfig] preview MediaPlayer error:\", error, errorString)\n"
                "                            }\n"
                "                            VideoOutput {\n"
                "                                id: previewVidOut\n"
                "                                anchors.fill: parent\n"
                "                                fillMode: VideoOutput.PreserveAspectCrop\n"
                "                            }\n"
                "                        }\n"
                "                    }\n"
                "                    Rectangle {\n"
                "                        visible: previewFadeWrapper.previewIsVideo || previewFadeWrapper.previewIsGif\n"
                "                        anchors.top: parent.top\n"
                "                        anchors.left: parent.left\n"
                "                        anchors.margins: 8\n"
                "                        radius: Appearance.rounding.full\n"
                "                        color: Qt.rgba(0, 0, 0, 0.65)\n"
                "                        implicitWidth: liveBadgeRow.implicitWidth + 14\n"
                "                        implicitHeight: 24\n"
                "                        RowLayout {\n"
                "                            id: liveBadgeRow\n"
                "                            anchors.centerIn: parent\n"
                "                            spacing: 4\n"
                "                            MaterialSymbol {\n"
                "                                text: \"play_circle\"\n"
                "                                iconSize: 14\n"
                "                                color: \"#ffffff\"\n"
                "                            }\n"
                "                            StyledText {\n"
                "                                text: previewFadeWrapper.previewIsGif ? \"GIF\" : \"LIVE\"\n"
                "                                color: \"#ffffff\"\n"
                "                                font.pixelSize: 11\n"
                "                                font.weight: Font.Medium\n"
                "                            }\n"
                "                        }\n"
                "                    }\n"
                "                }",
            ),
            (
                "quickPage.previewWallpaperPath",
                "source: Config.options.background.wallpaperPath",
                "source: quickPage.previewWallpaperPath",
            ),
            (
                'text: Translation.tr("Separate per monitor")',
                "        ConfigSelectionArray {\n"
                "            currentValue: Config.options.appearance.palette.type",
                "        ConfigSwitch {\n"
                "            buttonIcon: \"desktop_windows\"\n"
                "            text: Translation.tr(\"Separate per monitor\")\n"
                "            checked: Config.options.background.perMonitor\n"
                "            onCheckedChanged: {\n"
                "                if (Config.options.background.perMonitor !== checked) {\n"
                "                    Config.options.background.perMonitor = checked;\n"
                "                }\n"
                "            }\n"
                "        }\n\n"
                "        MonitorOrderPills {\n"
                "            visible: Config.options.background.perMonitor\n"
                "            selectedMonitor: quickPage.selectedWallpaperMonitor\n"
                "            onMonitorSelected: name => quickPage.selectedWallpaperMonitor = name\n"
                "        }\n\n"
                "        ConfigSelectionArray {\n"
                "            currentValue: Config.options.appearance.palette.type",
            ),
            (
                "quickPreviewGateTimer",
                '                    Loader {\n                        id: livePreviewVideoLoader\n                        anchors.fill: parent\n                        active: previewFadeWrapper.previewIsVideo && quickPage.visible && quickPage.previewWallpaperPath !== ""\n                        visible: active\n                        sourceComponent: Item {\n                            anchors.fill: parent\n                            MediaPlayer {\n                                id: previewVidPlayer\n                                source: "file://" + quickPage.previewWallpaperPath.replace(/^file:\\/\\//, "")\n                                loops: MediaPlayer.Infinite\n                                audioOutput: AudioOutput { muted: true }\n                                videoOutput: previewVidOut\n                                Component.onCompleted: play()\n                            }\n                            VideoOutput {\n                                id: previewVidOut\n                                anchors.fill: parent\n                                fillMode: VideoOutput.PreserveAspectCrop\n                            }\n                        }\n                    }\n',
                '                    Loader {\n                        id: livePreviewVideoLoader\n                        anchors.fill: parent\n                        // Two-phase teardown: stop + detach the player first, destroy the item\n                        // after a short delay so the render thread never samples a deleted video sink.\n                        readonly property bool wanted: previewFadeWrapper.previewIsVideo && quickPage.visible && quickPage.previewWallpaperPath !== ""\n                        property bool gate: false\n                        active: gate\n                        visible: active\n                        Component.onCompleted: gate = wanted\n                        onWantedChanged: {\n                            if (wanted) {\n                                quickPreviewGateTimer.stop();\n                                gate = true;\n                                if (item) item.resume();\n                            } else {\n                                if (item) item.shutdown();\n                                quickPreviewGateTimer.restart();\n                            }\n                        }\n                        Timer {\n                            id: quickPreviewGateTimer\n                            interval: 300\n                            onTriggered: livePreviewVideoLoader.gate = livePreviewVideoLoader.wanted\n                        }\n                        sourceComponent: Item {\n                            id: quickPreviewRoot\n                            anchors.fill: parent\n                            property bool shut: false\n                            function shutdown() { shut = true; previewVidPlayer.stop(); }\n                            function resume() { shut = false; previewVidPlayer.play(); }\n                            MediaPlayer {\n                                id: previewVidPlayer\n                                source: (quickPreviewRoot.shut || !previewFadeWrapper.previewIsVideo) ? "" : "file://" + quickPage.previewWallpaperPath.replace(/^file:\\/\\//, "")\n                                loops: MediaPlayer.Infinite\n                                audioOutput: AudioOutput { muted: true }\n                                videoOutput: quickPreviewRoot.shut ? null : previewVidOut\n                                Component.onCompleted: if (!quickPreviewRoot.shut && source.toString() !== "") play()\n                                onSourceChanged: {\n                                    stop();\n                                    if (!quickPreviewRoot.shut && source.toString() !== "") play();\n                                }\n                                onMediaStatusChanged: {\n                                    if (mediaStatus === MediaPlayer.LoadedMedia && !quickPreviewRoot.shut && playbackState !== MediaPlayer.PlayingState)\n                                        play();\n                                }\n                                onErrorOccurred: (error, errorString) => console.warn("[QuickConfig] preview MediaPlayer error:", error, errorString)\n                            }\n                            VideoOutput {\n                                id: previewVidOut\n                                anchors.fill: parent\n                                fillMode: VideoOutput.PreserveAspectCrop\n                            }\n                        }\n                    }\n',
            ),
        ],
    )

    ok &= patch_file(
        ii / "settings.qml",
        [
            (
                "WallpaperConfig.qml",
                '        {\n'
                '            name: Translation.tr("Background"),\n'
                '            icon: "texture",\n'
                '            component: "modules/settings/BackgroundConfig.qml"\n'
                '        },',
                '        {\n'
                '            name: Translation.tr("Background"),\n'
                '            icon: "texture",\n'
                '            component: "modules/settings/BackgroundConfig.qml"\n'
                '        },\n'
                '        {\n'
                '            name: Translation.tr("Wallpaper"),\n'
                '            icon: "wallpaper",\n'
                '            component: "modules/settings/WallpaperConfig.qml"\n'
                '        },',
            ),
            (
                "height: 850",
                "    width: 1100\n    height: 750",
                "    width: 1100\n    height: 850",
            ),
        ],
    )

    ok &= patch_file(
        ii / "modules/common/widgets/NavigationRailButton.qml",
        [
            (
                "itemTextBox",
                "        StyledText {\n"
                "            id: itemText\n"
                "            anchors {\n"
                "                top: itemIconBackground.bottom\n"
                "                topMargin: 2\n"
                "                horizontalCenter: itemIconBackground.horizontalCenter\n"
                "            }\n"
                "            states: State {\n"
                "                name: \"expanded\"\n"
                "                when: root.expanded\n"
                "                AnchorChanges {\n"
                "                    target: itemText\n"
                "                    anchors {\n"
                "                        top: undefined\n"
                "                        horizontalCenter: undefined\n"
                "                        left: itemIconBackground.right\n"
                "                        verticalCenter: itemIconBackground.verticalCenter\n"
                "                    }\n"
                "                }\n"
                "            }\n"
                "            transitions: Transition {\n"
                "                AnchorAnimation {\n"
                "                    duration: Appearance.animation.elementMoveFast.duration\n"
                "                    easing.type: Appearance.animation.elementMoveFast.type\n"
                "                    easing.bezierCurve: Appearance.animation.elementMoveFast.bezierCurve\n"
                "                }\n"
                "            }\n"
                "            text: buttonText\n"
                "            font.pixelSize: 14\n"
                "            color: Appearance.colors.colOnLayer1\n"
                "        }",
                "        Item {\n"
                "            id: itemTextBox\n"
                "            clip: !root.expanded\n"
                "            implicitWidth: root.expanded ? itemText.implicitWidth : Math.min(itemText.implicitWidth, root.baseSize - 4)\n"
                "            implicitHeight: itemText.implicitHeight\n"
                "            anchors {\n"
                "                top: itemIconBackground.bottom\n"
                "                topMargin: 2\n"
                "                horizontalCenter: itemIconBackground.horizontalCenter\n"
                "            }\n"
                "            states: State {\n"
                "                name: \"expanded\"\n"
                "                when: root.expanded\n"
                "                AnchorChanges {\n"
                "                    target: itemTextBox\n"
                "                    anchors {\n"
                "                        top: undefined\n"
                "                        horizontalCenter: undefined\n"
                "                        left: itemIconBackground.right\n"
                "                        verticalCenter: itemIconBackground.verticalCenter\n"
                "                    }\n"
                "                }\n"
                "            }\n"
                "            transitions: Transition {\n"
                "                AnchorAnimation {\n"
                "                    duration: Appearance.animation.elementMoveFast.duration\n"
                "                    easing.type: Appearance.animation.elementMoveFast.type\n"
                "                    easing.bezierCurve: Appearance.animation.elementMoveFast.bezierCurve\n"
                "                }\n"
                "            }\n\n"
                "            Row {\n"
                "                id: marqueeRow\n"
                "                readonly property real gap: 28\n"
                "                readonly property bool shouldScroll: !root.expanded && itemText.implicitWidth > (root.baseSize - 4)\n"
                "                spacing: marqueeRow.gap\n"
                "                x: 0\n\n"
                "                StyledText {\n"
                "                    id: itemText\n"
                "                    text: buttonText\n"
                "                    font.pixelSize: 14\n"
                "                    color: Appearance.colors.colOnLayer1\n"
                "                }\n\n"
                "                StyledText {\n"
                "                    visible: marqueeRow.shouldScroll\n"
                "                    text: buttonText\n"
                "                    font.pixelSize: 14\n"
                "                    color: Appearance.colors.colOnLayer1\n"
                "                }\n\n"
                "                NumberAnimation on x {\n"
                "                    running: marqueeRow.shouldScroll && root.visible\n"
                "                    loops: Animation.Infinite\n"
                "                    from: 0\n"
                "                    to: -(itemText.implicitWidth + marqueeRow.gap)\n"
                "                    duration: Math.max(2200, Math.round((itemText.implicitWidth + marqueeRow.gap) * 35))\n"
                "                    easing.type: Easing.Linear\n"
                "                }\n"
                "            }\n"
                "        }",
            ),
        ],
    )

    ok &= patch_file(
        ii / "modules/settings/BarConfig.qml",
        [
            (
                "MonitorOrderPills",
                "        Repeater {\n"
                "            model: (barConfigPage.hasMultipleMonitors && Config.options.bar.workspaces.splitByMonitor)",
                "        MonitorOrderPills {\n"
                "            visible: barConfigPage.hasMultipleMonitors && Config.options.bar.workspaces.splitByMonitor\n"
                "            selectable: false\n"
                "        }\n\n"
                "        Repeater {\n"
                "            model: (barConfigPage.hasMultipleMonitors && Config.options.bar.workspaces.splitByMonitor)",
            ),
        ],
    )

    ok &= patch_file(
        ii / "services/Wallpapers.qml",
        [
            (
                '"mp4", "webm"',
                '    readonly property list<string> extensions: [ // TODO: add videos\n'
                '        "jpg", "jpeg", "png", "webp", "avif", "bmp", "svg"\n'
                '    ]',
                '    readonly property list<string> extensions: [\n'
                '        "jpg", "jpeg", "png", "webp", "avif", "bmp", "svg",\n'
                '        "gif", "mp4", "webm", "mkv", "avi", "mov"\n'
                '    ]',
            ),
        ],
    )

    ok &= patch_file(
        ii / "modules/ii/background/widgets/AbstractBackgroundWidget.qml",
        [
            (
                "readonly property string rawWallpaperPath:",
                "    property bool wallpaperIsVideo: Config.options.background.wallpaperPath.endsWith(\".mp4\") || Config.options.background.wallpaperPath.endsWith(\".webm\") || Config.options.background.wallpaperPath.endsWith(\".mkv\") || Config.options.background.wallpaperPath.endsWith(\".avi\") || Config.options.background.wallpaperPath.endsWith(\".mov\")\n"
                "    property string wallpaperPath: wallpaperIsVideo ? Config.options.background.thumbnailPath : Config.options.background.wallpaperPath",
                "    readonly property string monitorName: QsWindow.window?.screen?.name ?? \"\"\n"
                "    readonly property var monitorCfg: (Config.options.background.perMonitor && monitorName !== \"\") ? (Config.options.background.monitors?.[monitorName] ?? null) : null\n"
                "    readonly property string rawWallpaperPath: (monitorCfg?.wallpaperPath && monitorCfg.wallpaperPath !== \"\") ? monitorCfg.wallpaperPath : Config.options.background.wallpaperPath\n"
                "    readonly property string rawThumbnailPath: (monitorCfg?.thumbnailPath && monitorCfg.thumbnailPath !== \"\") ? monitorCfg.thumbnailPath : Config.options.background.thumbnailPath\n"
                "    property bool wallpaperIsVideo: rawWallpaperPath.endsWith(\".mp4\") || rawWallpaperPath.endsWith(\".webm\") || rawWallpaperPath.endsWith(\".mkv\") || rawWallpaperPath.endsWith(\".avi\") || rawWallpaperPath.endsWith(\".mov\")\n"
                "    property string wallpaperPath: wallpaperIsVideo ? rawThumbnailPath : rawWallpaperPath",
            ),
        ],
    )

    ok &= patch_file(
        ii / "modules/ii/wallpaperSelector/WallpaperSelectorContent.qml",
        [
            (
                "readonly property string activeWallpaperPath:",
                "                        model: Wallpapers.folderModel\n"
                "                        onModelChanged: currentIndex = 0\n"
                "                        delegate: WallpaperDirectoryItem {\n"
                "                            required property var modelData\n"
                "                            required property int index\n"
                "                            fileModelData: modelData\n"
                "                            width: grid.cellWidth\n"
                "                            height: grid.cellHeight\n"
                "                            colBackground: (index === grid?.currentIndex || containsMouse) ? Appearance.colors.colPrimary : (fileModelData.filePath === Config.options.background.wallpaperPath) ? Appearance.colors.colSecondaryContainer : ColorUtils.transparentize(Appearance.colors.colPrimaryContainer)\n"
                "                            colText: (index === grid.currentIndex || containsMouse) ? Appearance.colors.colOnPrimary : (fileModelData.filePath === Config.options.background.wallpaperPath) ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer0",
                "                        model: Wallpapers.folderModel\n"
                "                        onModelChanged: currentIndex = 0\n"
                "                        delegate: WallpaperDirectoryItem {\n"
                "                            required property var modelData\n"
                "                            required property int index\n"
                "                            readonly property string activeWallpaperPath: (Config.options.background.perMonitor && (Config.options.background.selectedMonitor ?? \"\") !== \"\" && Config.options.background.monitors?.[Config.options.background.selectedMonitor]?.wallpaperPath) ? Config.options.background.monitors[Config.options.background.selectedMonitor].wallpaperPath : Config.options.background.wallpaperPath\n"
                "                            fileModelData: modelData\n"
                "                            width: grid.cellWidth\n"
                "                            height: grid.cellHeight\n"
                "                            colBackground: (index === grid?.currentIndex || containsMouse) ? Appearance.colors.colPrimary : (fileModelData.filePath === activeWallpaperPath) ? Appearance.colors.colSecondaryContainer : ColorUtils.transparentize(Appearance.colors.colPrimaryContainer)\n"
                "                            colText: (index === grid.currentIndex || containsMouse) ? Appearance.colors.colOnPrimary : (fileModelData.filePath === activeWallpaperPath) ? Appearance.colors.colOnSecondaryContainer : Appearance.colors.colOnLayer0",
            ),
        ],
    )

    ok &= patch_file(
        ii / "modules/ii/background/Background.qml",
        [
            (
                "import QtMultimedia",
                "import QtQuick\nimport QtQuick.Layouts",
                "import QtQuick\nimport QtMultimedia\nimport QtQuick.Layouts",
            ),
            (
                "readonly property string rawWallpaperPath:",
                "        // Wallpaper\n"
                "        property bool wallpaperIsVideo: Config.options.background.wallpaperPath.endsWith(\".mp4\") || Config.options.background.wallpaperPath.endsWith(\".webm\") || Config.options.background.wallpaperPath.endsWith(\".mkv\") || Config.options.background.wallpaperPath.endsWith(\".avi\") || Config.options.background.wallpaperPath.endsWith(\".mov\")\n"
                "        property string wallpaperPath: wallpaperIsVideo ? Config.options.background.thumbnailPath : Config.options.background.wallpaperPath",
                "        // Wallpaper\n"
                "        readonly property string monitorName: modelData?.name ?? \"\"\n"
                "        readonly property var monitorCfg: (Config.options.background.perMonitor && monitorName !== \"\") ? (Config.options.background.monitors?.[monitorName] ?? null) : null\n"
                "        readonly property string rawWallpaperPath: (monitorCfg?.wallpaperPath && monitorCfg.wallpaperPath !== \"\") ? monitorCfg.wallpaperPath : Config.options.background.wallpaperPath\n"
                "        readonly property string rawThumbnailPath: (monitorCfg?.thumbnailPath && monitorCfg.thumbnailPath !== \"\") ? monitorCfg.thumbnailPath : Config.options.background.thumbnailPath\n"
                "        readonly property bool wallpaperIsGif: rawWallpaperPath.toLowerCase().endsWith(\".gif\")\n"
                "        property bool wallpaperIsVideo: /\\.(mp4|webm|mkv|avi|mov)$/i.test(rawWallpaperPath)\n"
                "        property string wallpaperPath: wallpaperIsVideo ? rawThumbnailPath : rawWallpaperPath",
            ),
            (
                "if (!bgRoot.wallpaperPath || bgRoot.wallpaperPath === \"\") return;",
                "        function updateZoomScale() {\n"
                "            getWallpaperSizeProc.path = bgRoot.wallpaperPath;\n"
                "            getWallpaperSizeProc.running = true;\n"
                "        }",
                "        function updateZoomScale() {\n"
                "            if (!bgRoot.wallpaperPath || bgRoot.wallpaperPath === \"\") return;\n"
                "            getWallpaperSizeProc.path = bgRoot.wallpaperPath;\n"
                "            getWallpaperSizeProc.running = true;\n"
                "        }",
            ),
            (
                "liveVideoLoader",
                "            // Wallpaper\n"
                "            StyledImage {\n"
                "                id: wallpaper\n"
                "                visible: opacity > 0 && !blurLoader.active\n"
                "                opacity: (status === Image.Ready && !bgRoot.wallpaperIsVideo) ? 1 : 0",
                "            // Native Live Wallpaper (Video & GIF)\n"
                "            // Teardown is two-phase: the player is first stopped and detached from its\n"
                "            // VideoOutput, and only after a short delay (liveGateTimer) the Loader destroys\n"
                "            // it, so the render thread never samples a frame sink that is being deleted.\n"
                "            Loader {\n"
                "                id: liveVideoLoader\n"
                "                anchors.fill: parent\n"
                "                readonly property bool wanted: bgRoot.wallpaperIsVideo && !bgRoot.wallpaperSafetyTriggered && bgRoot.rawWallpaperPath !== \"\"\n"
                "                property bool gate: false\n"
                "                active: gate\n"
                "                visible: active && !blurLoader.active\n"
                "                Component.onCompleted: gate = wanted\n"
                "                onWantedChanged: {\n"
                "                    if (wanted) {\n"
                "                        liveGateTimer.stop();\n"
                "                        gate = true;\n"
                "                        if (item) item.resume();\n"
                "                    } else {\n"
                "                        if (item) item.shutdown();\n"
                "                        liveGateTimer.restart();\n"
                "                    }\n"
                "                }\n"
                "                Timer {\n"
                "                    id: liveGateTimer\n"
                "                    interval: 300\n"
                "                    onTriggered: liveVideoLoader.gate = liveVideoLoader.wanted\n"
                "                }\n"
                "                sourceComponent: Item {\n"
                "                    id: liveRoot\n"
                "                    anchors.fill: parent\n"
                "                    property bool shut: false\n"
                "                    function shutdown() { shut = true; bgVideoPlayer.stop(); }\n"
                "                    function resume() { shut = false; if (bgRoot.visible) bgVideoPlayer.play(); }\n"
                "                    MediaPlayer {\n"
                "                        id: bgVideoPlayer\n"
                "                        source: (liveRoot.shut || !bgRoot.wallpaperIsVideo) ? \"\" : \"file://\" + bgRoot.rawWallpaperPath.replace(/^file:\\/\\//, \"\")\n"
                "                        loops: Config.options.background.live.loop ? MediaPlayer.Infinite : 1\n"
                "                        playbackRate: Math.max(0.1, Config.options.background.live.speed)\n"
                "                        audioOutput: AudioOutput {\n"
                "                            muted: Config.options.background.live.muted\n"
                "                            volume: Config.options.background.live.volume\n"
                "                        }\n"
                "                        videoOutput: liveRoot.shut ? null : bgVideoOut\n"
                "                        Component.onCompleted: if (bgRoot.visible && !liveRoot.shut && source.toString() !== \"\") play()\n"
                "                        onSourceChanged: {\n"
                "                            stop();\n"
                "                            if (bgRoot.visible && !liveRoot.shut && source.toString() !== \"\") play();\n"
                "                        }\n"
                "                        onMediaStatusChanged: {\n"
                "                            if (mediaStatus === MediaPlayer.LoadedMedia && bgRoot.visible && !liveRoot.shut && playbackState !== MediaPlayer.PlayingState)\n"
                "                                play();\n"
                "                        }\n"
                "                        onErrorOccurred: (error, errorString) => console.warn(\"[Background] MediaPlayer error:\", error, errorString)\n"
                "                    }\n"
                "                    Connections {\n"
                "                        target: bgRoot\n"
                "                        function onVisibleChanged() {\n"
                "                            if (liveRoot.shut) return;\n"
                "                            if (bgRoot.visible) bgVideoPlayer.play();\n"
                "                            else if (Config.options.background.live.pauseOnFullscreen) bgVideoPlayer.pause();\n"
                "                        }\n"
                "                    }\n"
                "                    VideoOutput {\n"
                "                        id: bgVideoOut\n"
                "                        width: parent.width\n"
                "                        height: parent.height\n"
                "                        x: (Config.options.background.live.position - 50) * -2\n"
                "                        fillMode: Config.options.background.live.fillMode === \"fit\" ? VideoOutput.PreserveAspectFit\n"
                "                                : Config.options.background.live.fillMode === \"stretch\" ? VideoOutput.Stretch\n"
                "                                : VideoOutput.PreserveAspectCrop\n"
                "                    }\n"
                "                }\n"
                "            }\n"
                "\n"
                "            AnimatedImage {\n"
                "                id: liveGifWallpaper\n"
                "                anchors.fill: parent\n"
                "                visible: bgRoot.wallpaperIsGif && !bgRoot.wallpaperSafetyTriggered && !blurLoader.active\n"
                "                source: visible ? (\"file://\" + bgRoot.rawWallpaperPath.replace(/^file:\\/\\//, \"\")) : \"\"\n"
                "                fillMode: Image.PreserveAspectCrop\n"
                "                playing: visible && bgRoot.visible\n"
                "                asynchronous: true\n"
                "            }\n\n"
                "            // Wallpaper\n"
                "            StyledImage {\n"
                "                id: wallpaper\n"
                "                visible: opacity > 0 && !blurLoader.active\n"
                "                opacity: (status === Image.Ready && !bgRoot.wallpaperIsVideo && !bgRoot.wallpaperIsGif) ? 1 : 0",
            ),
            (
                "liveGateTimer",
                '            // Native Live Wallpaper (Video & GIF)\n            Loader {\n                id: liveVideoLoader\n                anchors.fill: parent\n                active: bgRoot.wallpaperIsVideo && !bgRoot.wallpaperSafetyTriggered && bgRoot.rawWallpaperPath !== ""\n                visible: active && !blurLoader.active\n                sourceComponent: Item {\n                    anchors.fill: parent\n                    MediaPlayer {\n                        id: bgVideoPlayer\n                        source: "file://" + bgRoot.rawWallpaperPath.replace(/^file:\\/\\//, "")\n                        loops: Config.options.background.live.loop ? MediaPlayer.Infinite : 1\n                        playbackRate: Config.options.background.live.speed\n                        audioOutput: AudioOutput {\n                            muted: Config.options.background.live.muted\n                            volume: Config.options.background.live.volume\n                        }\n                        videoOutput: bgVideoOut\n                        Component.onCompleted: if (bgRoot.visible) play()\n                        onSourceChanged: {\n                            stop();\n                            if (bgRoot.visible) play();\n                        }\n                        onMediaStatusChanged: {\n                            if (mediaStatus === MediaPlayer.LoadedMedia && bgRoot.visible && playbackState !== MediaPlayer.PlayingState)\n                                play();\n                        }\n                        onErrorOccurred: (error, errorString) => console.warn("[Background] MediaPlayer error:", error, errorString)\n                    }\n                    Connections {\n                        target: bgRoot\n                        function onVisibleChanged() {\n                            if (bgRoot.visible) bgVideoPlayer.play();\n                            else if (Config.options.background.live.pauseOnFullscreen) bgVideoPlayer.pause();\n                        }\n                    }\n                    VideoOutput {\n                        id: bgVideoOut\n                        width: parent.width\n                        height: parent.height\n                        x: (Config.options.background.live.position - 50) * -2\n                        fillMode: Config.options.background.live.fillMode === "fit" ? VideoOutput.PreserveAspectFit\n                                : Config.options.background.live.fillMode === "stretch" ? VideoOutput.Stretch\n                                : VideoOutput.PreserveAspectCrop\n                    }\n                }\n            }\n\n',
                '            // Native Live Wallpaper (Video & GIF)\n            // Teardown is two-phase: the player is first stopped and detached from its\n            // VideoOutput, and only after a short delay (liveGateTimer) the Loader destroys\n            // it, so the render thread never samples a frame sink that is being deleted.\n            Loader {\n                id: liveVideoLoader\n                anchors.fill: parent\n                readonly property bool wanted: bgRoot.wallpaperIsVideo && !bgRoot.wallpaperSafetyTriggered && bgRoot.rawWallpaperPath !== ""\n                property bool gate: false\n                active: gate\n                visible: active && !blurLoader.active\n                Component.onCompleted: gate = wanted\n                onWantedChanged: {\n                    if (wanted) {\n                        liveGateTimer.stop();\n                        gate = true;\n                        if (item) item.resume();\n                    } else {\n                        if (item) item.shutdown();\n                        liveGateTimer.restart();\n                    }\n                }\n                Timer {\n                    id: liveGateTimer\n                    interval: 300\n                    onTriggered: liveVideoLoader.gate = liveVideoLoader.wanted\n                }\n                sourceComponent: Item {\n                    id: liveRoot\n                    anchors.fill: parent\n                    property bool shut: false\n                    function shutdown() { shut = true; bgVideoPlayer.stop(); }\n                    function resume() { shut = false; if (bgRoot.visible) bgVideoPlayer.play(); }\n                    MediaPlayer {\n                        id: bgVideoPlayer\n                        source: (liveRoot.shut || !bgRoot.wallpaperIsVideo) ? "" : "file://" + bgRoot.rawWallpaperPath.replace(/^file:\\/\\//, "")\n                        loops: Config.options.background.live.loop ? MediaPlayer.Infinite : 1\n                        playbackRate: Math.max(0.1, Config.options.background.live.speed)\n                        audioOutput: AudioOutput {\n                            muted: Config.options.background.live.muted\n                            volume: Config.options.background.live.volume\n                        }\n                        videoOutput: liveRoot.shut ? null : bgVideoOut\n                        Component.onCompleted: if (bgRoot.visible && !liveRoot.shut && source.toString() !== "") play()\n                        onSourceChanged: {\n                            stop();\n                            if (bgRoot.visible && !liveRoot.shut && source.toString() !== "") play();\n                        }\n                        onMediaStatusChanged: {\n                            if (mediaStatus === MediaPlayer.LoadedMedia && bgRoot.visible && !liveRoot.shut && playbackState !== MediaPlayer.PlayingState)\n                                play();\n                        }\n                        onErrorOccurred: (error, errorString) => console.warn("[Background] MediaPlayer error:", error, errorString)\n                    }\n                    Connections {\n                        target: bgRoot\n                        function onVisibleChanged() {\n                            if (liveRoot.shut) return;\n                            if (bgRoot.visible) bgVideoPlayer.play();\n                            else if (Config.options.background.live.pauseOnFullscreen) bgVideoPlayer.pause();\n                        }\n                    }\n                    VideoOutput {\n                        id: bgVideoOut\n                        width: parent.width\n                        height: parent.height\n                        x: (Config.options.background.live.position - 50) * -2\n                        fillMode: Config.options.background.live.fillMode === "fit" ? VideoOutput.PreserveAspectFit\n                                : Config.options.background.live.fillMode === "stretch" ? VideoOutput.Stretch\n                                : VideoOutput.PreserveAspectCrop\n                    }\n                }\n            }\n\n',
            ),
        ],
    )

    ok &= patch_file(
        ii / "scripts/colors/switchwall.sh",
        [
            # One-step path: pristine upstream switchwall.sh -> final state (optional; skipped on already
            # patched / older intermediate installs, which continue with the incremental edits below).
            (
                'check_and_prompt_upscale() {\n    local img="$1"\n    local pm sm\n    pm=$(jq -r \'.background.perMonitor // false\' "$SHELL_CONFIG_FILE" 2>/dev/null)\n    sm=$(get_target_monitor)\n    if [[ "$pm" == "true" && -n "$sm" ]]; then\n        min_width_desired="$(hyprctl monitors -j | jq -r --arg m "$sm" \'(.[] | select(.name == $m) | .width) // ([.[].width] | max)\' | xargs)"\n        min_height_desired="$(hyprctl monitors -j | jq -r --arg m "$sm" \'(.[] | select(.name == $m) | .height) // ([.[].height] | max)\' | xargs)"\n    else\n        min_width_desired="$(hyprctl monitors -j | jq \'([.[].width] | max)\' | xargs)" # max monitor width\n        min_height_desired="$(hyprctl monitors -j | jq \'([.[].height] | max)\' | xargs)" # max monitor height\n    fi\n\n    if command -v identify &>/dev/null && [ -f "$img" ]; then\n',
                'check_and_prompt_upscale() {\n    local img="$1"\n    min_width_desired="$(hyprctl monitors -j | jq \'([.[].width] | max)\' | xargs)" # max monitor width\n    min_height_desired="$(hyprctl monitors -j | jq \'([.[].height] | max)\' | xargs)" # max monitor height\n\n    if command -v identify &>/dev/null && [ -f "$img" ]; then\n',
                'check_and_prompt_upscale() {\n    local img="$1"\n    local pm sm\n    pm=$(jq -r \'.background.perMonitor // false\' "$SHELL_CONFIG_FILE" 2>/dev/null)\n    sm=$(get_target_monitor)\n    if [[ "$pm" == "true" && -n "$sm" ]]; then\n        min_width_desired="$(hyprctl monitors -j | jq -r --arg m "$sm" \'(.[] | select(.name == $m) | .width) // ([.[].width] | max)\' | xargs)"\n        min_height_desired="$(hyprctl monitors -j | jq -r --arg m "$sm" \'(.[] | select(.name == $m) | .height) // ([.[].height] | max)\' | xargs)"\n    else\n        min_width_desired="$(hyprctl monitors -j | jq \'([.[].width] | max)\' | xargs)" # max monitor width\n        min_height_desired="$(hyprctl monitors -j | jq \'([.[].height] | max)\' | xargs)" # max monitor height\n    fi\n\n    if command -v identify &>/dev/null && [ -f "$img" ]; then\n',
                "optional",
            ),
            (
                '\nkill_existing_mpvpaper() {\n    pkill -x mpvpaper || true  # exact name: -f would also kill ffmpeg/editors whose argv merely mentions mpvpaper\n}\n\n',
                '\nkill_existing_mpvpaper() {\n    pkill -f -9 mpvpaper || true\n}\n\n',
                '\nkill_existing_mpvpaper() {\n    pkill -x mpvpaper || true  # exact name: -f would also kill ffmpeg/editors whose argv merely mentions mpvpaper\n}\n\n',
                "optional",
            ),
            (
                '}\n\nget_primary_monitor() {\n    local pref\n    pref=$(jq -r \'.bar.workspaces.defaultMonitor // ""\' "$SHELL_CONFIG_FILE" 2>/dev/null || echo "")\n    if [[ -n "$pref" ]] && hyprctl monitors -j 2>/dev/null | jq -e --arg m "$pref" \'any(.[]; .name == $m)\' >/dev/null 2>&1; then\n        echo "$pref"\n        return\n    fi\n    hyprctl monitors -j 2>/dev/null | jq -r \'max_by(.width * .height) | .name // ""\' 2>/dev/null || echo ""\n}\n\nget_target_monitor() {\n    if [[ -n "${monitor_flag:-}" ]]; then\n        echo "$monitor_flag"\n    elif [[ -n "${II_TARGET_MONITOR:-}" ]]; then\n        echo "$II_TARGET_MONITOR"\n    else\n        hyprctl monitors -j 2>/dev/null | jq -r \'(.[] | select(.focused) | .name) // ""\' 2>/dev/null || echo ""\n    fi\n}\n\nwrite_config_preserve_inode() {\n    cat "$SHELL_CONFIG_FILE.tmp" > "$SHELL_CONFIG_FILE" && rm -f "$SHELL_CONFIG_FILE.tmp"\n}\n\nset_wallpaper_path() {\n    local path="$1"\n    if [ -f "$SHELL_CONFIG_FILE" ]; then\n        local per_mon sel_mon primary_mon\n        per_mon=$(jq -r \'.background.perMonitor // false\' "$SHELL_CONFIG_FILE" 2>/dev/null)\n        sel_mon=$(get_target_monitor)\n        primary_mon=$(get_primary_monitor)\n        if [[ "$per_mon" == "true" && -n "$sel_mon" ]]; then\n            if [[ "$sel_mon" == "$primary_mon" || -z "$primary_mon" ]]; then\n                jq --arg mon "$sel_mon" --arg path "$path" \'.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {"wallpaperPath": $path}) | .background.wallpaperPath = $path\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n            else\n                jq --arg mon "$sel_mon" --arg path "$path" \'.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {"wallpaperPath": $path}) | if (.background.wallpaperPath // "") == "" then .background.wallpaperPath = $path else . end\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n            fi\n        else\n            jq --arg path "$path" \'.background.wallpaperPath = $path\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n        fi\n    fi\n}\n',
                '}\n\nset_wallpaper_path() {\n    local path="$1"\n    if [ -f "$SHELL_CONFIG_FILE" ]; then\n        jq --arg path "$path" \'.background.wallpaperPath = $path\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && mv "$SHELL_CONFIG_FILE.tmp" "$SHELL_CONFIG_FILE"\n    fi\n}\n',
                '}\n\nget_primary_monitor() {\n    local pref\n    pref=$(jq -r \'.bar.workspaces.defaultMonitor // ""\' "$SHELL_CONFIG_FILE" 2>/dev/null || echo "")\n    if [[ -n "$pref" ]] && hyprctl monitors -j 2>/dev/null | jq -e --arg m "$pref" \'any(.[]; .name == $m)\' >/dev/null 2>&1; then\n        echo "$pref"\n        return\n    fi\n    hyprctl monitors -j 2>/dev/null | jq -r \'max_by(.width * .height) | .name // ""\' 2>/dev/null || echo ""\n}\n\nget_target_monitor() {\n    if [[ -n "${monitor_flag:-}" ]]; then\n        echo "$monitor_flag"\n    elif [[ -n "${II_TARGET_MONITOR:-}" ]]; then\n        echo "$II_TARGET_MONITOR"\n    else\n        hyprctl monitors -j 2>/dev/null | jq -r \'(.[] | select(.focused) | .name) // ""\' 2>/dev/null || echo ""\n    fi\n}\n\nwrite_config_preserve_inode() {\n    cat "$SHELL_CONFIG_FILE.tmp" > "$SHELL_CONFIG_FILE" && rm -f "$SHELL_CONFIG_FILE.tmp"\n}\n\nset_wallpaper_path() {\n    local path="$1"\n    if [ -f "$SHELL_CONFIG_FILE" ]; then\n        local per_mon sel_mon primary_mon\n        per_mon=$(jq -r \'.background.perMonitor // false\' "$SHELL_CONFIG_FILE" 2>/dev/null)\n        sel_mon=$(get_target_monitor)\n        primary_mon=$(get_primary_monitor)\n        if [[ "$per_mon" == "true" && -n "$sel_mon" ]]; then\n            if [[ "$sel_mon" == "$primary_mon" || -z "$primary_mon" ]]; then\n                jq --arg mon "$sel_mon" --arg path "$path" \'.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {"wallpaperPath": $path}) | .background.wallpaperPath = $path\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n            else\n                jq --arg mon "$sel_mon" --arg path "$path" \'.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {"wallpaperPath": $path}) | if (.background.wallpaperPath // "") == "" then .background.wallpaperPath = $path else . end\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n            fi\n        else\n            jq --arg path "$path" \'.background.wallpaperPath = $path\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n        fi\n    fi\n}\n',
                "optional",
            ),
            (
                '    local path="$1"\n    if [ -f "$SHELL_CONFIG_FILE" ]; then\n        local per_mon sel_mon primary_mon\n        per_mon=$(jq -r \'.background.perMonitor // false\' "$SHELL_CONFIG_FILE" 2>/dev/null)\n        sel_mon=$(get_target_monitor)\n        primary_mon=$(get_primary_monitor)\n        if [[ "$per_mon" == "true" && -n "$sel_mon" ]]; then\n            if [[ "$sel_mon" == "$primary_mon" || -z "$primary_mon" ]]; then\n                jq --arg mon "$sel_mon" --arg path "$path" \'.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {"thumbnailPath": $path}) | .background.thumbnailPath = $path\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n            else\n                jq --arg mon "$sel_mon" --arg path "$path" \'.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {"thumbnailPath": $path}) | if (.background.thumbnailPath // "") == "" then .background.thumbnailPath = $path else . end\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n            fi\n        else\n            jq --arg path "$path" \'.background.thumbnailPath = $path\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n        fi\n    fi\n}\n',
                '    local path="$1"\n    if [ -f "$SHELL_CONFIG_FILE" ]; then\n        jq --arg path "$path" \'.background.thumbnailPath = $path\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && mv "$SHELL_CONFIG_FILE.tmp" "$SHELL_CONFIG_FILE"\n    fi\n}\n',
                '    local path="$1"\n    if [ -f "$SHELL_CONFIG_FILE" ]; then\n        local per_mon sel_mon primary_mon\n        per_mon=$(jq -r \'.background.perMonitor // false\' "$SHELL_CONFIG_FILE" 2>/dev/null)\n        sel_mon=$(get_target_monitor)\n        primary_mon=$(get_primary_monitor)\n        if [[ "$per_mon" == "true" && -n "$sel_mon" ]]; then\n            if [[ "$sel_mon" == "$primary_mon" || -z "$primary_mon" ]]; then\n                jq --arg mon "$sel_mon" --arg path "$path" \'.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {"thumbnailPath": $path}) | .background.thumbnailPath = $path\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n            else\n                jq --arg mon "$sel_mon" --arg path "$path" \'.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {"thumbnailPath": $path}) | if (.background.thumbnailPath // "") == "" then .background.thumbnailPath = $path else . end\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n            fi\n        else\n            jq --arg path "$path" \'.background.thumbnailPath = $path\' "$SHELL_CONFIG_FILE" > "$SHELL_CONFIG_FILE.tmp" && write_config_preserve_inode\n        fi\n    fi\n}\n',
                "optional",
            ),
            (
                '            mkdir -p "$THUMBNAIL_DIR"\n\n            # native live video wallpaper (no mpvpaper)\n            if ! command -v ffmpeg &> /dev/null; then\n                notify-send -a "Wallpaper switcher" -c "im.error" "Can\'t switch to video wallpaper" "Missing dependency: ffmpeg"\n                exit 0\n            fi\n\n            # Set wallpaper path (Quickshell Background.qml plays video natively via QtMultimedia)\n            set_wallpaper_path "$imgpath"\n\n            # Extract first frame for color generation\n',
                '            mkdir -p "$THUMBNAIL_DIR"\n\n            missing_deps=()\n            if ! command -v mpvpaper &> /dev/null; then\n                missing_deps+=("mpvpaper")\n            fi\n            if ! command -v ffmpeg &> /dev/null; then\n                missing_deps+=("ffmpeg")\n            fi\n            if [ ${#missing_deps[@]} -gt 0 ]; then\n                echo "Missing deps: ${missing_deps[*]}"\n                echo "Arch: sudo pacman -S ${missing_deps[*]}"\n                action=$(notify-send \\\n                    -a "Wallpaper switcher" \\\n                    -c "im.error" \\\n                    -A "install_arch=Install (Arch)" \\\n                    "Can\'t switch to video wallpaper" \\\n                    "Missing dependencies: ${missing_deps[*]}")\n                if [[ "$action" == "install_arch" ]]; then\n                    kitty -1 sudo pacman -S "${missing_deps[*]}"\n                    if command -v mpvpaper &>/dev/null && command -v ffmpeg &>/dev/null; then\n                        notify-send \'Wallpaper switcher\' \'Alright, try again!\' -a "Wallpaper switcher"\n                    fi\n                fi\n                exit 0\n            fi\n\n            # Set wallpaper path\n            set_wallpaper_path "$imgpath"\n\n            # Set video wallpaper\n            local video_path="$imgpath"\n            monitors=$(hyprctl monitors -j | jq -r \'.[] | .name\')\n            for monitor in $monitors; do\n                mpvpaper -o "$VIDEO_OPTS" "$monitor" "$video_path" &\n                sleep 0.1\n            done\n\n            # Extract first frame for color generation\n',
                '            mkdir -p "$THUMBNAIL_DIR"\n\n            # native live video wallpaper (no mpvpaper)\n            if ! command -v ffmpeg &> /dev/null; then\n                notify-send -a "Wallpaper switcher" -c "im.error" "Can\'t switch to video wallpaper" "Missing dependency: ffmpeg"\n                exit 0\n            fi\n\n            # Set wallpaper path (Quickshell Background.qml plays video natively via QtMultimedia)\n            set_wallpaper_path "$imgpath"\n\n            # Extract first frame for color generation\n',
                "optional",
            ),
            (
                '    fi\n\n    if [ -f "$SHELL_CONFIG_FILE" ]; then\n        local pm sm prim\n        pm=$(jq -r \'.background.perMonitor // false\' "$SHELL_CONFIG_FILE" 2>/dev/null)\n        sm=$(get_target_monitor)\n        prim=$(get_primary_monitor)\n        # skip secondary matugen so only primary monitor changes global theme\n        if [[ "$pm" == "true" && -n "$sm" && "$sm" != "$prim" && "$noswitch_flag" != "1" ]]; then\n            return 0\n        fi\n    fi\n\n    matugen "${matugen_args[@]}"\n    source "$(eval echo $ILLOGICAL_IMPULSE_VIRTUAL_ENV)/bin/activate"\n',
                '    fi\n\n    matugen "${matugen_args[@]}"\n    source "$(eval echo $ILLOGICAL_IMPULSE_VIRTUAL_ENV)/bin/activate"\n',
                '    fi\n\n    if [ -f "$SHELL_CONFIG_FILE" ]; then\n        local pm sm prim\n        pm=$(jq -r \'.background.perMonitor // false\' "$SHELL_CONFIG_FILE" 2>/dev/null)\n        sm=$(get_target_monitor)\n        prim=$(get_primary_monitor)\n        # skip secondary matugen so only primary monitor changes global theme\n        if [[ "$pm" == "true" && -n "$sm" && "$sm" != "$prim" && "$noswitch_flag" != "1" ]]; then\n            return 0\n        fi\n    fi\n\n    matugen "${matugen_args[@]}"\n    source "$(eval echo $ILLOGICAL_IMPULSE_VIRTUAL_ENV)/bin/activate"\n',
                "optional",
            ),
            (
                '    color=""\n    noswitch_flag=""\n    monitor_flag=""\n\n    get_type_from_config() {\n',
                '    color=""\n    noswitch_flag=""\n\n    get_type_from_config() {\n',
                '    color=""\n    noswitch_flag=""\n    monitor_flag=""\n\n    get_type_from_config() {\n',
                "optional",
            ),
            (
                '            --image)\n                imgpath="$2"\n                shift 2\n                ;;\n            --monitor)\n                monitor_flag="$2"\n                shift 2\n                ;;\n',
                '            --image)\n                imgpath="$2"\n                shift 2\n                ;;\n',
                '            --image)\n                imgpath="$2"\n                shift 2\n                ;;\n            --monitor)\n                monitor_flag="$2"\n                shift 2\n                ;;\n',
                "optional",
            ),
            (
                'select(.name == $m) | .width',
                "check_and_prompt_upscale() {\n"
                "    local img=\"$1\"\n"
                "    min_width_desired=\"$(hyprctl monitors -j | jq '([.[].width] | max)' | xargs)\" # max monitor width\n"
                "    min_height_desired=\"$(hyprctl monitors -j | jq '([.[].height] | max)' | xargs)\" # max monitor height",
                "check_and_prompt_upscale() {\n"
                "    local img=\"$1\"\n"
                "    local pm sm\n"
                "    pm=$(jq -r '.background.perMonitor // false' \"$SHELL_CONFIG_FILE\" 2>/dev/null)\n"
                "    sm=$(jq -r '.background.selectedMonitor // \"\"' \"$SHELL_CONFIG_FILE\" 2>/dev/null)\n"
                "    if [[ \"$pm\" == \"true\" && -n \"$sm\" ]]; then\n"
                "        min_width_desired=\"$(hyprctl monitors -j | jq -r --arg m \"$sm\" '(.[] | select(.name == $m) | .width) // ([.[].width] | max)' | xargs)\"\n"
                "        min_height_desired=\"$(hyprctl monitors -j | jq -r --arg m \"$sm\" '(.[] | select(.name == $m) | .height) // ([.[].height] | max)' | xargs)\"\n"
                "    else\n"
                "        min_width_desired=\"$(hyprctl monitors -j | jq '([.[].width] | max)' | xargs)\" # max monitor width\n"
                "        min_height_desired=\"$(hyprctl monitors -j | jq '([.[].height] | max)' | xargs)\" # max monitor height\n"
                "    fi",
            ),
            (
                "get_target_monitor()",
                "get_primary_monitor() {\n"
                "    local pref\n"
                "    pref=$(jq -r '.bar.workspaces.defaultMonitor // \"\"' \"$SHELL_CONFIG_FILE\" 2>/dev/null || echo \"\")\n"
                "    if [[ -n \"$pref\" ]] && hyprctl monitors -j 2>/dev/null | jq -e --arg m \"$pref\" 'any(.[]; .name == $m)' >/dev/null 2>&1; then\n"
                "        echo \"$pref\"\n"
                "        return\n"
                "    fi\n"
                "    hyprctl monitors -j 2>/dev/null | jq -r 'max_by(.width * .height) | .name // \"\"' 2>/dev/null || echo \"\"\n"
                "}\n\n"
                "set_wallpaper_path() {\n"
                "    local path=\"$1\"\n"
                "    if [ -f \"$SHELL_CONFIG_FILE\" ]; then\n"
                "        local per_mon sel_mon primary_mon\n"
                "        per_mon=$(jq -r '.background.perMonitor // false' \"$SHELL_CONFIG_FILE\" 2>/dev/null)\n"
                "        sel_mon=$(jq -r '.background.selectedMonitor // \"\"' \"$SHELL_CONFIG_FILE\" 2>/dev/null)\n"
                "        primary_mon=$(get_primary_monitor)\n"
                "        if [[ \"$per_mon\" == \"true\" && -n \"$sel_mon\" ]]; then\n"
                "            if [[ \"$sel_mon\" == \"$primary_mon\" || -z \"$primary_mon\" ]]; then\n"
                "                jq --arg mon \"$sel_mon\" --arg path \"$path\" '.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {\"wallpaperPath\": $path}) | .background.wallpaperPath = $path' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && mv \"$SHELL_CONFIG_FILE.tmp\" \"$SHELL_CONFIG_FILE\"\n"
                "            else\n"
                "                jq --arg mon \"$sel_mon\" --arg path \"$path\" '.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {\"wallpaperPath\": $path}) | if (.background.wallpaperPath // \"\") == \"\" then .background.wallpaperPath = $path else . end' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && mv \"$SHELL_CONFIG_FILE.tmp\" \"$SHELL_CONFIG_FILE\"\n"
                "            fi\n"
                "        else\n"
                "            jq --arg path \"$path\" '.background.wallpaperPath = $path' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && mv \"$SHELL_CONFIG_FILE.tmp\" \"$SHELL_CONFIG_FILE\"\n"
                "        fi\n"
                "    fi\n"
                "}\n\n"
                "set_thumbnail_path() {\n"
                "    local path=\"$1\"\n"
                "    if [ -f \"$SHELL_CONFIG_FILE\" ]; then\n"
                "        local per_mon sel_mon primary_mon\n"
                "        per_mon=$(jq -r '.background.perMonitor // false' \"$SHELL_CONFIG_FILE\" 2>/dev/null)\n"
                "        sel_mon=$(jq -r '.background.selectedMonitor // \"\"' \"$SHELL_CONFIG_FILE\" 2>/dev/null)\n"
                "        primary_mon=$(get_primary_monitor)\n"
                "        if [[ \"$per_mon\" == \"true\" && -n \"$sel_mon\" ]]; then\n"
                "            if [[ \"$sel_mon\" == \"$primary_mon\" || -z \"$primary_mon\" ]]; then\n"
                "                jq --arg mon \"$sel_mon\" --arg path \"$path\" '.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {\"thumbnailPath\": $path}) | .background.thumbnailPath = $path' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && mv \"$SHELL_CONFIG_FILE.tmp\" \"$SHELL_CONFIG_FILE\"\n"
                "            else\n"
                "                jq --arg mon \"$sel_mon\" --arg path \"$path\" '.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {\"thumbnailPath\": $path}) | if (.background.thumbnailPath // \"\") == \"\" then .background.thumbnailPath = $path else . end' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && mv \"$SHELL_CONFIG_FILE.tmp\" \"$SHELL_CONFIG_FILE\"\n"
                "            fi\n"
                "        else\n"
                "            jq --arg path \"$path\" '.background.thumbnailPath = $path' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && mv \"$SHELL_CONFIG_FILE.tmp\" \"$SHELL_CONFIG_FILE\"\n"
                "        fi\n"
                "    fi\n"
                "}",
                "get_primary_monitor() {\n"
                "    local pref\n"
                "    pref=$(jq -r '.bar.workspaces.defaultMonitor // \"\"' \"$SHELL_CONFIG_FILE\" 2>/dev/null || echo \"\")\n"
                "    if [[ -n \"$pref\" ]] && hyprctl monitors -j 2>/dev/null | jq -e --arg m \"$pref\" 'any(.[]; .name == $m)' >/dev/null 2>&1; then\n"
                "        echo \"$pref\"\n"
                "        return\n"
                "    fi\n"
                "    hyprctl monitors -j 2>/dev/null | jq -r 'max_by(.width * .height) | .name // \"\"' 2>/dev/null || echo \"\"\n"
                "}\n\n"
                "get_target_monitor() {\n"
                "    if [[ -n \"${monitor_flag:-}\" ]]; then\n"
                "        echo \"$monitor_flag\"\n"
                "    elif [[ -n \"${II_TARGET_MONITOR:-}\" ]]; then\n"
                "        echo \"$II_TARGET_MONITOR\"\n"
                "    else\n"
                "        hyprctl monitors -j 2>/dev/null | jq -r '(.[] | select(.focused) | .name) // \"\"' 2>/dev/null || echo \"\"\n"
                "    fi\n"
                "}\n\n"
                "write_config_preserve_inode() {\n"
                "    cat \"$SHELL_CONFIG_FILE.tmp\" > \"$SHELL_CONFIG_FILE\" && rm -f \"$SHELL_CONFIG_FILE.tmp\"\n"
                "}\n\n"
                "set_wallpaper_path() {\n"
                "    local path=\"$1\"\n"
                "    if [ -f \"$SHELL_CONFIG_FILE\" ]; then\n"
                "        local per_mon sel_mon primary_mon\n"
                "        per_mon=$(jq -r '.background.perMonitor // false' \"$SHELL_CONFIG_FILE\" 2>/dev/null)\n"
                "        sel_mon=$(get_target_monitor)\n"
                "        primary_mon=$(get_primary_monitor)\n"
                "        if [[ \"$per_mon\" == \"true\" && -n \"$sel_mon\" ]]; then\n"
                "            if [[ \"$sel_mon\" == \"$primary_mon\" || -z \"$primary_mon\" ]]; then\n"
                "                jq --arg mon \"$sel_mon\" --arg path \"$path\" '.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {\"wallpaperPath\": $path}) | .background.wallpaperPath = $path' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && write_config_preserve_inode\n"
                "            else\n"
                "                jq --arg mon \"$sel_mon\" --arg path \"$path\" '.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {\"wallpaperPath\": $path}) | if (.background.wallpaperPath // \"\") == \"\" then .background.wallpaperPath = $path else . end' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && write_config_preserve_inode\n"
                "            fi\n"
                "        else\n"
                "            jq --arg path \"$path\" '.background.wallpaperPath = $path' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && write_config_preserve_inode\n"
                "        fi\n"
                "    fi\n"
                "}\n\n"
                "set_thumbnail_path() {\n"
                "    local path=\"$1\"\n"
                "    if [ -f \"$SHELL_CONFIG_FILE\" ]; then\n"
                "        local per_mon sel_mon primary_mon\n"
                "        per_mon=$(jq -r '.background.perMonitor // false' \"$SHELL_CONFIG_FILE\" 2>/dev/null)\n"
                "        sel_mon=$(get_target_monitor)\n"
                "        primary_mon=$(get_primary_monitor)\n"
                "        if [[ \"$per_mon\" == \"true\" && -n \"$sel_mon\" ]]; then\n"
                "            if [[ \"$sel_mon\" == \"$primary_mon\" || -z \"$primary_mon\" ]]; then\n"
                "                jq --arg mon \"$sel_mon\" --arg path \"$path\" '.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {\"thumbnailPath\": $path}) | .background.thumbnailPath = $path' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && write_config_preserve_inode\n"
                "            else\n"
                "                jq --arg mon \"$sel_mon\" --arg path \"$path\" '.background.monitors = (.background.monitors // {}) | .background.monitors[$mon] = ((.background.monitors[$mon] // {}) + {\"thumbnailPath\": $path}) | if (.background.thumbnailPath // \"\") == \"\" then .background.thumbnailPath = $path else . end' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && write_config_preserve_inode\n"
                "            fi\n"
                "        else\n"
                "            jq --arg path \"$path\" '.background.thumbnailPath = $path' \"$SHELL_CONFIG_FILE\" > \"$SHELL_CONFIG_FILE.tmp\" && write_config_preserve_inode\n"
                "        fi\n"
                "    fi\n"
                "}",
            ),
            (
                "sm=$(get_target_monitor)\n    if [[ \"$pm\" == \"true\" && -n \"$sm\" ]]; then\n        min_width_desired",
                "    sm=$(jq -r '.background.selectedMonitor // \"\"' \"$SHELL_CONFIG_FILE\" 2>/dev/null)",
                "    sm=$(get_target_monitor)",
            ),
            (
                "sm=$(get_target_monitor)\n        prim=$(get_primary_monitor)",
                "        sm=$(jq -r '.background.selectedMonitor // \"\"' \"$SHELL_CONFIG_FILE\" 2>/dev/null)\n        prim=$(get_primary_monitor)",
                "        sm=$(get_target_monitor)\n        prim=$(get_primary_monitor)",
            ),
            (
                "--monitor)",
                "    noswitch_flag=\"\"\n",
                "    noswitch_flag=\"\"\n    monitor_flag=\"\"\n",
            ),
            (
                "monitor_flag=\"$2\"",
                "            --noswitch)\n",
                "            --monitor)\n"
                "                monitor_flag=\"$2\"\n"
                "                shift 2\n"
                "                ;;\n"
                "            --noswitch)\n",
            ),
            (
                "imgpath=$(jq -r '.background.wallpaperPath'",
                "                imgpath=$(jq -r 'if (.background.perMonitor // false) and ((.background.selectedMonitor // \"\") != \"\") then (.background.monitors[.background.selectedMonitor].wallpaperPath // .background.wallpaperPath) else .background.wallpaperPath end' \"$SHELL_CONFIG_FILE\" 2>/dev/null || echo \"\")",
                "                imgpath=$(jq -r '.background.wallpaperPath' \"$SHELL_CONFIG_FILE\" 2>/dev/null || echo \"\")",
            ),
            (
                "native live video wallpaper (no mpvpaper)",
                "            missing_deps=()\n"
                "            if ! command -v mpvpaper &> /dev/null; then\n"
                "                missing_deps+=(\"mpvpaper\")\n"
                "            fi\n"
                "            if ! command -v ffmpeg &> /dev/null; then\n"
                "                missing_deps+=(\"ffmpeg\")\n"
                "            fi\n"
                "            if [ ${#missing_deps[@]} -gt 0 ]; then\n"
                "                echo \"Missing deps: ${missing_deps[*]}\"\n"
                "                echo \"Arch: sudo pacman -S ${missing_deps[*]}\"\n"
                "                action=$(notify-send \\\n"
                "                    -a \"Wallpaper switcher\" \\\n"
                "                    -c \"im.error\" \\\n"
                "                    -A \"install_arch=Install (Arch)\" \\\n"
                "                    \"Can't switch to video wallpaper\" \\\n"
                "                    \"Missing dependencies: ${missing_deps[*]}\")\n"
                "                if [[ \"$action\" == \"install_arch\" ]]; then\n"
                "                    kitty -1 sudo pacman -S \"${missing_deps[*]}\"\n"
                "                    if command -v mpvpaper &>/dev/null && command -v ffmpeg &>/dev/null; then\n"
                "                        notify-send 'Wallpaper switcher' 'Alright, try again!' -a \"Wallpaper switcher\"\n"
                "                    fi\n"
                "                fi\n"
                "                exit 0\n"
                "            fi\n\n"
                "            # Set wallpaper path\n"
                "            set_wallpaper_path \"$imgpath\"\n\n"
                "            # Set video wallpaper\n"
                "            local video_path=\"$imgpath\"\n"
                "            monitors=$(hyprctl monitors -j | jq -r '.[] | .name')\n"
                "            for monitor in $monitors; do\n"
                "                mpvpaper -o \"$VIDEO_OPTS\" \"$monitor\" \"$video_path\" &\n"
                "                sleep 0.1\n"
                "            done",
                "            # native live video wallpaper (no mpvpaper)\n"
                "            if ! command -v ffmpeg &> /dev/null; then\n"
                "                notify-send -a \"Wallpaper switcher\" -c \"im.error\" \"Can't switch to video wallpaper\" \"Missing dependency: ffmpeg\"\n"
                "                exit 0\n"
                "            fi\n\n"
                "            # Set wallpaper path (Quickshell Background.qml plays video natively via QtMultimedia)\n"
                "            set_wallpaper_path \"$imgpath\"",
            ),
            (
                "skip secondary matugen",
                "    matugen \"${matugen_args[@]}\"\n"
                "    source \"$(eval echo $ILLOGICAL_IMPULSE_VIRTUAL_ENV)/bin/activate\"\n"
                "    python3 \"$SCRIPT_DIR/generate_colors_material.py\" \"${generate_colors_material_args[@]}\" \\\n"
                "        > \"$STATE_DIR\"/user/generated/material_colors.scss\n"
                "    deactivate\n"
                "    \"$SCRIPT_DIR\"/applycolor.sh",
                "    if [ -f \"$SHELL_CONFIG_FILE\" ]; then\n"
                "        local pm sm prim\n"
                "        pm=$(jq -r '.background.perMonitor // false' \"$SHELL_CONFIG_FILE\" 2>/dev/null)\n"
                "        sm=$(get_target_monitor)\n"
                "        prim=$(get_primary_monitor)\n"
                "        # skip secondary matugen so only primary monitor changes global theme\n"
                "        if [[ \"$pm\" == \"true\" && -n \"$sm\" && \"$sm\" != \"$prim\" && \"$noswitch_flag\" != \"1\" ]]; then\n"
                "            return 0\n"
                "        fi\n"
                "    fi\n\n"
                "    matugen \"${matugen_args[@]}\"\n"
                "    source \"$(eval echo $ILLOGICAL_IMPULSE_VIRTUAL_ENV)/bin/activate\"\n"
                "    python3 \"$SCRIPT_DIR/generate_colors_material.py\" \"${generate_colors_material_args[@]}\" \\\n"
                "        > \"$STATE_DIR\"/user/generated/material_colors.scss\n"
                "    deactivate\n"
                "    \"$SCRIPT_DIR\"/applycolor.sh",
            ),
            (
                "pkill -x mpvpaper || true",
                "    pkill -f -9 mpvpaper || true",
                "    pkill -x mpvpaper || true  # exact name: -f would also kill ffmpeg/editors whose argv merely mentions mpvpaper",
            ),
            (
                "# native live wallpaper: no mpvpaper restore script",
                '                create_restore_script "$video_path"\n',
                '                remove_restore  # native live wallpaper: no mpvpaper restore script (execs.lua would start a 2nd player)\n',
            ),
        ],
    )

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
