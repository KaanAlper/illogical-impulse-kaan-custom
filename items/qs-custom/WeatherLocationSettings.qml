pragma ComponentBehavior: Bound
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

// Shared weather settings: location (GPS, or country -> province -> district, or a city search),
// units and polling interval. The bar weather and the background weather widget read the same
// config (bar.weather), so this one component is used in Settings -> Bar, Background and Services.
ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 12

    readonly property var cfg: Config.options.bar.weather

    // ---- location data (weather-geo.py: dr5hn/countries-states-cities-database)
    property var countries: []
    property var states: []          // [{n, t, lat, lon, c: [[name, lat, lon], ...]}]
    property string dataStatus: ""   // "", "loading", "error"
    property string query: ""
    property var results: []
    property string searchStatus: "" // "", "searching", "empty", "error"
    property bool applying: false

    readonly property string uiLang: {
        const ui = Config.options.language?.ui ?? "auto";
        const name = (ui === "auto" ? Qt.locale().name : ui).replace("_", "-");
        return name === "zh-CN" || name === "pt-BR" ? name : name.split("-")[0];
    }

    function nameOf(item) {
        return item?.t?.[root.uiLang] ?? item?.n ?? "";
    }

    // Sorted by the displayed (localized) name
    function sortedByName(list) {
        return [...list].sort((a, b) => root.nameOf(a).localeCompare(root.nameOf(b), root.uiLang));
    }

    function loadCountries() {
        root.dataStatus = "loading";
        countriesProc.running = false;
        countriesProc.command = ["python3", Quickshell.shellPath("scripts/weather-geo.py"), "countries"];
        countriesProc.running = true;
    }

    function loadCountry(code) {
        root.states = [];
        if (!code) return;
        root.dataStatus = "loading";
        countryProc.running = false;
        countryProc.command = ["python3", Quickshell.shellPath("scripts/weather-geo.py"), "country", code];
        countryProc.running = true;
    }

    function selectedState() {
        return root.states.find(s => s.n === root.cfg.state) ?? null;
    }

    function setLocation(lat, lon, label) {
        root.cfg.city = `${lat},${lon}`;
        root.cfg.label = label;
        root.cfg.enableGPS = false;
    }

    function pickCountry(code) {
        root.cfg.country = code;
        root.cfg.state = "";
        root.cfg.district = "";
        root.cfg.label = "";
        root.cfg.city = "";
        root.loadCountry(code);
    }

    function pickState(name) {
        root.cfg.state = name;
        root.cfg.district = "";
        const s = root.selectedState();
        const country = root.countries.find(c => c.c === root.cfg.country);
        if (s && s.lat != null && s.lon != null)
            root.setLocation(s.lat, s.lon, [root.nameOf(s), root.nameOf(country)].filter(x => x).join(", "));
    }

    function pickDistrict(entry) {
        root.cfg.district = entry[0];
        const s = root.selectedState();
        const country = root.countries.find(c => c.c === root.cfg.country);
        root.setLocation(entry[1], entry[2], [entry[0], root.nameOf(s), root.nameOf(country)].filter(x => x).join(", "));
    }

    function search(text) {
        const q = text.trim();
        if (q.length < 2) {
            root.results = [];
            root.searchStatus = "";
            return;
        }
        root.searchStatus = "searching";
        searchProc.running = false;
        searchProc.command = ["curl", "-s", "-m", "8", `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=6&language=${root.uiLang.split("-")[0]}&format=json`];
        searchProc.running = true;
    }

    function labelOf(place) {
        return [place.name, place.admin1, place.country].filter((x, i, a) => x && a.indexOf(x) === i).join(", ");
    }

    function pickSearchResult(place) {
        root.applying = true;
        root.cfg.country = "";
        root.cfg.state = "";
        root.cfg.district = "";
        root.setLocation(place.latitude, place.longitude, root.labelOf(place));
        root.results = [];
        root.searchStatus = "";
        searchInput.text = "";
        root.applying = false;
    }

    Component.onCompleted: {
        loadCountries();
        loadCountry(cfg.country);
    }

    Timer {
        id: debounce
        interval: 450
        onTriggered: root.search(root.query)
    }

    Process {
        id: countriesProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.countries = JSON.parse(text);
                    root.dataStatus = "";
                } catch (e) {
                    root.dataStatus = "error";
                }
            }
        }
        onExited: (code, status) => {
            if (code !== 0)
                root.dataStatus = "error";
        }
    }

    Process {
        id: countryProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.states = JSON.parse(text).s ?? [];
                    root.dataStatus = "";
                } catch (e) {
                    root.dataStatus = "error";
                }
            }
        }
        onExited: (code, status) => {
            if (code !== 0)
                root.dataStatus = "error";
        }
    }

    Process {
        id: searchProc
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.results = JSON.parse(text).results ?? [];
                    root.searchStatus = root.results.length > 0 ? "" : "empty";
                } catch (e) {
                    root.results = [];
                    root.searchStatus = "error";
                }
            }
        }
        onExited: (code, status) => {
            if (code !== 0) {
                root.results = [];
                root.searchStatus = "error";
            }
        }
    }

    // ---- Location
    ContentSubsection {
        title: Translation.tr("Location")
        tooltip: Translation.tr("Pick \"Automatic\" to detect your location, or choose a place by hand.")

        ConfigSelectionArray {
            Layout.fillWidth: false
            currentValue: root.cfg.enableGPS ? "gps" : "manual"
            onSelected: newValue => {
                root.cfg.enableGPS = newValue === "gps";
            }
            options: [
                {
                    displayName: Translation.tr("Automatic"),
                    icon: "assistant_navigation",
                    value: "gps"
                },
                {
                    displayName: Translation.tr("Choose manually"),
                    icon: "edit_location_alt",
                    value: "manual"
                }
            ]
        }
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 12
        visible: !root.cfg.enableGPS

        StyledText {
            Layout.fillWidth: true
            Layout.leftMargin: 8
            text: root.cfg.label.length > 0 ? Translation.tr("Selected: %1").arg(root.cfg.label) : (root.cfg.city.length > 0 ? Translation.tr("Selected: %1").arg(root.cfg.city) : Translation.tr("No place selected yet"))
            color: Appearance.colors.colSubtext
            font.pixelSize: Appearance.font.pixelSize.small
            elide: Text.ElideRight
        }

        ContentSubsection {
            title: Translation.tr("Country")

            StyledComboBox {
                id: countryBox
                buttonIcon: "public"
                textRole: "displayName"
                model: [
                    {
                        displayName: Translation.tr("Select a country"),
                        value: ""
                    },
                    ...root.sortedByName(root.countries).map(c => ({
                                displayName: root.nameOf(c),
                                value: c.c
                            }))
                ]
                currentIndex: {
                    const i = model.findIndex(m => m.value === root.cfg.country);
                    return i !== -1 ? i : 0;
                }
                onActivated: index => root.pickCountry(model[index].value)
            }
        }

        ContentSubsection {
            title: Translation.tr("Province / State")
            visible: root.cfg.country !== ""

            StyledComboBox {
                id: stateBox
                buttonIcon: "location_city"
                textRole: "displayName"
                model: [
                    {
                        displayName: Translation.tr("Select a province"),
                        value: ""
                    },
                    ...root.sortedByName(root.states).map(s => ({
                                displayName: root.nameOf(s),
                                value: s.n
                            }))
                ]
                currentIndex: {
                    const i = model.findIndex(m => m.value === root.cfg.state);
                    return i !== -1 ? i : 0;
                }
                onActivated: index => root.pickState(model[index].value)
            }
        }

        ContentSubsection {
            title: Translation.tr("District / City")
            visible: root.cfg.state !== ""

            StyledComboBox {
                id: districtBox
                buttonIcon: "pin_drop"
                textRole: "displayName"
                readonly property var entries: root.selectedState()?.c ?? []
                model: [
                    {
                        displayName: Translation.tr("Whole province"),
                        value: ""
                    },
                    ...entries.map((e, i) => ({
                                displayName: e[0],
                                value: e[0],
                                index: i
                            }))
                ]
                currentIndex: {
                    const i = model.findIndex(m => m.value === root.cfg.district);
                    return i !== -1 ? i : 0;
                }
                onActivated: index => {
                    if (index === 0)
                        root.pickState(root.cfg.state);
                    else
                        root.pickDistrict(entries[model[index].index]);
                }
            }
        }

        StyledText {
            visible: root.dataStatus !== ""
            Layout.fillWidth: true
            Layout.leftMargin: 8
            text: root.dataStatus === "loading" ? Translation.tr("Loading...") : Translation.tr("Could not load location data. Check your internet connection.")
            color: root.dataStatus === "error" ? Appearance.colors.colError : Appearance.colors.colSubtext
            font.pixelSize: Appearance.font.pixelSize.smaller
        }

        ContentSubsection {
            title: Translation.tr("Or search for a place")

            MaterialTextArea {
                id: searchInput
                Layout.fillWidth: true
                placeholderText: Translation.tr("Search for a city")
                wrapMode: TextEdit.Wrap
                onTextChanged: {
                    if (root.applying)
                        return;
                    root.query = text;
                    debounce.restart();
                }
            }

            StyledText {
                visible: root.searchStatus !== ""
                Layout.fillWidth: true
                Layout.leftMargin: 8
                text: root.searchStatus === "searching" ? Translation.tr("Searching...") : root.searchStatus === "empty" ? Translation.tr("No matching city found") : Translation.tr("Could not search cities. Check your internet connection.")
                color: root.searchStatus === "error" ? Appearance.colors.colError : Appearance.colors.colSubtext
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
                    onClicked: root.pickSearchResult(resultButton.modelData)
                }
            }
        }
    }

    // ---- Units
    ContentSubsection {
        title: Translation.tr("Temperature unit")

        ConfigSelectionArray {
            Layout.fillWidth: false
            currentValue: root.cfg.useUSCS ? "f" : "c"
            onSelected: newValue => {
                root.cfg.useUSCS = newValue === "f";
            }
            options: [
                {
                    displayName: Translation.tr("Celsius (°C)"),
                    icon: "device_thermostat",
                    value: "c"
                },
                {
                    displayName: Translation.tr("Fahrenheit (°F)"),
                    icon: "thermometer",
                    value: "f"
                }
            ]
        }
    }

    // ---- Refresh
    ContentSubsection {
        title: Translation.tr("Refresh")

        ConfigSpinBox {
            icon: "av_timer"
            text: Translation.tr("Polling interval (m)")
            value: root.cfg.fetchInterval
            from: 5
            to: 50
            stepSize: 5
            onValueChanged: {
                root.cfg.fetchInterval = value;
            }
        }
    }
}
