import QtQuick
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
    readonly property string customExt: {
        const p = customPath.toLowerCase();
        const dot = p.lastIndexOf(".");
        return dot >= 0 ? p.substring(dot + 1) : "";
    }
    readonly property bool isVideoOrGifOrScr: ["mp4", "webm", "mkv", "mov", "avi", "m4v", "gif", "webp", "apng", "scr"].includes(customExt)
    readonly property bool showImageAnimations: (Config.options?.screensaver?.mode ?? "dvd") === "custom" && customPath !== "" && !isVideoOrGifOrScr

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
            Config.options.screensaver.customPath = path;
            Config.options.screensaver.mode = "custom";
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
            text: Translation.tr("Wait time before screensaver (minutes)")
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
            text: Translation.tr("Animation speed (%1x)").arg((Config.options.screensaver.speed ?? 1.0).toFixed(1))
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
            Layout.fillWidth: true
            implicitHeight: 40
            buttonRadius: Appearance.rounding.normal
            colBackground: Appearance.colors.colPrimary
            colBackgroundHover: Appearance.colors.colPrimaryHover
            onClicked: Quickshell.execDetached(["qs", "ipc", "-c", "ii", "call", "screensaver", "show"])
            contentItem: RowLayout {
                anchors.centerIn: parent
                spacing: 8
                MaterialSymbol {
                    text: "play_arrow"
                    iconSize: 20
                    color: Appearance.m3colors.m3onPrimary
                }
                StyledText {
                    text: Translation.tr("Preview Screensaver")
                    color: Appearance.m3colors.m3onPrimary
                    font.pixelSize: Appearance.font.pixelSize.small
                    font.weight: Font.Medium
                }
            }
        }
    }

    ContentSection {
        icon: "style"
        title: Translation.tr("Screensaver Style")

        ConfigSelectionArray {
            currentValue: Config.options.screensaver.mode
            onSelected: newValue => {
                Config.options.screensaver.mode = newValue;
            }
            options: [
                { displayName: "DVD Bounce", icon: "album", value: "dvd" },
                { displayName: "Matrix Rain", icon: "terminal", value: "matrix" },
                { displayName: "Starfield", icon: "auto_awesome", value: "starfield" },
                { displayName: "Mystify", icon: "polyline", value: "mystify" },
                { displayName: "XANA", icon: "adjust", value: "xana" },
                { displayName: Translation.tr("Custom File"), icon: "folder_open", value: "custom" }
            ]
        }
    }

    ContentSection {
        visible: Config.options.screensaver.mode === "custom"
        icon: "perm_media"
        title: Translation.tr("Custom Media / .scr")

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
                    { displayName: "DVD Bounce", icon: "open_with", value: "dvd" },
                    { displayName: "Float", icon: "waves", value: "float" },
                    { displayName: "None", icon: "block", value: "none" }
                ]
            }
        }
    }
}
