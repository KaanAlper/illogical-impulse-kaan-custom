pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Services.Pipewire
import Qt5Compat.GraphicalEffects
import qs.services
import qs.modules.common
import qs.modules.common.widgets

/**
 * Bar button with a per-app volume mixer popup (EarTrumpet-style), ported from Logical Lunge's native bar.
 * Click the icon to open a popup with the default output device and every app playing sound on it:
 * - the device row and one row per app, each with its icon, name, slider and percentage;
 * - an app's streams (a browser has several) are grouped into one row and set together;
 * - clicking an app's icon mutes / unmutes it; moving a muted app's slider unmutes it;
 * - the mouse wheel over a row changes it by 5 % a notch, like the bar's volume wheel;
 * - apps are named after their window: Electron/Chromium-based apps report themselves as "Chromium", so the
 *   stream's process is walked up to the process that owns a Hyprland window, and that window's app is shown.
 * A click outside closes the popup (HyprlandFocusGrab), like the tray overflow popup.
 *
 * Sibling of AudioMonoToggle / AudioOutputSwitcher (independent; none touches the others).
 */
MouseArea {
    id: root

    property bool popupOpen: false
    readonly property real wheelStep: 0.05
    // stream process id -> { pids: [...], hint: "..." } (filled by ancestryProc)
    property var ancestry: ({})

    // One entry per app: { key, name, icon, nodes: [PwNode] }; playback streams of the default output only
    readonly property var apps: {
        const groups = {};
        const order = [];
        for (const node of Audio.outputAppNodes) {
            const p = node.properties ?? {};
            const win = root.windowFor(node);
            const entry = win ? null : root.desktopEntryForNode(node);
            const key = win ? `pid:${win.pid}`
                : entry ? `app:${entry.id}`
                : (p["application.process.binary"] || p["application.name"] || node.name);
            if (!groups[key]) {
                groups[key] = {
                    key: key,
                    name: win ? root.appNameFor(win) : (entry?.name || Audio.appNodeDisplayName(node)),
                    icon: win ? Quickshell.iconPath(AppSearch.guessIcon(win.class), "image-missing")
                        : entry ? Quickshell.iconPath(AppSearch.guessIcon(entry.icon || entry.id), "image-missing")
                        : root.iconFor(node),
                    nodes: []
                };
                order.push(key);
            }
            groups[key].nodes.push(node);
        }
        return order.map(k => groups[k]);
    }

    // The Hyprland window owned by the stream's process or one of its ancestors (null if none)
    function windowFor(node) {
        const pid = parseInt(node?.properties?.["application.process.id"] ?? "");
        if (!pid) return null;
        const info = root.ancestry[pid];
        const chain = info?.pids ?? [pid];
        for (const id of chain) {
            const w = HyprlandData.windowList.find(w => w.pid === id);
            if (w) return w;
        }
        return null;
    }

    function desktopEntryForNode(node) {
        const pid = parseInt(node?.properties?.["application.process.id"] ?? "");
        const hint = (pid ? root.ancestry[pid]?.hint : "") ?? "";
        if (!hint) return null;
        const h = hint.toLowerCase();
        return DesktopEntries.applications.values.find(a =>
            (a.startupClass ?? "").toLowerCase() === h ||
            (a.icon ?? "").toLowerCase() === h ||
            (a.id ?? "").toLowerCase() === h ||
            (a.execString ?? "").toLowerCase().includes(h) ||
            (a.id ?? "").toLowerCase().includes(h)
        ) ?? null;
    }

    function appNameFor(win) {
        const cls = (win.class ?? "").toLowerCase();
        const e = DesktopEntries.applications.values.find(a => (a.startupClass ?? "").toLowerCase() === cls)
            ?? DesktopEntries.byId(win.class);
        return e?.name || win.initialTitle || win.title || win.class;
    }

    function refreshAncestry() {
        const pids = Audio.outputAppNodes.map(n => parseInt(n?.properties?.["application.process.id"] ?? "")).filter(p => p > 0);
        if (pids.length === 0) return;
        ancestryProc.command = ["python3", "-c",
            "import os,sys,json\n" +
            "def hint_for(pid):\n" +
            "    try:\n" +
            "        args=[a for a in open(f'/proc/{pid}/cmdline','rb').read().split(b'\\0') if a]\n" +
            "        s=[a.decode('utf-8','ignore') for a in args]\n" +
            "    except Exception: return ''\n" +
            "    joined=' '.join(s)\n" +
            "    if '--type=' in joined: return ''\n" +
            "    for a in s:\n" +
            "        if a.startswith('--class=') or a.startswith('--app-id='): return a.split('=',1)[1]\n" +
            "        if 'app.asar' in a or a.endswith('.asar'):\n" +
            "            parts=[p for p in os.path.dirname(a).split('/') if p and p not in ('usr','lib','opt','share','resources','app')]\n" +
            "            if parts: return parts[-1]\n" +
            "    if s:\n" +
            "        first=s[0].split(' --',1)[0].strip()\n" +
            "        b=os.path.basename(first)\n" +
            "        if b and not b.startswith(('electron','python','node','bash','sh')):\n" +
            "            return b\n" +
            "    return ''\n" +
            "res={}\n" +
            "for p in sys.argv[1:]:\n" +
            "    pid=int(p); chain=[pid]; q=pid; h=''\n" +
            "    for _ in range(8):\n" +
            "        h = hint_for(q) or h\n" +
            "        try: ppid=int(open(f'/proc/{q}/stat').read().split(')')[1].split()[1])\n" +
            "        except Exception: break\n" +
            "        if ppid<=1: break\n" +
            "        chain.append(ppid); q=ppid\n" +
            "    res[str(pid)]={'pids':chain,'hint':h}\n" +
            "print(json.dumps(res))",
            ...pids.map(String)];
        ancestryProc.running = true;
    }

    Process {
        id: ancestryProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.ancestry = JSON.parse(text.trim() || "{}");
                } catch (e) {}
            }
        }
    }
    Connections {
        target: Audio
        function onOutputAppNodesChanged() {
            root.refreshAncestry();
        }
    }
    Component.onCompleted: Qt.callLater(root.refreshAncestry)

    function iconFor(node) {
        const p = node?.properties ?? {};
        for (const name of [p["application.icon-name"], p["application.process.binary"], p["application.name"], p["node.name"]]) {
            if (!name) continue;
            const icon = AppSearch.guessIcon(name);
            if (AppSearch.iconExists(icon)) return Quickshell.iconPath(icon, "image-missing");
        }
        return Quickshell.iconPath("audio-volume-high", "image-missing");
    }

    // Group helpers: the row shows the loudest stream; setting it sets every stream of the app
    function groupVolume(nodes) {
        return nodes.reduce((m, n) => Math.max(m, n?.audio?.volume ?? 0), 0);
    }
    function groupMuted(nodes) {
        return nodes.length > 0 && nodes.every(n => n?.audio?.muted ?? false);
    }
    function setGroupVolume(nodes, v) {
        const vol = Math.max(0, Math.min(1, v));
        for (const n of nodes) {
            if (!n?.audio) continue;
            n.audio.volume = vol;
            if (n.audio.muted) n.audio.muted = false; // moving a muted app's slider unmutes it
        }
    }
    function toggleGroupMute(nodes) {
        const mute = !root.groupMuted(nodes);
        for (const n of nodes) if (n?.audio) n.audio.muted = mute;
    }

    hoverEnabled: true
    cursorShape: Qt.PointingHandCursor
    acceptedButtons: Qt.LeftButton
    implicitWidth: icon.implicitWidth
    implicitHeight: icon.implicitHeight

    onClicked: root.popupOpen = !root.popupOpen
    onPopupOpenChanged: {
        focusGrab.active = root.popupOpen;
        if (root.popupOpen) root.refreshAncestry();
    }

    // Bind the nodes only while the popup is open, so their volume/mute properties are live
    PwObjectTracker {
        objects: root.popupOpen ? [Audio.sink, ...Audio.outputAppNodes] : []
    }

    // Click anywhere outside the popup window closes it.
    HyprlandFocusGrab {
        id: focusGrab
        active: false
        windows: [mixerColumn?.QsWindow?.window]
        onCleared: root.popupOpen = false
    }

    MaterialSymbol {
        id: icon
        anchors.centerIn: parent
        text: "instant_mix"
        iconSize: Appearance.font.pixelSize.larger
        color: root.popupOpen ? Appearance.colors.colPrimary : Appearance.colors.colOnLayer0

        Behavior on color {
            animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this)
        }
    }

    // One mixer row: icon (click mutes), name, slider, percentage; wheel changes it by 5 %
    component MixerRow: MouseArea {
        id: row
        required property string name
        required property string iconSource
        required property string fallbackSymbol
        required property real volume
        required property bool muted
        signal volumeRequested(real v)
        signal muteToggled()

        Layout.fillWidth: true
        implicitWidth: 300
        implicitHeight: rowLayout.implicitHeight + 8
        acceptedButtons: Qt.NoButton
        onWheel: wheel => {
            const notches = wheel.angleDelta.y / 120;
            if (notches !== 0) row.volumeRequested(row.volume + notches * root.wheelStep);
        }

        RowLayout {
            id: rowLayout
            anchors.fill: parent
            anchors.leftMargin: 6
            anchors.rightMargin: 6
            spacing: 8

            MouseArea {
                Layout.preferredWidth: 30
                Layout.preferredHeight: 30
                cursorShape: Qt.PointingHandCursor
                onClicked: row.muteToggled()

                StyledImage {
                    id: appIcon
                    anchors.fill: parent
                    visible: false
                    source: row.iconSource
                }
                Desaturate {
                    anchors.fill: appIcon
                    source: appIcon
                    visible: row.iconSource !== ""
                    desaturation: row.muted ? 1.0 : 0.0
                    opacity: row.muted ? 0.4 : 1.0
                }
                MaterialSymbol {
                    anchors.centerIn: parent
                    visible: row.iconSource === "" || row.muted
                    text: row.muted ? "volume_off" : row.fallbackSymbol
                    iconSize: 22
                    color: Appearance.colors.colOnLayer1
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: -4
                StyledText {
                    Layout.fillWidth: true
                    text: row.name
                    elide: Text.ElideRight
                    font.pixelSize: Appearance.font.pixelSize.small
                    color: Appearance.colors.colSubtext
                }
                StyledSlider {
                    Layout.fillWidth: true
                    configuration: StyledSlider.Configuration.S
                    value: row.volume
                    onMoved: row.volumeRequested(value)
                }
            }

            StyledText {
                Layout.preferredWidth: 36
                horizontalAlignment: Text.AlignRight
                text: `${Math.round(row.volume * 100)}%`
                font.pixelSize: Appearance.font.pixelSize.small
                color: row.muted ? Appearance.colors.colSubtext : Appearance.colors.colOnLayer1
            }
        }
    }

    StyledPopup {
        id: popup
        hoverTarget: root
        active: root.popupOpen

        ColumnLayout {
            id: mixerColumn
            spacing: 4

            // Default output device
            MixerRow {
                name: Audio.sink ? Audio.friendlyDeviceName(Audio.sink) : Translation.tr("No output device")
                iconSource: ""
                fallbackSymbol: "speaker"
                volume: Audio.sink?.audio?.volume ?? 0
                muted: Audio.sink?.audio?.muted ?? false
                onVolumeRequested: v => {
                    if (!Audio.sink?.audio) return;
                    Audio.sink.audio.volume = Math.max(0, Math.min(1, v));
                    if (Audio.sink.audio.muted) Audio.sink.audio.muted = false;
                }
                onMuteToggled: if (Audio.sink?.audio) Audio.sink.audio.muted = !Audio.sink.audio.muted
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                implicitHeight: 1
                color: Appearance.colors.colOutlineVariant
                visible: root.apps.length > 0
            }

            Repeater {
                model: root.apps
                delegate: MixerRow {
                    required property var modelData
                    name: modelData.name
                    iconSource: modelData.icon
                    fallbackSymbol: "music_note"
                    volume: root.groupVolume(modelData.nodes)
                    muted: root.groupMuted(modelData.nodes)
                    onVolumeRequested: v => root.setGroupVolume(modelData.nodes, v)
                    onMuteToggled: root.toggleGroupMute(modelData.nodes)
                }
            }

            StyledText {
                Layout.fillWidth: true
                Layout.margins: 6
                visible: root.apps.length === 0
                text: Translation.tr("No apps are playing sound")
                font.pixelSize: Appearance.font.pixelSize.small
                color: Appearance.colors.colSubtext
            }
        }
    }
}
