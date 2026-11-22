import QtQuick
import QtMultimedia
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.functions

ContentPage {
    id: wallpaperPage
    forceWidth: true

    property string selectedMonitor: Quickshell.screens.length > 0 ? Quickshell.screens[0].name : ""
    property bool previewPaused: false

    readonly property string activePath: {
        if (Config.options.background.perMonitor && wallpaperPage.selectedMonitor !== "") {
            const entry = Config.options.background.monitors?.[wallpaperPage.selectedMonitor];
            if (entry && entry.wallpaperPath && entry.wallpaperPath !== "")
                return entry.wallpaperPath;
        }
        return Config.options.background.wallpaperPath;
    }
    readonly property bool isVideo: /\.(mp4|webm|mkv|avi|mov)$/i.test(activePath)
    readonly property bool isGif: /\.gif$/i.test(activePath)
    readonly property string fileName: {
        const p = activePath.replace(/^file:\/\//, "");
        const parts = p.split("/");
        return parts.length > 0 ? parts[parts.length - 1] : "";
    }

    function formatMs(ms) {
        if (!ms || ms <= 0) return "00:00";
        const totalSec = Math.floor(ms / 1000);
        const m = Math.floor(totalSec / 60);
        const s = totalSec % 60;
        return `${m < 10 ? "0" : ""}${m}:${s < 10 ? "0" : ""}${s}`;
    }

    Process {
        id: randomWallProc
        property string status: ""
        command: ["bash", "-c", "true"]
        stdout: SplitParser {
            onRead: data => randomWallProc.status = data.trim()
        }
    }

    ContentSection {
        icon: "wallpaper"
        title: Translation.tr("Wallpaper")
        Layout.fillWidth: true

        ConfigSwitch {
            buttonIcon: "desktop_windows"
            text: Translation.tr("Separate per monitor")
            checked: Config.options.background.perMonitor
            onCheckedChanged: {
                if (Config.options.background.perMonitor !== checked) {
                    Config.options.background.perMonitor = checked;
                }
            }
        }

        MonitorOrderPills {
            visible: Config.options.background.perMonitor
            selectedMonitor: wallpaperPage.selectedMonitor
            onMonitorSelected: name => wallpaperPage.selectedMonitor = name
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            Item {
                id: wpPreviewBox
                implicitWidth: 380
                implicitHeight: 214

                NumberAnimation on opacity {
                    id: wpFadeAnim
                    from: 0.25
                    to: 1
                    duration: 180
                    easing.type: Easing.OutCubic
                    running: false
                }
                Connections {
                    target: wallpaperPage
                    function onActivePathChanged() {
                        wallpaperPage.previewPaused = false;
                        wpFadeAnim.restart();
                    }
                }

                Item {
                    anchors.fill: parent
                    layer.enabled: true
                    layer.effect: OpacityMask {
                        maskSource: Rectangle {
                            width: wpPreviewBox.width
                            height: wpPreviewBox.height
                            radius: Appearance.rounding.normal
                        }
                    }

                    Rectangle {
                        anchors.fill: parent
                        color: Appearance.colors.colLayer2
                    }

                    StyledImage {
                        id: staticPreview
                        anchors.fill: parent
                        visible: !wallpaperPage.isVideo && !wallpaperPage.isGif
                        fillMode: Config.options.background.live.fillMode === "fit" ? Image.PreserveAspectFit
                                : Config.options.background.live.fillMode === "stretch" ? Image.Stretch
                                : Image.PreserveAspectCrop
                        source: visible ? wallpaperPage.activePath : ""
                        cache: true
                    }

                    AnimatedImage {
                        id: gifPreview
                        anchors.fill: parent
                        visible: wallpaperPage.isGif
                        source: visible ? ("file://" + wallpaperPage.activePath.replace(/^file:\/\//, "")) : ""
                        fillMode: Config.options.background.live.fillMode === "fit" ? Image.PreserveAspectFit
                                : Config.options.background.live.fillMode === "stretch" ? Image.Stretch
                                : Image.PreserveAspectCrop
                        playing: visible && wallpaperPage.visible && !wallpaperPage.previewPaused
                        speed: Config.options.background.live.speed
                        asynchronous: true
                    }

                    Loader {
                        id: videoPreviewLoader
                        anchors.fill: parent
                        active: wallpaperPage.isVideo && wallpaperPage.visible && wallpaperPage.activePath !== ""
                        visible: active
                        sourceComponent: Item {
                            anchors.fill: parent
                            property alias player: wpVidPlayer
                            MediaPlayer {
                                id: wpVidPlayer
                                source: "file://" + wallpaperPage.activePath.replace(/^file:\/\//, "")
                                loops: Config.options.background.live.loop ? MediaPlayer.Infinite : 1
                                playbackRate: Config.options.background.live.speed
                                audioOutput: AudioOutput { muted: true }
                                videoOutput: wpVidOut
                                Component.onCompleted: if (!wallpaperPage.previewPaused) play()
                            }
                            Connections {
                                target: wallpaperPage
                                function onPreviewPausedChanged() {
                                    if (wallpaperPage.previewPaused) wpVidPlayer.pause();
                                    else wpVidPlayer.play();
                                }
                            }
                            VideoOutput {
                                id: wpVidOut
                                anchors.fill: parent
                                fillMode: Config.options.background.live.fillMode === "fit" ? VideoOutput.PreserveAspectFit
                                        : Config.options.background.live.fillMode === "stretch" ? VideoOutput.Stretch
                                        : VideoOutput.PreserveAspectCrop
                            }
                        }
                    }

                    Rectangle {
                        visible: wallpaperPage.isVideo || wallpaperPage.isGif
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.margins: 8
                        radius: Appearance.rounding.full
                        color: Qt.rgba(0, 0, 0, 0.65)
                        implicitWidth: wpBadgeRow.implicitWidth + 14
                        implicitHeight: 24
                        RowLayout {
                            id: wpBadgeRow
                            anchors.centerIn: parent
                            spacing: 4
                            MaterialSymbol {
                                text: wallpaperPage.previewPaused ? "pause_circle" : "play_circle"
                                iconSize: 14
                                color: "#ffffff"
                            }
                            StyledText {
                                text: wallpaperPage.isGif ? "GIF" : "LIVE"
                                color: "#ffffff"
                                font.pixelSize: 11
                                font.weight: Font.Medium
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                RippleButtonWithIcon {
                    Layout.fillWidth: true
                    materialIcon: "wallpaper"
                    mainText: Translation.tr("Choose file")
                    onClicked: {
                        if (Config.options.background.perMonitor && wallpaperPage.selectedMonitor !== "") {
                            Quickshell.execDetached(["bash", "-c", `${Directories.wallpaperSwitchScriptPath} --monitor "${wallpaperPage.selectedMonitor}"`]);
                        } else {
                            Quickshell.execDetached(`${Directories.wallpaperSwitchScriptPath}`);
                        }
                    }
                }

                RippleButtonWithIcon {
                    enabled: !randomWallProc.running
                    visible: Config.options.policies.weeb === 1
                    Layout.fillWidth: true
                    buttonRadius: Appearance.rounding.small
                    materialIcon: "ifl"
                    mainText: randomWallProc.running ? Translation.tr("Be patient...") : Translation.tr("Random: Konachan")
                    onClicked: {
                        const mon = (Config.options.background.perMonitor && wallpaperPage.selectedMonitor !== "") ? wallpaperPage.selectedMonitor : "";
                        randomWallProc.command = ["bash", "-c", `II_TARGET_MONITOR="${mon}" "${FileUtils.trimFileProtocol(Directories.scriptPath)}/colors/random/random_konachan_wall.sh"`];
                        randomWallProc.running = true;
                    }
                }

                RippleButtonWithIcon {
                    enabled: !randomWallProc.running
                    visible: Config.options.policies.weeb === 1
                    Layout.fillWidth: true
                    buttonRadius: Appearance.rounding.small
                    materialIcon: "ifl"
                    mainText: randomWallProc.running ? Translation.tr("Be patient...") : Translation.tr("Random: osu! seasonal")
                    onClicked: {
                        const mon = (Config.options.background.perMonitor && wallpaperPage.selectedMonitor !== "") ? wallpaperPage.selectedMonitor : "";
                        randomWallProc.command = ["bash", "-c", `II_TARGET_MONITOR="${mon}" "${FileUtils.trimFileProtocol(Directories.scriptPath)}/colors/random/random_osu_wall.sh"`];
                        randomWallProc.running = true;
                    }
                }

                RippleButtonWithIcon {
                    visible: wallpaperPage.isVideo || wallpaperPage.isGif
                    Layout.fillWidth: true
                    buttonRadius: Appearance.rounding.small
                    materialIcon: wallpaperPage.previewPaused ? "play_arrow" : "pause"
                    mainText: wallpaperPage.previewPaused ? Translation.tr("Resume preview") : Translation.tr("Pause preview")
                    onClicked: wallpaperPage.previewPaused = !wallpaperPage.previewPaused
                }

                // Media metadata summary (file, duration, resolution)
                Rectangle {
                    Layout.fillWidth: true
                    radius: Appearance.rounding.small
                    color: Appearance.colors.colLayer2
                    implicitHeight: metaCol.implicitHeight + 14

                    ColumnLayout {
                        id: metaCol
                        anchors.fill: parent
                        anchors.margins: 7
                        spacing: 3

                        StyledText {
                            Layout.fillWidth: true
                            elide: Text.ElideMiddle
                            text: wallpaperPage.fileName !== "" ? wallpaperPage.fileName : Translation.tr("None")
                            color: Appearance.m3colors.m3onSurface
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            font.weight: Font.Medium
                        }

                        StyledText {
                            Layout.fillWidth: true
                            color: Appearance.colors.colSubtext
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            text: {
                                if (wallpaperPage.isVideo && videoPreviewLoader.item) {
                                    const p = videoPreviewLoader.item.player;
                                    const dur = wallpaperPage.formatMs(p.duration);
                                    const pos = wallpaperPage.formatMs(p.position);
                                    const res = p.metaData.value(MediaMetaData.Resolution);
                                    const resTxt = (res && res.width > 0) ? ` · ${res.width}×${res.height}` : "";
                                    return `${Translation.tr("Duration")}: ${pos} / ${dur}${resTxt}`;
                                }
                                if (wallpaperPage.isGif) {
                                    return `GIF · ${gifPreview.sourceSize.width}×${gifPreview.sourceSize.height} (${gifPreview.frameCount} frames)`;
                                }
                                return `${Translation.tr("Resolution")}: ${staticPreview.sourceSize.width}×${staticPreview.sourceSize.height}`;
                            }
                        }
                    }
                }
            }
        }
    }

    ContentSection {
        icon: "motion_play"
        title: Translation.tr("Live wallpaper")
        Layout.fillWidth: true

        ConfigSlider {
            buttonIcon: "speed"
            text: `${Translation.tr("Playback speed")}: ${Config.options.background.live.speed.toFixed(2)}x`
            value: Config.options.background.live.speed
            from: 0.25
            to: 2.5
            usePercentTooltip: false
            onValueChanged: {
                const rounded = Math.round(value * 20) / 20;
                if (Math.abs(Config.options.background.live.speed - rounded) >= 0.02) {
                    Config.options.background.live.speed = rounded;
                }
            }
        }

        ContentSubsection {
            title: Translation.tr("Fill mode")
            ConfigSelectionArray {
                currentValue: Config.options.background.live.fillMode
                onSelected: newValue => Config.options.background.live.fillMode = newValue
                options: [
                    { displayName: Translation.tr("Crop"), icon: "crop", value: "crop" },
                    { displayName: Translation.tr("Fit"), icon: "fit_screen", value: "fit" },
                    { displayName: Translation.tr("Stretch"), icon: "aspect_ratio", value: "stretch" }
                ]
            }
        }

        ConfigSwitch {
            buttonIcon: "repeat"
            text: Translation.tr("Loop playback")
            checked: Config.options.background.live.loop
            onCheckedChanged: Config.options.background.live.loop = checked
        }

        ConfigSwitch {
            buttonIcon: "fullscreen"
            text: Translation.tr("Pause when fullscreen")
            checked: Config.options.background.live.pauseOnFullscreen
            onCheckedChanged: Config.options.background.live.pauseOnFullscreen = checked
        }

        ConfigSwitch {
            buttonIcon: "volume_off"
            text: Translation.tr("Mute audio")
            checked: Config.options.background.live.muted
            onCheckedChanged: Config.options.background.live.muted = checked
        }

        ConfigSlider {
            visible: !Config.options.background.live.muted
            buttonIcon: "volume_up"
            text: Translation.tr("Volume")
            value: Config.options.background.live.volume
            from: 0.0
            to: 1.0
            onValueChanged: {
                const rounded = Math.round(value * 20) / 20;
                if (Math.abs(Config.options.background.live.volume - rounded) >= 0.02) {
                    Config.options.background.live.volume = rounded;
                }
            }
        }
    }
}
