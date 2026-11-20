import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets

ContentPage {
    id: root
    forceWidth: true

    property string selectedMonitor: Quickshell.screens.length > 0 ? Quickshell.screens[0].name : ""
    readonly property bool perMonitor: Config.options?.screensaver?.perMonitor ?? false
    readonly property var monitorsMap: Config.options?.screensaver?.monitors ?? ({})

    function eff(key, fallback) {
        if (root.perMonitor && root.selectedMonitor !== "") {
            const m = root.monitorsMap[root.selectedMonitor];
            if (m && m[key] !== undefined) return m[key];
        }
        const v = Config.options?.screensaver?.[key];
        return v !== undefined ? v : fallback;
    }

    function setEff(key, val) {
        if (root.perMonitor && root.selectedMonitor !== "") {
            const all = Object.assign({}, Config.options.screensaver.monitors ?? {});
            const cur = Object.assign({}, all[root.selectedMonitor] ?? {});
            cur[key] = val;
            all[root.selectedMonitor] = cur;
            Config.options.screensaver.monitors = all;
        } else {
            Config.options.screensaver[key] = val;
        }
    }

    readonly property string effMode: eff("mode", "dvd")
    readonly property string effColor: eff("color", "#000000")
    readonly property string effCustomPath: eff("customPath", "")
    readonly property string effImageAnimation: eff("imageAnimation", "breathe")
    readonly property real effSpeed: eff("speed", 1.0)

    readonly property var customItems: Config.options?.screensaver?.customItems ?? []
    readonly property string customExt: {
        const p = effCustomPath.toLowerCase();
        const dot = p.lastIndexOf(".");
        return dot >= 0 ? p.substring(dot + 1) : "";
    }
    readonly property bool isVideoOrGifOrScr: ["mp4", "webm", "mkv", "mov", "avi", "m4v", "gif", "webp", "apng", "scr"].includes(customExt)
    readonly property bool showImageAnimations: effMode === "custom" && effCustomPath !== "" && !isVideoOrGifOrScr

    readonly property var colorSwatches: [
        "#000000", "#0f172a", "#1a1b26", "#1e293b",
        "#1e3a8a", "#312e81", "#581c87", "#831843",
        "#7f1d1d", "#9a3412", "#14532d", "#134e4a",
        "#0369a1", "#d97706", "#475569", "#ffffff"
    ]

    property int renamingIndex: -1

    function addCustomItem(path) {
        const list = (Config.options.screensaver.customItems ?? []).slice();
        const existing = list.findIndex(it => it.path === path);
        if (existing === -1) {
            const parts = path.split("/");
            const base = parts[parts.length - 1] || path;
            list.push({ name: base, path: path });
            Config.options.screensaver.customItems = list;
        }
        root.setEff("customPath", path);
        root.setEff("mode", "custom");
    }

    function renameCustomItem(idx, newName) {
        const trimmed = newName.trim();
        if (!trimmed) { root.renamingIndex = -1; return; }
        const list = (Config.options.screensaver.customItems ?? []).map((it, i) =>
            i === idx ? ({ name: trimmed, path: it.path }) : it
        );
        Config.options.screensaver.customItems = list;
        root.renamingIndex = -1;
    }

    function deleteCustomItem(idx) {
        const list = (Config.options.screensaver.customItems ?? []).slice();
        const removed = list.splice(idx, 1)[0];
        Config.options.screensaver.customItems = list;
        if (removed && root.effCustomPath === removed.path) {
            if (list.length > 0) {
                root.setEff("customPath", list[0].path);
            } else {
                root.setEff("customPath", "");
                root.setEff("mode", "dvd");
            }
        }
        if (root.renamingIndex === idx) root.renamingIndex = -1;
    }

    Timer {
        id: idleSyncTimer
        interval: 200
        repeat: false
        onTriggered: {
            idleSyncProc.running = false;
            idleSyncProc.running = true;
        }
    }

    Process {
        id: idleSyncProc
        command: [
            "python3",
            Quickshell.shellPath("scripts/apply-screensaver-idle.py"),
            Config.options.screensaver.enable ? "1" : "0",
            String(Config.options.screensaver.timeoutMinutes)
        ]
    }

    Process {
        id: previewProc
        command: ["qs", "-c", "ii", "ipc", "call", "screensaver", "open"]
    }

    FileDialog {
        id: mediaPicker
        title: Translation.tr("Select screensaver media or .scr")
        nameFilters: [
            "All supported (*.png *.jpg *.jpeg *.webp *.svg *.bmp *.gif *.mp4 *.webm *.mkv *.mov *.avi *.m4v *.scr)",
            "Images (*.png *.jpg *.jpeg *.webp *.svg *.bmp)",
            "Videos & GIF (*.mp4 *.webm *.mkv *.mov *.avi *.m4v *.gif)",
            "Windows Screensaver (*.scr)",
            "All files (*)"
        ]
        onAccepted: {
            const path = selectedFile.toString().replace(/^file:\/\//, "");
            root.addCustomItem(path);
        }
    }

    ColorDialog {
        id: colorPicker
        title: Translation.tr("Select screensaver color")
        selectedColor: root.effColor
        onAccepted: root.setEff("color", selectedColor.toString())
    }

    ContentSection {
        icon: "tv"
        title: Translation.tr("Screensaver")

        ConfigSwitch {
            buttonIcon: "bedtime"
            text: Translation.tr("Enable screensaver on idle")
            checked: Config.options.screensaver.enable
            onCheckedChanged: {
                if (Config.options.screensaver.enable !== checked) {
                    Config.options.screensaver.enable = checked;
                    idleSyncTimer.restart();
                }
            }
        }

        ConfigSpinBox {
            icon: "timer"
            text: Translation.tr("Idle timeout (minutes)")
            value: Config.options.screensaver.timeoutMinutes
            from: 1
            to: 60
            stepSize: 1
            onValueChanged: {
                if (Config.options.screensaver.timeoutMinutes !== value) {
                    Config.options.screensaver.timeoutMinutes = value;
                    idleSyncTimer.restart();
                }
            }
        }

        ConfigSwitch {
            buttonIcon: "monitor"
            text: Translation.tr("Separate per monitor")
            checked: Config.options.screensaver.perMonitor ?? false
            onCheckedChanged: {
                if ((Config.options.screensaver.perMonitor ?? false) !== checked) {
                    Config.options.screensaver.perMonitor = checked;
                    if (checked && root.selectedMonitor === "" && Quickshell.screens.length > 0) {
                        root.selectedMonitor = Quickshell.screens[0].name;
                    }
                }
            }
        }

        Flow {
            visible: root.perMonitor
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: Quickshell.screens
                delegate: RippleButton {
                    id: monBtn
                    required property var modelData
                    required property int index
                    readonly property bool selected: root.selectedMonitor === modelData.name
                    implicitWidth: monRow.implicitWidth + 24
                    implicitHeight: 40
                    buttonRadius: Appearance.rounding.normal
                    colBackground: selected ? Appearance.colors.colPrimaryContainer : Appearance.colors.colSurfaceContainerHigh
                    onClicked: root.selectedMonitor = modelData.name

                    Rectangle {
                        anchors.fill: parent
                        radius: parent.buttonRadius
                        color: "transparent"
                        border.width: monBtn.selected ? 2 : 1
                        border.color: monBtn.selected ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant
                    }

                    contentItem: RowLayout {
                        id: monRow
                        anchors.centerIn: parent
                        spacing: 8
                        MaterialSymbol {
                            text: "desktop_windows"
                            iconSize: 18
                            color: monBtn.selected ? Appearance.colors.colPrimary : Appearance.m3colors.m3onSurface
                        }
                        StyledText {
                            text: "%1 · %2 (%3×%4)".arg(monBtn.index + 1).arg(monBtn.modelData.name).arg(monBtn.modelData.width).arg(monBtn.modelData.height)
                            color: monBtn.selected ? Appearance.colors.colOnPrimaryContainer : Appearance.m3colors.m3onSurface
                            font.pixelSize: Appearance.font.pixelSize.small
                            font.weight: monBtn.selected ? Font.DemiBold : Font.Normal
                        }
                    }
                }
            }
        }

        ConfigSlider {
            text: Translation.tr("Speed: %1x").arg(root.effSpeed.toFixed(1))
            value: root.effSpeed
            usePercentTooltip: false
            buttonIcon: "speed"
            from: 0.3
            to: 3.0
            stopIndicatorValues: [1.0]
            onValueChanged: {
                const rounded = Math.round(value * 10) / 10;
                if (Math.abs(root.effSpeed - rounded) >= 0.05) {
                    root.setEff("speed", rounded);
                }
            }
        }

        RippleButton {
            Layout.alignment: Qt.AlignLeft
            implicitWidth: previewRow.implicitWidth + 28
            implicitHeight: 36
            buttonRadius: Appearance.rounding.full
            colBackground: Appearance.colors.colPrimary
            colBackgroundHover: Appearance.colors.colPrimaryHover
            onClicked: {
                previewProc.running = false;
                previewProc.running = true;
            }
            contentItem: RowLayout {
                id: previewRow
                anchors.centerIn: parent
                spacing: 6
                MaterialSymbol {
                    text: "play_arrow"
                    iconSize: 18
                    color: Appearance.m3colors.m3onPrimary
                }
                StyledText {
                    text: Translation.tr("Preview")
                    color: Appearance.m3colors.m3onPrimary
                    font.pixelSize: Appearance.font.pixelSize.small
                    font.weight: Font.Medium
                }
            }
        }
    }

    ContentSection {
        icon: "style"
        title: Translation.tr("Style")

        ConfigSelectionArray {
            currentValue: root.effMode
            onSelected: newValue => {
                root.setEff("mode", newValue);
                if (newValue === "custom" && root.effCustomPath === "" && root.customItems.length > 0) {
                    root.setEff("customPath", root.customItems[0].path);
                }
            }
            options: [
                { displayName: "DVD", icon: "album", value: "dvd" },
                { displayName: "Matrix", icon: "terminal", value: "matrix" },
                { displayName: "Starfield", icon: "auto_awesome", value: "starfield" },
                { displayName: "Mystify", icon: "polyline", value: "mystify" },
                { displayName: "XANA", icon: "adjust", value: "xana" },
                { displayName: Translation.tr("Color"), icon: "palette", value: "color" },
                { displayName: Translation.tr("Custom"), icon: "folder_open", value: "custom" }
            ]
        }

        ContentSubsection {
            visible: root.customItems.length > 0
            title: Translation.tr("Custom")

            Flow {
                Layout.fillWidth: true
                spacing: 6

                Repeater {
                    model: root.customItems
                    delegate: Item {
                        id: chipWrap
                        required property var modelData
                        required property int index
                        readonly property bool active: root.effMode === "custom" && root.effCustomPath === modelData.path
                        readonly property bool isRenaming: root.renamingIndex === index
                        implicitWidth: isRenaming ? 200 : chipBtn.implicitWidth
                        implicitHeight: 34

                        RippleButton {
                            id: chipBtn
                            visible: !chipWrap.isRenaming
                            anchors.fill: parent
                            implicitWidth: chipRow.implicitWidth + 20
                            implicitHeight: 34
                            buttonRadius: Appearance.rounding.full
                            colBackground: chipWrap.active ? Appearance.colors.colPrimaryContainer : Appearance.colors.colSurfaceContainerHigh
                            onClicked: {
                                root.setEff("customPath", chipWrap.modelData.path);
                                root.setEff("mode", "custom");
                            }
                            MouseArea {
                                anchors.fill: parent
                                acceptedButtons: Qt.RightButton
                                onClicked: chipMenu.popup()
                            }
                            contentItem: RowLayout {
                                id: chipRow
                                anchors.centerIn: parent
                                spacing: 6
                                MaterialSymbol {
                                    text: "perm_media"
                                    iconSize: 16
                                    color: chipWrap.active ? Appearance.colors.colPrimary : Appearance.m3colors.m3onSurface
                                }
                                StyledText {
                                    text: chipWrap.modelData.name
                                    color: chipWrap.active ? Appearance.colors.colOnPrimaryContainer : Appearance.m3colors.m3onSurface
                                    font.pixelSize: Appearance.font.pixelSize.small
                                }
                            }

                            Menu {
                                id: chipMenu
                                MenuItem {
                                    text: Translation.tr("Rename")
                                    onTriggered: root.renamingIndex = chipWrap.index
                                }
                                MenuItem {
                                    text: Translation.tr("Delete")
                                    onTriggered: root.deleteCustomItem(chipWrap.index)
                                }
                            }
                        }

                        TextField {
                            visible: chipWrap.isRenaming
                            anchors.fill: parent
                            text: chipWrap.modelData.name
                            onVisibleChanged: if (visible) { forceActiveFocus(); selectAll(); }
                            onAccepted: root.renameCustomItem(chipWrap.index, text)
                            Keys.onEscapePressed: root.renamingIndex = -1
                        }
                    }
                }
            }
        }
    }

    ContentSection {
        visible: root.effMode === "color"
        icon: "palette"
        title: Translation.tr("Color")

        Flow {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: root.colorSwatches
                delegate: RippleButton {
                    id: swatchBtn
                    required property string modelData
                    readonly property bool selected: root.effColor.toLowerCase() === modelData.toLowerCase()
                    implicitWidth: 36
                    implicitHeight: 36
                    buttonRadius: Appearance.rounding.full
                    colBackground: modelData
                    onClicked: root.setEff("color", modelData)

                    Rectangle {
                        anchors.fill: parent
                        radius: parent.buttonRadius
                        color: "transparent"
                        border.width: swatchBtn.selected ? 3 : 1
                        border.color: swatchBtn.selected ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                implicitWidth: 28
                implicitHeight: 28
                radius: Appearance.rounding.full
                color: root.effColor
                border.width: 1
                border.color: Appearance.colors.colOutlineVariant
            }

            StyledText {
                Layout.fillWidth: true
                text: root.effColor.toUpperCase()
                color: Appearance.m3colors.m3onSurface
                font.pixelSize: Appearance.font.pixelSize.small
                font.family: Appearance.font.family.monospace
            }

            RippleButton {
                implicitWidth: pickColorTxt.implicitWidth + 24
                implicitHeight: 34
                buttonRadius: Appearance.rounding.full
                colBackground: Appearance.colors.colSecondaryContainer
                onClicked: colorPicker.open()
                contentItem: StyledText {
                    id: pickColorTxt
                    anchors.centerIn: parent
                    text: Translation.tr("Pick Color")
                    color: Appearance.colors.colOnSecondaryContainer
                    font.pixelSize: Appearance.font.pixelSize.small
                    font.weight: Font.Medium
                }
            }
        }
    }

    ContentSection {
        visible: root.effMode === "custom"
        icon: "perm_media"
        title: Translation.tr("Add / Select Custom Media")

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            StyledText {
                Layout.fillWidth: true
                text: root.effCustomPath !== "" ? root.effCustomPath : Translation.tr("No file selected (image, GIF, video, or .scr)")
                color: root.effCustomPath !== "" ? Appearance.m3colors.m3onSurface : Appearance.colors.colSubtext
                font.pixelSize: Appearance.font.pixelSize.small
                elide: Text.ElideMiddle
            }

            RippleButton {
                implicitWidth: browseTxt.implicitWidth + 24
                implicitHeight: 34
                buttonRadius: Appearance.rounding.full
                colBackground: Appearance.colors.colSecondaryContainer
                onClicked: mediaPicker.open()
                contentItem: StyledText {
                    id: browseTxt
                    anchors.centerIn: parent
                    text: Translation.tr("Choose File")
                    color: Appearance.colors.colOnSecondaryContainer
                    font.pixelSize: Appearance.font.pixelSize.small
                    font.weight: Font.Medium
                }
            }
        }

        ContentSubsection {
            visible: root.showImageAnimations
            title: Translation.tr("Image Animation")

            ConfigSelectionArray {
                currentValue: root.effImageAnimation
                onSelected: newValue => {
                    root.setEff("imageAnimation", newValue);
                }
                options: [
                    { displayName: "Breathe", icon: "air", value: "breathe" },
                    { displayName: "Knight Rider", icon: "linear_scale", value: "knightrider" },
                    { displayName: "Spin", icon: "rotate_right", value: "spin" },
                    { displayName: "DVD", icon: "open_with", value: "dvd" },
                    { displayName: "Float", icon: "waves", value: "float" },
                    { displayName: "None", icon: "block", value: "none" }
                ]
            }
        }
    }
}
