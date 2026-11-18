pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs
import qs.services
import qs.modules.common
import qs.modules.common.functions
import qs.modules.common.widgets

Item {
    id: root
    required property string backend // "claude" | "codex"

    property string sessionId: ""
    property bool busy: false
    property bool modelPickerOpen: false
    property string selectedModel: backend === "claude" ? "claude-sonnet-5-5" : "gpt-5.4"
    property string selectedEffort: "medium"
    property var suggestionList: []

    readonly property var modelCatalog: backend === "claude"
        ? [
            { id: "claude-sonnet-5-5", name: "Claude Sonnet 5.5", efforts: ["low", "medium", "high", "max"] },
            { id: "claude-opus-5-5",   name: "Claude Opus 5.5",   efforts: ["low", "medium", "high", "max"] },
            { id: "haiku",             name: "Claude Haiku 4.5",  efforts: [] }
          ]
        : [
            { id: "gpt-5.4",       name: "GPT-5.4",       efforts: ["low", "medium", "high"] },
            { id: "gpt-5.3-codex", name: "GPT-5.3 Codex", efforts: ["low", "medium", "high"] },
            { id: "o3",            name: "o3",            efforts: ["low", "medium", "high"] },
            { id: "o4-mini",       name: "o4-mini",       efforts: [] }
          ]

    readonly property var cliCommands: [
        { name: "/model",   instant: true,  description: Translation.tr("Select model & reasoning effort") },
        { name: "/effort",  instant: true,  description: Translation.tr("Set reasoning effort") },
        { name: "/login",   instant: true,  description: backend === "claude" ? "Sign in / authenticate Claude CLI" : "Sign in / authenticate Codex CLI" },
        { name: "/compact", instant: true,  description: Translation.tr("Compact conversation context") },
        { name: "/clear",   instant: true,  description: Translation.tr("Start a new conversation") }
    ]

    function currentModelObj() {
        for (let i = 0; i < modelCatalog.length; i++) {
            if (modelCatalog[i].id === root.selectedModel)
                return modelCatalog[i];
        }
        return modelCatalog[0];
    }

    function currentModelLabel(): string {
        const m = currentModelObj();
        if (m.efforts && m.efforts.length > 0)
            return m.name + " (" + root.selectedEffort + ")";
        return m.name;
    }

    function appendMessage(role: string, text: string) {
        msgModel.append({ role: role, content: text });
        Qt.callLater(() => msgList.positionViewAtEnd());
    }

    function updateLastAssistant(text: string, replace: bool) {
        if (msgModel.count === 0)
            return;
        const idx = msgModel.count - 1;
        const cur = msgModel.get(idx).content;
        msgModel.setProperty(idx, "content", replace ? text : (cur + text));
        Qt.callLater(() => msgList.positionViewAtEnd());
    }

    function openLogin() {
        const cmd = root.backend === "claude" ? "claude" : "codex login";
        Quickshell.execDetached([Config.options.apps.terminal, "-e", "bash", "-c", `${cmd}; echo; read -p 'Press Enter to close...'`]);
    }

    function clearChat() {
        root.sessionId = "";
        msgModel.clear();
    }

    function sendPrompt(rawText: string) {
        const text = rawText.trim();
        if (!text || root.busy)
            return;

        if (text.startsWith("/")) {
            const cmd = text.split(/\s+/)[0].toLowerCase();
            if (cmd === "/model" || cmd === "/effort") {
                root.modelPickerOpen = true;
                return;
            }
            if (cmd === "/login") {
                root.openLogin();
                return;
            }
            if (cmd === "/clear") {
                root.clearChat();
                return;
            }
        }

        root.appendMessage("user", text);
        root.appendMessage("assistant", "");
        root.busy = true;

        const m = currentModelObj();
        if (root.backend === "claude") {
            const args = [
                "claude", "-p", text,
                "--output-format", "stream-json",
                "--verbose",
                "--include-partial-messages",
                "--model", m.id
            ];
            if (m.efforts && m.efforts.length > 0) {
                args.push("--effort", root.selectedEffort);
            }
            if (root.sessionId !== "") {
                args.push("--resume", root.sessionId);
            }
            runner.command = args;
        } else {
            const args = ["codex", "exec"];
            if (root.sessionId !== "") {
                args.push("resume", root.sessionId);
            }
            args.push("--json", "-m", m.id);
            if (m.efforts && m.efforts.length > 0) {
                args.push("-c", `model_reasoning_effort="${root.selectedEffort}"`);
            }
            args.push(text);
            runner.command = args;
        }
        runner.running = true;
    }

    ListModel {
        id: msgModel
    }

    Process {
        id: runner
        stdout: SplitParser {
            onRead: data => {
                if (!data || !data.trim().startsWith("{"))
                    return;
                try {
                    const ev = JSON.parse(data);
                    if (root.backend === "claude") {
                        if (ev.session_id)
                            root.sessionId = ev.session_id;
                        if (ev.type === "stream_event" && ev.event?.delta?.type === "text_delta" && ev.event.delta.text) {
                            root.updateLastAssistant(ev.event.delta.text, false);
                        } else if (ev.type === "assistant" && ev.message?.content) {
                            const parts = ev.message.content.filter(c => c.type === "text").map(c => c.text).join("");
                            if (parts)
                                root.updateLastAssistant(parts, true);
                        } else if (ev.type === "result" && ev.result) {
                            root.updateLastAssistant(ev.result, true);
                        }
                    } else {
                        if (ev.thread_id)
                            root.sessionId = ev.thread_id;
                        if (ev.type === "item.completed" && ev.item?.type === "agent_message" && ev.item.text) {
                            root.updateLastAssistant(ev.item.text, true);
                        } else if (ev.type === "agent_message" && ev.text) {
                            root.updateLastAssistant(ev.text, false);
                        }
                    }
                } catch (e) {}
            }
        }
        stderr: SplitParser {
            onRead: data => {
                if (data && data.trim().length > 0 && msgModel.count > 0) {
                    const idx = msgModel.count - 1;
                    if (msgModel.get(idx).content === "")
                        root.updateLastAssistant(data, false);
                }
            }
        }
        onExited: (code, status) => {
            root.busy = false;
            if (msgModel.count > 0) {
                const idx = msgModel.count - 1;
                if (msgModel.get(idx).content.trim() === "" && code !== 0) {
                    root.updateLastAssistant(
                        (root.backend === "codex" ? "codex" : "claude") + ` CLI error (exit ${code}). Run /login or check installation.`,
                        true
                    );
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            MouseArea {
                anchors.fill: parent
                visible: root.modelPickerOpen
                z: 5
                onPressed: mouse => {
                    root.modelPickerOpen = false;
                    mouse.accepted = false;
                }
            }

            ListView {
                id: msgList
                anchors.fill: parent
                clip: true
                spacing: 6
                model: msgModel

                delegate: Rectangle {
                    id: msgCard
                    required property string role
                    required property string content
                    width: msgList.width
                    implicitHeight: msgCol.implicitHeight + 10
                    radius: Appearance.rounding.small
                    color: role === "user" ? ColorUtils.transparentize(Appearance.colors.colLayer2, 0.45) : "transparent"

                    ColumnLayout {
                        id: msgCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 5
                        spacing: 3

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            StyledText {
                                font.pixelSize: Appearance.font.pixelSize.smaller
                                font.family: Appearance.font.family.monospace
                                font.weight: Font.DemiBold
                                color: msgCard.role === "user" ? Appearance.colors.colPrimary : Appearance.colors.colSubtext
                                text: msgCard.role === "user" ? ">" : ("✦ " + root.currentModelLabel())
                            }
                            Item { Layout.fillWidth: true }
                            RippleButton {
                                implicitWidth: 24
                                implicitHeight: 24
                                buttonRadius: Appearance.rounding.small
                                colBackground: "transparent"
                                colBackgroundHover: Appearance.colors.colSurfaceContainerHigh
                                onClicked: Quickshell.clipboardText = msgCard.content
                                contentItem: MaterialSymbol {
                                    anchors.centerIn: parent
                                    text: "content_copy"
                                    iconSize: 14
                                    color: Appearance.colors.colSubtext
                                }
                            }
                        }

                        StyledText {
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                            font.pixelSize: Appearance.font.pixelSize.small
                            color: Appearance.m3colors.m3onSurface
                            text: msgCard.content || (msgCard.role === "assistant" && root.busy ? "…" : "")
                        }
                    }
                }
            }
        }

        // Inline Model & Effort picker
        Rectangle {
            visible: root.modelPickerOpen
            Layout.fillWidth: true
            implicitHeight: Math.min(280, pickerCol.implicitHeight + 14)
            clip: true
            radius: Appearance.rounding.normal
            color: Appearance.colors.colLayer2
            border.width: 1
            border.color: Appearance.colors.colOutlineVariant

            ColumnLayout {
                id: pickerCol
                anchors.fill: parent
                anchors.margins: 8
                spacing: 4

                StyledText {
                    Layout.leftMargin: 6
                    font.pixelSize: Appearance.font.pixelSize.smaller
                    font.weight: Font.Medium
                    color: Appearance.colors.colSubtext
                    text: root.backend === "claude" ? "Claude Models" : "Codex Models"
                }

                Repeater {
                    model: root.modelCatalog
                    delegate: Rectangle {
                        required property var modelData
                        readonly property bool selected: root.selectedModel === modelData.id
                        readonly property bool hasEfforts: (modelData.efforts?.length ?? 0) > 1
                        Layout.fillWidth: true
                        implicitHeight: mCol.implicitHeight + 6
                        radius: Appearance.rounding.small
                        color: selected ? Appearance.colors.colPrimaryContainer : "transparent"

                        ColumnLayout {
                            id: mCol
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 4
                            spacing: 4

                            RippleButton {
                                Layout.fillWidth: true
                                implicitHeight: 28
                                buttonRadius: Appearance.rounding.small
                                colBackground: "transparent"
                                colBackgroundHover: selected ? "transparent" : Appearance.colors.colSurfaceContainerHigh
                                onClicked: {
                                    root.selectedModel = modelData.id;
                                    if (hasEfforts && modelData.efforts.indexOf(root.selectedEffort) < 0)
                                        root.selectedEffort = modelData.efforts[0];
                                    if (!hasEfforts)
                                        root.modelPickerOpen = false;
                                }
                                contentItem: RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 6
                                    anchors.rightMargin: 6
                                    StyledText {
                                        Layout.fillWidth: true
                                        font.pixelSize: Appearance.font.pixelSize.small
                                        color: selected ? Appearance.colors.colOnPrimaryContainer : Appearance.m3colors.m3onSurface
                                        text: modelData.name
                                    }
                                    MaterialSymbol {
                                        visible: selected
                                        text: "check"
                                        iconSize: 16
                                        color: Appearance.colors.colPrimary
                                    }
                                }
                            }

                            ColumnLayout {
                                visible: selected && hasEfforts
                                Layout.fillWidth: true
                                Layout.leftMargin: 10
                                Layout.rightMargin: 10
                                spacing: 2

                                Slider {
                                    Layout.fillWidth: true
                                    implicitHeight: 22
                                    from: 0
                                    to: Math.max(1, (modelData.efforts?.length ?? 1) - 1)
                                    stepSize: 1
                                    snapMode: Slider.SnapAlways
                                    value: Math.max(0, modelData.efforts.indexOf(root.selectedEffort))
                                    onMoved: {
                                        const eff = modelData.efforts[Math.round(value)];
                                        if (eff)
                                            root.selectedEffort = eff;
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    Repeater {
                                        model: modelData.efforts
                                        delegate: MouseArea {
                                            required property string modelData
                                            Layout.fillWidth: true
                                            implicitHeight: effLbl.implicitHeight
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: root.selectedEffort = modelData
                                            StyledText {
                                                id: effLbl
                                                anchors.horizontalCenter: parent.horizontalCenter
                                                font.pixelSize: Appearance.font.pixelSize.smaller - 1
                                                color: root.selectedEffort === modelData ? Appearance.colors.colPrimary : Appearance.colors.colOnPrimaryContainer
                                                text: modelData
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Scrollable / command list
        Rectangle {
            id: cliSuggestions
            visible: root.suggestionList.length > 0 && inputField.text.startsWith("/")
            property int selectedIndex: 0
            Layout.fillWidth: true
            implicitHeight: Math.min(180, cliSugList.contentHeight + 12)
            clip: true
            radius: Appearance.rounding.normal
            color: Appearance.colors.colLayer2
            border.width: 1
            border.color: Appearance.colors.colOutlineVariant

            ListView {
                id: cliSugList
                anchors.fill: parent
                anchors.margins: 6
                clip: true
                spacing: 2
                currentIndex: cliSuggestions.selectedIndex
                highlightFollowsCurrentItem: true
                onCurrentIndexChanged: positionViewAtIndex(currentIndex, ListView.Contain)
                model: root.suggestionList

                delegate: RippleButton {
                    required property var modelData
                    required property int index
                    readonly property bool active: cliSuggestions.selectedIndex === index
                    width: cliSugList.width
                    implicitHeight: 30
                    buttonRadius: Appearance.rounding.small
                    colBackground: active ? Appearance.colors.colPrimaryContainer : "transparent"
                    colBackgroundHover: active ? Appearance.colors.colPrimaryContainer : Appearance.colors.colSurfaceContainerHigh
                    onHoveredChanged: if (hovered) cliSuggestions.selectedIndex = index
                    onClicked: {
                        inputField.clear();
                        root.sendPrompt(modelData.name);
                    }
                    contentItem: RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        spacing: 8
                        StyledText {
                            font.pixelSize: Appearance.font.pixelSize.small
                            font.family: Appearance.font.family.monospace
                            color: active ? Appearance.colors.colPrimary : Appearance.m3colors.m3onSurface
                            text: modelData.name
                        }
                        StyledText {
                            Layout.fillWidth: true
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            color: active ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colSubtext
                            horizontalAlignment: Text.AlignRight
                            maximumLineCount: 1
                            elide: Text.ElideRight
                            text: modelData.description
                        }
                    }
                }
            }
        }

        // Input box
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: Math.max(66, inputCol.implicitHeight + 10)
            radius: Appearance.rounding.normal
            color: Appearance.colors.colLayer2

            ColumnLayout {
                id: inputCol
                anchors.fill: parent
                anchors.margins: 6
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    StyledTextArea {
                        id: inputField
                        Layout.fillWidth: true
                        wrapMode: TextArea.Wrap
                        placeholderText: (root?.backend ?? "") === "claude"
                            ? Translation.tr("Message Claude... \"/\" for commands")
                            : Translation.tr("Message Codex... \"/\" for commands")
                        onActiveFocusChanged: if (activeFocus) root.modelPickerOpen = false
                        onTextChanged: {
                            if (text.startsWith("/")) {
                                const q = text.toLowerCase();
                                cliSuggestions.selectedIndex = 0;
                                root.suggestionList = root.cliCommands.filter(c => c.name.startsWith(q));
                            } else {
                                root.suggestionList = [];
                            }
                        }
                        Keys.onPressed: event => {
                            if (event.key === Qt.Key_Up && cliSuggestions.visible) {
                                cliSuggestions.selectedIndex = Math.max(0, cliSuggestions.selectedIndex - 1);
                                event.accepted = true;
                            } else if (event.key === Qt.Key_Down && cliSuggestions.visible) {
                                cliSuggestions.selectedIndex = Math.min(root.suggestionList.length - 1, cliSuggestions.selectedIndex + 1);
                                event.accepted = true;
                            } else if (event.key === Qt.Key_Escape) {
                                if (root.modelPickerOpen) {
                                    root.modelPickerOpen = false;
                                    event.accepted = true;
                                } else if (cliSuggestions.visible) {
                                    inputField.clear();
                                    event.accepted = true;
                                }
                            } else if ((event.key === Qt.Key_Enter || event.key === Qt.Key_Return) && !(event.modifiers & Qt.ShiftModifier)) {
                                if (cliSuggestions.visible && root.suggestionList.length > 0) {
                                    const sel = root.suggestionList[cliSuggestions.selectedIndex] ?? root.suggestionList[0];
                                    inputField.clear();
                                    root.sendPrompt(sel.name);
                                } else {
                                    const t = inputField.text;
                                    inputField.clear();
                                    root.sendPrompt(t);
                                }
                                event.accepted = true;
                            }
                        }
                    }

                    RippleButton {
                        implicitWidth: 36
                        implicitHeight: 36
                        buttonRadius: Appearance.rounding.small
                        enabled: inputField.text.length > 0 && !root.busy
                        toggled: enabled
                        onClicked: {
                            const t = inputField.text;
                            inputField.clear();
                            root.sendPrompt(t);
                        }
                        contentItem: MaterialSymbol {
                            anchors.centerIn: parent
                            text: root.busy ? "hourglass_top" : "arrow_upward"
                            iconSize: 20
                            color: enabled ? Appearance.m3colors.m3onPrimary : Appearance.colors.colOnLayer2Disabled
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    ApiInputBoxIndicator {
                        icon: "api"
                        text: root.currentModelLabel()
                        MouseArea {
                            z: 10
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.modelPickerOpen = !root.modelPickerOpen
                        }
                    }

                    Item { Layout.fillWidth: true }

                    ApiCommandButton {
                        buttonText: "/"
                        onClicked: {
                            inputField.text = "/";
                            inputField.forceActiveFocus();
                        }
                    }
                    ApiCommandButton {
                        buttonText: "/clear"
                        onClicked: root.clearChat()
                    }
                }
            }
        }
    }
}
