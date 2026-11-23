pragma ComponentBehavior: Bound
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts
import Quickshell.Io

// Shared weather settings: location (GPS or a searched city), units and polling interval.
// The bar weather and the background weather widget read the same config (bar.weather),
// so this one component is used in Settings -> Bar, Background and Services.
ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 8

    readonly property var weatherConfig: Config.options.bar.weather
    property var results: []
    property string status: "" // "", "searching", "empty", "error"
    property string query: ""
    property bool applying: false

    function search(text) {
        const q = text.trim();
        if (q.length < 2) {
            root.results = [];
            root.status = "";
            return;
        }
        root.status = "searching";
        searchProc.running = false;
        searchProc.command = ["curl", "-s", "-m", "8", `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=6&language=en&format=json`];
        searchProc.running = true;
    }

    function labelOf(place) {
        return [place.name, place.admin1, place.country].filter((x, i, a) => x && a.indexOf(x) === i).join(", ");
    }

    function choose(place) {
        root.applying = true;
        // wttr.in understands "City,Country"
        root.weatherConfig.city = `${place.name},${place.country ?? ""}`.replace(/,$/, "");
        root.weatherConfig.enableGPS = false;
        root.results = [];
        root.status = "";
        cityInput.text = root.labelOf(place);
        root.applying = false;
    }

    Timer {
        id: debounce
        interval: 450
        onTriggered: root.search(root.query)
    }

    Process {
        id: searchProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    root.results = data.results ?? [];
                    root.status = root.results.length > 0 ? "" : "empty";
                } catch (e) {
                    root.results = [];
                    root.status = "error";
                }
            }
        }
        onExited: (code, status) => {
            if (code !== 0) {
                root.results = [];
                root.status = "error";
            }
        }
    }

    ConfigRow {
        ConfigSwitch {
            buttonIcon: "assistant_navigation"
            text: Translation.tr("Enable GPS based location")
            checked: root.weatherConfig.enableGPS
            onCheckedChanged: {
                root.weatherConfig.enableGPS = checked;
            }
        }
        ConfigSwitch {
            buttonIcon: "thermometer"
            text: Translation.tr("Fahrenheit unit")
            checked: root.weatherConfig.useUSCS
            onCheckedChanged: {
                root.weatherConfig.useUSCS = checked;
            }
            StyledToolTip {
                text: Translation.tr("It may take a few seconds to update")
            }
        }
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6
        visible: !root.weatherConfig.enableGPS

        StyledText {
            Layout.fillWidth: true
            Layout.leftMargin: 8
            text: root.weatherConfig.city.length > 0 ? Translation.tr("Current location: %1").arg(root.weatherConfig.city) : Translation.tr("No city selected")
            color: Appearance.colors.colSubtext
            font.pixelSize: Appearance.font.pixelSize.smaller
            elide: Text.ElideRight
        }

        MaterialTextArea {
            id: cityInput
            Layout.fillWidth: true
            placeholderText: Translation.tr("Search for a city")
            wrapMode: TextEdit.Wrap
            Component.onCompleted: text = root.weatherConfig.city
            onTextChanged: {
                if (root.applying)
                    return;
                root.query = text;
                debounce.restart();
            }
        }

        StyledText {
            visible: root.status !== ""
            Layout.fillWidth: true
            Layout.leftMargin: 8
            text: root.status === "searching" ? Translation.tr("Searching...") : root.status === "empty" ? Translation.tr("No matching city found") : Translation.tr("Could not search cities. Check your internet connection.")
            color: root.status === "error" ? Appearance.colors.colError : Appearance.colors.colSubtext
            font.pixelSize: Appearance.font.pixelSize.smaller
        }

        Repeater {
            model: root.results
            delegate: RippleButtonWithIcon {
                id: resultButton
                required property var modelData
                Layout.fillWidth: true
                buttonRadius: Appearance.rounding.small
                materialIcon: "location_on"
                mainText: root.labelOf(resultButton.modelData)
                onClicked: root.choose(resultButton.modelData)
            }
        }
    }

    ConfigSpinBox {
        icon: "av_timer"
        text: Translation.tr("Polling interval (m)")
        value: root.weatherConfig.fetchInterval
        from: 5
        to: 50
        stepSize: 5
        onValueChanged: {
            root.weatherConfig.fetchInterval = value;
        }
    }
}
