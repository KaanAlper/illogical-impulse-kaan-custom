import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

// Ultra-light Wayland curtain matching Plymouth XANA logo so the desktop never
// flashes between Plymouth handoff and Quickshell LockScreen (WlSessionLock).
ShellRoot {
    Variants {
        model: Quickshell.screens
        delegate: PanelWindow {
            required property var modelData
            screen: modelData
            color: "#000000"
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "quickshell:bootsplash"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            anchors {
                top: true
                bottom: true
                left: true
                right: true
            }

            Image {
                anchors.centerIn: parent
                source: Qt.resolvedUrl("watermark.png")
                width: 252
                height: 360
                fillMode: Image.PreserveAspectFit
                smooth: true
            }
        }
    }

    // Exit cleanly once `qs -c ii` + LockScreen (WlSessionLock) have taken over
    Process {
        running: true
        command: [
            "bash", "-c",
            "for i in $(seq 1 80); do qs ipc -c ii show >/dev/null 2>&1 && sleep 0.6 && break; sleep 0.1; done"
        ]
        onExited: Qt.quit()
    }

    // Hard safety timeout: never stay on screen more than 8 seconds
    Timer {
        interval: 8000
        running: true
        repeat: false
        onTriggered: Qt.quit()
    }
}
