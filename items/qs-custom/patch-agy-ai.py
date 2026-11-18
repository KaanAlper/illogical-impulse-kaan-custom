#!/usr/bin/env python3
"""Idempotently patch Quickshell ii Ai.qml & AiChat.qml for native Antigravity (agy) CLI integration."""

import pathlib
import sys


def patch_file(path: pathlib.Path, edits: list[tuple[str, str, str]]) -> bool:
    if not path.exists():
        sys.stderr.write(f"  UYARI: {path} bulunamadi.\n")
        return False
    src = path.read_text(encoding="utf-8")
    changed = False
    for guard, target, replacement in edits:
        if guard in src:
            continue
        if target not in src:
            sys.stderr.write(f"  UYARI: {path.name} icinde hedef bulunamadi ({guard}).\n")
            return False
        src = src.replace(target, replacement, 1)
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
                'root.agyConversationId = "";',
                "    function clearMessages() {",
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
        ],
    )

    # 2. AiChat.qml: hide useless key/temp/tool pills for agy, native CLI-style / popup, clickable model picker
    ok &= patch_file(
        ii / "modules/ii/sidebarLeft/AiChat.qml",
        [
            (
                '    property bool modelPickerOpen: false',
                '    property string commandPrefix: "/"',
                '    property string commandPrefix: "/"\n'
                '    property bool modelPickerOpen: false\n'
                '    property bool configPickerOpen: false',
            ),
            (
                'Ai.getModel()?.api_format === "agy" && inputText.startsWith(root.commandPrefix)',
                '        if (inputText.startsWith(root.commandPrefix)) {',
                '        if (Ai.getModel()?.api_format === "agy" && inputText.startsWith(root.commandPrefix)) {\n'
                '            const parts = inputText.trim().split(/\\s+/);\n'
                '            const cmd = parts[0].substring(1);\n'
                '            if (cmd === "model" || cmd === "effort") { root.configPickerOpen = false; root.modelPickerOpen = true; return; }\n'
                '            if (cmd === "config" || cmd === "settings") { root.modelPickerOpen = false; root.configPickerOpen = true; return; }\n'
                '            if (cmd === "login") {\n'
                '                const agyBin = FileUtils.trimFileProtocol(`${Directories.home}/.local/bin/agy`);\n'
                '                Quickshell.execDetached([Config.options.apps.terminal, "-e", agyBin]);\n'
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
                "AgyConfigPicker {",
                "        Rectangle { // Input area",
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
                '                    text: Ai.getModel().name\n'
                '                    tooltipText: Translation.tr("Current model: %1\\nSet it with %2model MODEL").arg(Ai.getModel().name).arg(root.commandPrefix)\n'
                '                    MouseArea {\n'
                '                        z: 10\n'
                '                        anchors.fill: parent\n'
                '                        cursorShape: Qt.PointingHandCursor\n'
                '                        onClicked: root.modelPickerOpen = !root.modelPickerOpen\n'
                '                    }\n'
                '                }',
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

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
