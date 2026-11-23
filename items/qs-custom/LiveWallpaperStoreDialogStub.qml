import QtQuick

// Placeholder used when the "live-video" feature is not installed: hides the Live Store button
Item {
    property string targetMonitor: ""
    readonly property bool available: false
    function open() {}
}
