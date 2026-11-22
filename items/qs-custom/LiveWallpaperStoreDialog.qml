import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets

Popup {
    id: storePopup

    property string targetMonitor: ""
    property var items: []
    property bool loading: false
    property string downloadingId: ""
    property int currentPage: 1
    property string searchQuery: ""

    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    anchors.centerIn: Overlay.overlay
    width: Math.min(820, (Overlay.overlay?.width ?? 900) - 48)
    height: Math.min(640, (Overlay.overlay?.height ?? 700) - 48)
    padding: 0

    function loadStore(page, query) {
        storePopup.loading = true;
        storePopup.currentPage = page;
        storePopup.searchQuery = query;
        listProc.command = [
            "python3",
            Quickshell.shellPath("scripts/colors/live-wallpaper-store.py"),
            "list",
            String(page),
            query
        ];
        listProc.running = false;
        listProc.running = true;
    }

    onOpened: {
        if (items.length === 0) {
            loadStore(1, "");
        }
    }

    Process {
        id: listProc
        stdout: StdioCollector {
            onStreamFinished: {
                storePopup.loading = false;
                try {
                    storePopup.items = JSON.parse(text.trim() || "[]");
                } catch (e) {
                    storePopup.items = [];
                }
            }
        }
    }

    Process {
        id: downloadProc
        onExited: (code, status) => {
            storePopup.downloadingId = "";
            if (code === 0) {
                storePopup.close();
            }
        }
    }

    background: Rectangle {
        radius: Appearance.rounding.large
        color: Appearance.m3colors.m3surfaceContainer
        border.width: 1
        border.color: Appearance.colors.colOutlineVariant
    }

    Overlay.modal: Rectangle {
        color: Qt.rgba(0, 0, 0, 0.58)
    }

    contentItem: ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            MaterialSymbol {
                text: "storefront"
                iconSize: 22
                color: Appearance.colors.colPrimary
            }
            StyledText {
                Layout.fillWidth: true
                text: storePopup.targetMonitor !== ""
                    ? `${Translation.tr("Live Wallpaper Store")} · ${storePopup.targetMonitor}`
                    : Translation.tr("Live Wallpaper Store")
                font.pixelSize: Appearance.font.pixelSize.large
                font.weight: Font.Medium
                color: Appearance.m3colors.m3onSurface
            }
            RippleButton {
                implicitWidth: 34
                implicitHeight: 34
                buttonRadius: Appearance.rounding.full
                colBackground: Appearance.colors.colLayer2
                onClicked: storePopup.close()
                contentItem: MaterialSymbol {
                    anchors.centerIn: parent
                    text: "close"
                    iconSize: 18
                    color: Appearance.m3colors.m3onSurface
                }
            }
        }

        // Search + category chips
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 38
                radius: Appearance.rounding.full
                color: Appearance.colors.colLayer2
                border.width: 1
                border.color: searchField.activeFocus ? Appearance.colors.colPrimary : Appearance.colors.colOutlineVariant

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 8
                    MaterialSymbol {
                        text: "search"
                        iconSize: 18
                        color: Appearance.colors.colSubtext
                    }
                    TextInput {
                        id: searchField
                        Layout.fillWidth: true
                        color: Appearance.m3colors.m3onSurface
                        font.pixelSize: Appearance.font.pixelSize.small
                        font.family: Appearance.font.family.main
                        clip: true
                        onAccepted: storePopup.loadStore(1, text)
                        Text {
                            anchors.fill: parent
                            verticalAlignment: Text.AlignVCenter
                            text: Translation.tr("Search live wallpapers (e.g. anime, cyberpunk, space)...")
                            color: Appearance.colors.colSubtext
                            font: parent.font
                            visible: parent.text === "" && !parent.activeFocus
                        }
                    }
                }
            }

            RippleButton {
                implicitWidth: searchBtnTxt.implicitWidth + 24
                implicitHeight: 38
                buttonRadius: Appearance.rounding.full
                colBackground: Appearance.colors.colPrimary
                onClicked: storePopup.loadStore(1, searchField.text)
                contentItem: StyledText {
                    id: searchBtnTxt
                    anchors.centerIn: parent
                    text: Translation.tr("Search")
                    color: Appearance.m3colors.m3onPrimary
                    font.pixelSize: Appearance.font.pixelSize.small
                    font.weight: Font.Medium
                }
            }
        }

        Flow {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: ["", "anime", "cyberpunk", "nature", "abstract", "space", "gaming"]
                delegate: RippleButton {
                    required property string modelData
                    readonly property bool activeChip: storePopup.searchQuery.toLowerCase() === modelData
                    implicitWidth: chipTxt.implicitWidth + 20
                    implicitHeight: 30
                    buttonRadius: Appearance.rounding.full
                    colBackground: activeChip ? Appearance.colors.colPrimary : Appearance.colors.colLayer2
                    onClicked: {
                        searchField.text = modelData;
                        storePopup.loadStore(1, modelData);
                    }
                    contentItem: StyledText {
                        id: chipTxt
                        anchors.centerIn: parent
                        text: modelData === "" ? Translation.tr("Featured") : modelData.charAt(0).toUpperCase() + modelData.slice(1)
                        color: activeChip ? Appearance.m3colors.m3onPrimary : Appearance.m3colors.m3onSurface
                        font.pixelSize: Appearance.font.pixelSize.smaller
                    }
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            CircularProgress {
                anchors.centerIn: parent
                visible: storePopup.loading
                implicitSize: 38
                lineWidth: 3
                value: 0.72
                enableAnimation: false
                colPrimary: Appearance.colors.colPrimary
                colSecondary: Qt.rgba(1, 1, 1, 0.14)
                RotationAnimator on rotation {
                    running: storePopup.loading && storePopup.visible
                    from: 0; to: 360
                    duration: 900
                    loops: Animation.Infinite
                }
            }

            StyledText {
                anchors.centerIn: parent
                visible: !storePopup.loading && storePopup.items.length === 0
                text: Translation.tr("No wallpapers found")
                color: Appearance.colors.colSubtext
            }

            GridView {
                id: storeGrid
                anchors.fill: parent
                visible: !storePopup.loading && storePopup.items.length > 0
                clip: true
                cellWidth: Math.floor(width / 2)
                cellHeight: 196
                model: storePopup.items

                delegate: Item {
                    required property var modelData
                    width: storeGrid.cellWidth
                    height: storeGrid.cellHeight

                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: 6
                        radius: Appearance.rounding.normal
                        color: Appearance.colors.colLayer2
                        border.width: 1
                        border.color: Appearance.colors.colOutlineVariant

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 6

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                Image {
                                    anchors.fill: parent
                                    source: modelData.thumb
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                    layer.enabled: true
                                    layer.effect: OpacityMask {
                                        maskSource: Rectangle {
                                            width: storeGrid.cellWidth - 28
                                            height: storeGrid.cellHeight - 62
                                            radius: Appearance.rounding.small
                                        }
                                    }
                                }

                                Rectangle {
                                    anchors.top: parent.top
                                    anchors.left: parent.left
                                    anchors.margins: 6
                                    radius: Appearance.rounding.full
                                    color: Qt.rgba(0, 0, 0, 0.65)
                                    implicitWidth: 46
                                    implicitHeight: 20
                                    StyledText {
                                        anchors.centerIn: parent
                                        text: "MP4"
                                        color: "#ffffff"
                                        font.pixelSize: 10
                                        font.weight: Font.Medium
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                StyledText {
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                    text: modelData.title
                                    color: Appearance.m3colors.m3onSurface
                                    font.pixelSize: Appearance.font.pixelSize.smaller
                                }
                                RippleButton {
                                    readonly property bool isBusy: storePopup.downloadingId === modelData.id
                                    enabled: storePopup.downloadingId === ""
                                    Layout.preferredWidth: Math.max(68, applyTxt.implicitWidth + 22)
                                    Layout.preferredHeight: 28
                                    implicitWidth: Layout.preferredWidth
                                    implicitHeight: 28
                                    buttonRadius: Appearance.rounding.full
                                    colBackground: Appearance.colors.colPrimary
                                    onClicked: {
                                        storePopup.downloadingId = modelData.id;
                                        const mon = storePopup.targetMonitor;
                                        downloadProc.command = [
                                            "python3",
                                            Quickshell.shellPath("scripts/colors/live-wallpaper-store.py"),
                                            "download",
                                            modelData.id,
                                            modelData.slug,
                                            mon
                                        ];
                                        downloadProc.running = false;
                                        downloadProc.running = true;
                                    }
                                    contentItem: StyledText {
                                        id: applyTxt
                                        anchors.centerIn: parent
                                        text: isBusy ? Translation.tr("Downloading...") : Translation.tr("Apply")
                                        color: Appearance.m3colors.m3onPrimary
                                        font.pixelSize: 11
                                        font.weight: Font.Medium
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Pagination
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            RippleButton {
                enabled: storePopup.currentPage > 1 && !storePopup.loading
                implicitWidth: prevTxt.implicitWidth + 20
                implicitHeight: 30
                buttonRadius: Appearance.rounding.full
                colBackground: Appearance.colors.colLayer2
                onClicked: storePopup.loadStore(storePopup.currentPage - 1, storePopup.searchQuery)
                contentItem: StyledText {
                    id: prevTxt
                    anchors.centerIn: parent
                    text: Translation.tr("Previous")
                    color: Appearance.m3colors.m3onSurface
                    font.pixelSize: Appearance.font.pixelSize.smaller
                }
            }
            StyledText {
                text: `${storePopup.currentPage}`
                color: Appearance.colors.colSubtext
                font.pixelSize: Appearance.font.pixelSize.small
            }
            RippleButton {
                enabled: !storePopup.loading && storePopup.items.length > 0
                implicitWidth: nextTxt.implicitWidth + 20
                implicitHeight: 30
                buttonRadius: Appearance.rounding.full
                colBackground: Appearance.colors.colLayer2
                onClicked: storePopup.loadStore(storePopup.currentPage + 1, storePopup.searchQuery)
                contentItem: StyledText {
                    id: nextTxt
                    anchors.centerIn: parent
                    text: Translation.tr("Next")
                    color: Appearance.m3colors.m3onSurface
                    font.pixelSize: Appearance.font.pixelSize.smaller
                }
            }
            Item { Layout.fillWidth: true }
        }
    }
}
