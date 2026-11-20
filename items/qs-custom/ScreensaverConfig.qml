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

    readonly property string customPath: Config.options?.screensaver?.customPath ?? ""
    readonly property var customItems: Config.options?.screensaver?.customItems ?? []
    readonly property string customExt: {
        const p = customPath.toLowerCase();
        const dot = p.lastIndexOf(".");
        return dot >= 0 ? p.substring(dot + 1) : "";
    }
    readonly property bool isVideoOrGifOrScr: ["mp4", "webm", "mkv", "mov", "avi", "m4v", "gif", "webp", "apng", "scr"].includes(customExt)
    readonly property bool showImageAnimations: (Config.options?.screensaver?.mode ?? "dvd") === "custom" && customPath !== "" && !isVideoOrGifOrScr

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
        Config.options.screensaver.customPath = path;
        Config.options.screensaver.mode = "custom";
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
        if (removed && Config.options.screensaver.customPath === removed.path) {
            if (list.length > 0) {
                Config.options.screensaver.customPath = list[0].path;
            } else {
                Config.options.screensaver.customPath = "";
                Config.options.screensaver.mode = "dvd";
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

        ConfigSlider {
            text: Translation.tr("Speed: %1x").arg((Config.options.screensaver.speed ?? 1.0).toFixed(1))
            value: Config.options.screensaver.speed ?? 1.0
            usePercentTooltip: false
            buttonIcon: "speed"
            from: 0.3
            to: 3.0
            stopIndicatorValues: [1.0]
            onValueChanged: {
                const rounded = Math.round(value * 10) / 10;
                if (Math.abs((Config.options.screensaver.speed ?? 1.0) - rounded) >= 0.05) {
                    Config.options.screensaver.speed = rounded;
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
            currentValue: Config.options.screensaver.mode
            onSelected: newValue => {
                Config.options.screensaver.mode = newValue;
                if (newValue === "custom" && root.customPath === "" && root.customItems.length > 0) {
                    Config.options.screensaver.customPath = root.customItems[0].path;
                }
            }
            options: [
                { displayName: "DVD", icon: "album", value: "dvd" },
                { displayName: "Matrix", icon: "terminal", value: "matrix" },
                { displayName: "Starfield", icon: "auto_awesome", value: "starfield" },
                { displayName: "Mystify", icon: "polyline", value: "mystify" },
                { displayName: "XANA", icon: "adjust", value: "xana" },
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
                        readonly property bool active: Config.options.screensaver.mode === "custom" && Config.options.screensaver.customPath === modelData.path
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
                                Config.options.screensaver.customPath = chipWrap.modelData.path;
                                Config.options.screensaver.mode = "custom";
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
        visible: Config.options.screensaver.mode === "custom"
        icon: "perm_media"
        title: Translation.tr("Add / Select Custom Media")

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            StyledText {
                Layout.fillWidth: true
                text: root.customPath !== "" ? root.customPath : Translation.tr("No file selected (image, GIF, video, or .scr)")
                color: root.customPath !== "" ? Appearance.m3colors.m3onSurface : Appearance.colors.colSubtext
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
                currentValue: Config.options.screensaver.imageAnimation
                onSelected: newValue => {
                    Config.options.screensaver.imageAnimation = newValue;
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
