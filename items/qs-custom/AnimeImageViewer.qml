import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland

PanelWindow {
    id: root
    required property string sourceUrl
    property string previewUrl: ""
    property string tags: ""
    signal closeRequested()

    WlrLayershell.namespace: "quickshell:animeViewer"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    color: "transparent"

    Item {
        id: keyScope
        anchors.fill: parent
        focus: true
        Keys.onEscapePressed: root.closeRequested()

        Rectangle {
            anchors.fill: parent
            color: "#cc000000"

            MouseArea {
                anchors.fill: parent
                onClicked: root.closeRequested()
            }
        }

        // Preview image shown underneath while full-res loads
        Image {
            id: previewImg
            anchors.centerIn: parent
            width: Math.min(parent.width * 0.9, implicitWidth > 0 ? implicitWidth : parent.width * 0.9)
            height: Math.min(parent.height * 0.9, implicitHeight > 0 ? implicitHeight : parent.height * 0.9)
            source: root.previewUrl
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            smooth: true
            visible: root.previewUrl !== "" && fullImg.status !== Image.Ready
        }

        // Full-size image
        Image {
            id: fullImg
            anchors.centerIn: parent
            width: parent.width * 0.92
            height: parent.height * 0.92
            source: root.sourceUrl
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            smooth: true
            cache: true

            MouseArea {
                anchors.fill: parent
                // Consume clicks on the image area so only backdrop/Esc/Close dismisses
                onClicked: mouse => mouse.accepted = true
            }
        }

        // Loading indicator while full-size image is fetching
        Rectangle {
            anchors.centerIn: parent
            visible: fullImg.status === Image.Loading
            color: "#aa000000"
            radius: Appearance.rounding.full
            implicitWidth: loadingRow.implicitWidth + 24
            implicitHeight: loadingRow.implicitHeight + 16

            RowLayout {
                id: loadingRow
                anchors.centerIn: parent
                spacing: 8
                MaterialLoadingIndicator {
                    implicitSize: 20
                }
                StyledText {
                    text: Translation.tr("Loading full image...")
                    color: "#ffffff"
                    font.pixelSize: Appearance.font.pixelSize.small
                }
            }
        }

        // Top-right action pill
        Rectangle {
            anchors {
                top: parent.top
                right: parent.right
                topMargin: 20
                rightMargin: 20
            }
            radius: Appearance.rounding.full
            color: Appearance.colors.colLayer2
            border.color: Appearance.colors.colLayer3
            border.width: 1
            implicitWidth: actionRow.implicitWidth + 12
            implicitHeight: actionRow.implicitHeight + 8

            RowLayout {
                id: actionRow
                anchors.centerIn: parent
                spacing: 4

                RippleButton {
                    implicitWidth: 34
                    implicitHeight: 34
                    buttonRadius: Appearance.rounding.full
                    onClicked: Qt.openUrlExternally(root.sourceUrl)
                    contentItem: MaterialSymbol {
                        anchors.centerIn: parent
                        text: "open_in_new"
                        iconSize: 18
                        color: Appearance.colors.colOnLayer2
                    }
                    StyledToolTip {
                        text: Translation.tr("Open in browser")
                    }
                }

                RippleButton {
                    implicitWidth: 34
                    implicitHeight: 34
                    buttonRadius: Appearance.rounding.full
                    onClicked: Quickshell.clipboardText = root.sourceUrl
                    contentItem: MaterialSymbol {
                        anchors.centerIn: parent
                        text: "content_copy"
                        iconSize: 18
                        color: Appearance.colors.colOnLayer2
                    }
                    StyledToolTip {
                        text: Translation.tr("Copy URL")
                    }
                }

                RippleButton {
                    implicitWidth: 34
                    implicitHeight: 34
                    buttonRadius: Appearance.rounding.full
                    onClicked: root.closeRequested()
                    contentItem: MaterialSymbol {
                        anchors.centerIn: parent
                        text: "close"
                        iconSize: 18
                        color: Appearance.colors.colOnLayer2
                    }
                    StyledToolTip {
                        text: Translation.tr("Close (Esc)")
                    }
                }
            }
        }
    }
}
