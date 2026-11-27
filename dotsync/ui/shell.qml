// dotsync arayüzü: logical-lunge kurulum penceresinin görsel dili (M3 koyu, lila vurgu, kayan sayfalar).
// Yalnızca ön yüz: tüm iş `dotsync.py status|apply` çıktısından gelir (JSON / JSON satırları).
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

ShellRoot {
    id: root

    // ---- palet (logical-lunge Setup.cs ile aynı)
    readonly property color cBg: "#141218"
    readonly property color cSurface: "#1d1b20"
    readonly property color cSurface2: "#2b2930"
    readonly property color cOutline: "#49454f"
    readonly property color cOutlineSoft: Qt.rgba(1, 1, 1, 0.12)
    readonly property color cFg: "#e6e0e9"
    readonly property color cSub: "#cac4d0"
    readonly property color cDim: "#938f99"
    readonly property color cOk: "#a8dab5"
    readonly property color cErr: "#f2b8b5"
    readonly property color cAccent: "#b69df8"

    readonly property string bin: Quickshell.env("DOTSYNC_BIN") || (Quickshell.env("HOME") + "/.local/share/dotsync/client/dotsync.py")

    // Modlar: boot (varsayılan, yalnızca eksik varsa açılır) | setup (her zaman açılır) |
    // bootstrap (ilk kurulum: önce installer'ın kendisi kurulur, sonra setup gibi devam eder)
    readonly property string bootstrapPath: Quickshell.env("DOTSYNC_BOOTSTRAP") || ""
    readonly property bool bootstrapMode: bootstrapPath !== ""
    readonly property bool setupMode: bootstrapMode || Quickshell.env("DOTSYNC_MODE") === "setup"

    // 0 = installer kurulumu (yalnızca ilk kurulumda), 1 = eksikler, 2 = ilerleme, 3 = sonuç
    readonly property int firstPage: bootstrapMode ? 0 : 1
    property int page: firstPage
    property bool nothingToDo: false
    property bool bootFailed: false
    property bool loading: true
    property string loadError: ""
    property int selectedCount: 0
    property int applyTotal: 0
    property int applyDone: 0
    property bool allOk: true
    property bool deferredOnly: false
    property bool pwMode: false             // true: kurulum terminalsiz, uygulama içi parola ile arka planda

    // Yönetici onayı: 0 yok, 1 eksik bağımlılıklar (İndir / Daha sonra), 2 parola
    property int dlgStep: 0
    property bool dlgBusy: false
    property string dlgError: ""
    property string pendingPw: ""
    readonly property string sudoBin: Quickshell.env("DOTSYNC_SUDO") || "sudo"
    ListModel { id: adminItems }    // title, missing

    ListModel {
        id: bootSteps
        ListElement { sid: "deps"; label: "Gerekli araçlar denetleniyor"; st: "wait" }
        ListElement { sid: "client"; label: "Installer (dotsync) kuruluyor"; st: "wait" }
        ListElement { sid: "cache"; label: "Ayar deposu hazırlanıyor"; st: "wait" }
    }
    ListModel { id: items }      // id,title,desc,kind,terminal,missing,checked,partial,expanded,featuresJson,runState,detail
    ListModel { id: installedItems }
    property bool showInstalled: false
    ListModel { id: resultRows }

    function _syncParentFromFeats(idx, feats) {
        var total = 0, sel = 0;
        for (var j = 0; j < feats.length; j++) {
            var f = feats[j];
            var sub = f.features || [];
            if (sub.length > 0) {
                var subSel = 0;
                for (var k = 0; k < sub.length; k++) if (sub[k].checked) subSel++;
                f.checked = subSel > 0;
                f.partial = subSel > 0 && subSel < sub.length;
                total += sub.length;
                sel += subSel;
            } else {
                total += 1;
                if (f.checked) sel += 1;
            }
        }
        list.keepScroll(function() { items.setProperty(idx, "featuresJson", JSON.stringify(feats)); });
        items.setProperty(idx, "checked", sel > 0);
        items.setProperty(idx, "partial", sel > 0 && sel < total);
        root.recount();
    }

    function toggleAllFeatures(idx, newVal) {
        var it = items.get(idx);
        var feats = JSON.parse(it.featuresJson || "[]");
        for (var j = 0; j < feats.length; j++) {
            feats[j].checked = newVal;
            feats[j].partial = false;
            var sub = feats[j].features || [];
            for (var k = 0; k < sub.length; k++) sub[k].checked = newVal;
        }
        list.keepScroll(function() { items.setProperty(idx, "featuresJson", JSON.stringify(feats)); });
        items.setProperty(idx, "checked", newVal);
        items.setProperty(idx, "partial", false);
        root.recount();
    }

    function toggleSubFeature(idx, featIdx) {
        var it = items.get(idx);
        var feats = JSON.parse(it.featuresJson || "[]");
        if (featIdx < 0 || featIdx >= feats.length) return;
        var f = feats[featIdx];
        var sub = f.features || [];
        if (sub.length > 0) {
            var newVal = !(f.checked && !f.partial);
            f.checked = newVal;
            f.partial = false;
            for (var k = 0; k < sub.length; k++) sub[k].checked = newVal;
        } else {
            f.checked = !f.checked;
        }
        root._syncParentFromFeats(idx, feats);
    }

    function toggleNestedFeature(idx, featIdx, subIdx) {
        var it = items.get(idx);
        var feats = JSON.parse(it.featuresJson || "[]");
        if (featIdx < 0 || featIdx >= feats.length) return;
        var sub = feats[featIdx].features || [];
        if (subIdx < 0 || subIdx >= sub.length) return;
        sub[subIdx].checked = !sub[subIdx].checked;
        root._syncParentFromFeats(idx, feats);
    }

    function toggleFeatureExpand(idx, featIdx) {
        var it = items.get(idx);
        var feats = JSON.parse(it.featuresJson || "[]");
        if (featIdx < 0 || featIdx >= feats.length) return;
        feats[featIdx].expanded = !feats[featIdx].expanded;
        list.keepScroll(function() { items.setProperty(idx, "featuresJson", JSON.stringify(feats)); });
    }

    // Katalog görünümü: kimlikten tutarlı bir renk tonu ve baş harf rozeti
    function hueOf(id) { var h = 0; for (var i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) % 360; return h / 360; }
    function badgeColor(id) { return Qt.hsla(hueOf(id), 0.55, 0.62, 0.22); }
    function badgeFg(id) { return Qt.hsla(hueOf(id), 0.75, 0.80, 1); }
    function initialOf(title) { return (title || "?").trim().charAt(0).toUpperCase(); }

    function recount() {
        var n = 0;
        for (var i = 0; i < items.count; i++) if (items.get(i).checked) n++;
        selectedCount = n;
    }

    function load() {
        loading = true;
        loadError = "";
        statusProc.running = true;
    }

    function needsAdmin(it) { return it.terminal || it.kind === "pkgs"; }

    // "Seçilenleri indir": yönetici gerektiren eksik varsa önce popup
    function requestApply() {
        adminItems.clear();
        for (var i = 0; i < items.count; i++) {
            var it = items.get(i);
            if (!it.checked) continue;
            if (needsAdmin(it)) adminItems.append({ title: it.title, missing: it.missing });
            var fl = JSON.parse(it.featuresJson || "[]");
            for (var j = 0; j < fl.length; j++) {
                var sub = fl[j].features || [];
                var cand = sub.length > 0 ? sub : [fl[j]];
                for (var k = 0; k < cand.length; k++) {
                    var c = cand[k];
                    if (c.checked && c.needs && c.needs.length > 0)
                        adminItems.append({ title: c.title, missing: c.needs.join(", ") });
                }
            }
        }
        if (adminItems.count === 0) { startApply(false); return; }
        dlgError = ""; dlgBusy = false; pendingPw = "";
        dlgStep = 1;
    }

    // "Daha sonra": yönetici gerektirenler atlanır, reddedilmiş sayılmaz (bir sonraki açılışta tekrar sorulur)
    function deferAdmin() {
        dlgStep = 0;
        startApply(false, true);
    }

    function submitPassword(pw) {
        if (dlgBusy || pw === "") return;
        dlgError = ""; dlgBusy = true; pendingPw = pw;
        pwCheckProc.running = true;
        pwWriteTimer.target = pwCheckProc; pwWriteTimer.restart();
    }

    function startApply(usePw, later) {
        var ids = [], declines = [], featArgs = [];
        for (var i = 0; i < items.count; i++) {
            var it = items.get(i);
            if (later && it.checked && needsAdmin(it)) {
                items.setProperty(i, "runState", "skip");
                continue;
            }
            if (it.checked) {
                ids.push(it.id);
                var feats = JSON.parse(it.featuresJson || "[]");
                if (feats.length > 0) {
                    var chosen = [], totalFeats = 0;
                    for (var j = 0; j < feats.length; j++) {
                        var sub = feats[j].features || [];
                        if (sub.length > 0) {
                            totalFeats += sub.length;
                            for (var k = 0; k < sub.length; k++) if (sub[k].checked) chosen.push(sub[k].id);
                        } else {
                            totalFeats += 1;
                            if (feats[j].checked) chosen.push(feats[j].id);
                        }
                    }
                    if (chosen.length < totalFeats) {
                        featArgs.push(it.id + ":" + chosen.join(","));
                    } else if (feats.length > 0 && chosen.length === totalFeats) {
                        featArgs.push(it.id + ":" + chosen.join(","));
                    }
                }
            } else {
                declines.push(it.id);
            }
            items.setProperty(i, "runState", it.checked ? "wait" : "skip");
        }
        var args = ["python3", root.bin, "apply"].concat(ids);
        if (declines.length) args = args.concat(["--decline"]).concat(declines);
        if (featArgs.length) args = args.concat(["--features"]).concat(featArgs);
        if (usePw) args = args.concat(["--password-stdin"]);
        if (later) args = args.concat(["--skip-feature-install"]);
        pwMode = !!usePw;
        deferredOnly = !!later && ids.length === 0;
        applyProc.command = args;
        applyTotal = ids.length;
        applyDone = 0;
        allOk = true;
        if (ids.length === 0 && declines.length === 0) { page = 3; return; }
        page = 2;
        applyProc.running = true;
        if (usePw) { pwWriteTimer.target = applyProc; pwWriteTimer.restart(); }
    }

    function setRun(id, state, detail) {
        for (var i = 0; i < items.count; i++) {
            if (items.get(i).id === id) {
                var prev = items.get(i).runState;
                items.setProperty(i, "runState", state);
                items.setProperty(i, "detail", detail || "");
                if (state === "fail") allOk = false;
                if ((state === "ok" || state === "fail") && prev !== "ok" && prev !== "fail") applyDone++;
            }
        }
    }

    function onEvent(line) {
        if (!line) return;
        var e;
        try { e = JSON.parse(line); } catch (err) { return; }
        if (e.event === "start") setRun(e.id, "run", "");
        else if (e.event === "done") setRun(e.id, e.ok ? "ok" : "fail", e.detail);
        else if (e.event === "error") { allOk = false; loadError = e.detail; }
        else if (e.event === "finished") page = 3;
    }

    Process {
        id: statusProc
        command: root.setupMode ? ["python3", root.bin, "status", "--include-declined"] : ["python3", root.bin, "status"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var data = JSON.parse(text);
                    items.clear();
                    installedItems.clear();
                    for (var i = 0; i < data.items.length; i++) {
                        var s = data.items[i];
                        var isInstalled = (s.state === "ok");
                        if (!isInstalled && (s.state !== "missing" || s.declined)) continue;
                        var defChecked = isInstalled ? true : (s.default !== false);
                        var rawFeats = s.features || [];
                        var feats = [];
                        for (var j = 0; j < rawFeats.length; j++) {
                            var f = rawFeats[j];
                            var fChecked = defChecked && (f.default !== false);
                            var subRaw = f.features || [];
                            var subList = [];
                            for (var k = 0; k < subRaw.length; k++) {
                                var sf = subRaw[k];
                                subList.push({
                                    id: sf.id,
                                    title: sf.title || sf.id,
                                    desc: sf.desc || "",
                                    needs: sf.needs || [],
                                    checked: fChecked && (sf.default !== false)
                                });
                            }
                            feats.push({
                                id: f.id,
                                title: f.title || f.id,
                                desc: f.desc || "",
                                needs: f.needs || [],
                                checked: fChecked,
                                partial: false,
                                expanded: false,
                                features: subList
                            });
                        }
                        var targetModel = isInstalled ? installedItems : items;
                        targetModel.append({
                            id: s.id, title: s.title, desc: s.desc, kind: s.kind,
                            terminal: s.terminal, missing: s.missing.join(", "),
                            checked: defChecked, partial: false, expanded: false,
                            featuresJson: JSON.stringify(feats),
                            runState: "idle", detail: ""
                        });
                    }
                    root.recount();
                    root.loading = false;
                    if (items.count === 0 && !(root.setupMode && installedItems.count > 0)) {
                        if (!root.setupMode) Qt.quit();
                        root.nothingToDo = true;
                        root.page = 3;
                    } else if (items.count === 0) {
                        // setup modu: eksik olmasa da kurulu olanları göster (liste açık başlar)
                        root.showInstalled = true;
                        root.page = 1;
                    } else if (root.page === 0 || root.page === 3) {
                        root.page = 1;
                    }
                } catch (err) {
                    root.loadError = "Durum okunamadı";
                    root.loading = false;
                }
            }
        }
        onExited: code => { if (code !== 0 && !root.loadError) { root.loadError = "dotsync çalışmadı (kod " + code + ")"; root.loading = false; } }
    }

    // Parola: sudo ile doğrulanır (yalnızca stdin'den; ekrana/arg'a yazılmaz)
    Process {
        id: pwCheckProc
        command: [root.sudoBin, "-S", "-k", "-p", "", "-v"]
        stdinEnabled: true
        onExited: code => {
            root.dlgBusy = false;
            if (code === 0) {
                pwInput.text = "";
                root.dlgStep = 0;
                root.startApply(true);
            } else {
                root.pendingPw = "";
                root.dlgError = "Parola yanlış. Tekrar dene.";
            }
        }
    }
    Timer {
        id: pwWriteTimer
        property var target: null
        interval: 200
        onTriggered: {
            if (target && root.pendingPw !== "") target.write(root.pendingPw + "\n");
            if (target === applyProc) root.pendingPw = "";
        }
    }

    Process {
        id: applyProc
        stdinEnabled: true
        stdout: SplitParser { onRead: line => root.onEvent(line) }
        onExited: code => { if (root.page === 2) root.page = 3; }
    }

    function bootStep(sid, state) {
        for (var i = 0; i < bootSteps.count; i++)
            if (bootSteps.get(i).sid === sid) bootSteps.setProperty(i, "st", state);
    }

    Process {
        id: bootstrapProc
        command: ["bash", root.bootstrapPath]
        environment: ({ "DOTSYNC_PROGRESS": "1" })
        stdout: SplitParser {
            onRead: line => {
                var m = line.match(/^STEP (başla|bitti) (\w+)$/);
                if (m) root.bootStep(m[2], m[1] === "başla" ? "run" : "ok");
            }
        }
        onExited: code => {
            if (code === 0) afterBootstrap.start();
            else root.bootFailed = true;
        }
    }
    Timer { id: afterBootstrap; interval: 700; onTriggered: root.load() }

    Process { id: resetProc; command: ["python3", root.bin, "reset"]; onExited: root.load() }

    Component.onCompleted: { if (bootstrapMode) bootstrapProc.running = true; else load(); }

    FloatingWindow {
        id: win
        title: "Dots Sync"
        color: "transparent"
        implicitWidth: 760
        implicitHeight: 540
        minimumSize: Qt.size(760, 540)
        maximumSize: Qt.size(760, 540)

        Rectangle {
            id: frame
            anchors.fill: parent
            radius: 18
            color: root.cBg
            border.color: root.cOutlineSoft
            border.width: 1
            clip: true
            focus: true
            Keys.onEscapePressed: Qt.quit()

            // ---- üst şerit: ad, adım noktaları, kapat
            Item {
                id: header
                height: 60
                anchors { left: parent.left; right: parent.right; top: parent.top }

                Rectangle { x: 24; y: 24; width: 12; height: 12; radius: 6; color: root.cAccent }
                Text { x: 46; y: 19; text: "Dots Sync"; color: root.cFg; font.pixelSize: 15; font.weight: Font.DemiBold }

                Row {
                    anchors.centerIn: parent
                    spacing: 8
                    Repeater {
                        model: root.bootstrapMode ? 4 : 3
                        Rectangle {
                            width: (index + root.firstPage) === root.page ? 22 : 8
                            height: 8
                            radius: 4
                            color: (index + root.firstPage) <= root.page ? root.cAccent : root.cOutline
                            Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                            Behavior on color { ColorAnimation { duration: 220 } }
                        }
                    }
                }

                MouseArea {
                    id: closeArea
                    x: parent.width - 52; y: 14; width: 32; height: 32
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: Qt.quit()
                    Rectangle { anchors.fill: parent; radius: 16; color: root.cSurface2; opacity: closeArea.containsMouse ? 1 : 0; Behavior on opacity { NumberAnimation { duration: 120 } } }
                    Text { anchors.centerIn: parent; text: "✕"; color: root.cSub; font.pixelSize: 13 }
                }
            }

            // ---- sayfa şeridi (kayar)
            Item {
                id: viewport
                anchors { left: parent.left; right: parent.right; top: header.bottom; bottom: parent.bottom }
                clip: true

                Row {
                    id: strip
                    x: -root.page * viewport.width
                    height: viewport.height
                    Behavior on x { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

                    // ============ Sayfa 0: installer kurulumu (yalnızca ilk kurulumda görünür)
                    Item {
                        width: viewport.width; height: viewport.height
                        ColumnLayout {
                            anchors { fill: parent; leftMargin: 32; rightMargin: 32; topMargin: 4; bottomMargin: 24 }
                            spacing: 14
                            Text { text: "Kuruluma hoş geldin"; color: root.cFg; font.pixelSize: 24; font.weight: Font.DemiBold }
                            Text {
                                Layout.fillWidth: true; wrapMode: Text.WordWrap
                                text: root.bootFailed
                                    ? "Installer kurulamadı. Terminalde ~/kaan-dots/bootstrap.sh çalıştırıp hatayı görebilirsin."
                                    : "Önce installer'ın kendisi kuruluyor. Sonraki açılışlarda bu adım olmaz; yalnızca sistemde eksik olanlar sorulur."
                                color: root.bootFailed ? root.cErr : root.cSub; font.pixelSize: 13
                            }
                            Repeater {
                                model: bootSteps
                                delegate: RowLayout {
                                    Layout.fillWidth: true; Layout.topMargin: 6; spacing: 14
                                    Rectangle {
                                        width: 22; height: 22; radius: 11
                                        color: model.st === "ok" ? root.cOk : "transparent"
                                        border.color: model.st === "run" ? root.cAccent : root.cOutline
                                        border.width: model.st === "ok" ? 0 : 2
                                        Text { anchors.centerIn: parent; visible: model.st === "ok"; text: "✓"; color: root.cBg; font.pixelSize: 13; font.weight: Font.Bold }
                                        Rectangle {
                                            visible: model.st === "run"
                                            anchors.centerIn: parent; width: 8; height: 8; radius: 4; color: root.cAccent
                                            SequentialAnimation on opacity {
                                                running: model.st === "run"; loops: Animation.Infinite
                                                NumberAnimation { to: 0.2; duration: 600; easing.type: Easing.InOutSine }
                                                NumberAnimation { to: 1; duration: 600; easing.type: Easing.InOutSine }
                                            }
                                        }
                                    }
                                    Text { text: model.label; color: model.st === "wait" ? root.cDim : root.cFg; font.pixelSize: 14 }
                                }
                            }
                            Item { Layout.fillHeight: true }
                            Rectangle {
                                visible: root.bootFailed
                                Layout.alignment: Qt.AlignRight
                                implicitWidth: failTxt.implicitWidth + 44; implicitHeight: 42; radius: 21
                                color: root.cAccent
                                Text { id: failTxt; anchors.centerIn: parent; text: "Kapat"; color: root.cBg; font.pixelSize: 14; font.weight: Font.DemiBold }
                                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: Qt.quit() }
                            }
                        }
                    }

                    // ============ Sayfa 1: eksikler
                    Item {
                        width: viewport.width; height: viewport.height

                        ColumnLayout {
                            anchors { fill: parent; leftMargin: 32; rightMargin: 32; topMargin: 4; bottomMargin: 24 }
                            spacing: 14

                            Text {
                                text: root.loading ? "Denetleniyor…" : (root.setupMode ? "Neleri kuralım?" : "Yerelde eksik olanlar")
                                color: root.cFg; font.pixelSize: 24; font.weight: Font.DemiBold
                            }
                            Text {
                                Layout.fillWidth: true
                                wrapMode: Text.WordWrap
                                text: root.loadError ? root.loadError
                                    : (!root.loading && items.count === 0) ? "Bu bilgisayarda eksik bir şey yok. Kurulu olanlar aşağıda listelendi."
                                    : "GitHub'daki ayarlarında olup bu bilgisayarda bulunmayanlar. İndirmek istediklerini işaretle; işaretlemediklerin için bir daha sorulmaz."
                                color: root.loadError ? root.cErr : root.cSub
                                font.pixelSize: 13
                            }

                            ListView {
                                id: list
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 10
                                clip: true
                                model: items
                                boundsBehavior: Flickable.StopAtBounds
                                // Kart açılıp kapanınca içerik yüksekliği değişir; ListView konumu başa atmasın.
                                property real keepY: -1
                                onContentHeightChanged: if (keepY >= 0) contentY = keepY
                                function keepScroll(change) {
                                    keepY = contentY;
                                    change();
                                    Qt.callLater(function() { if (list.keepY >= 0) list.contentY = list.keepY; list.keepY = -1; });
                                }
                                delegate: Rectangle {
                                    id: card
                                    readonly property int cardIdx: index
                                    readonly property var feats: JSON.parse(model.featuresJson || "[]")
                                    readonly property int selFeatCount: {
                                        var c = 0;
                                        for (var j = 0; j < feats.length; j++) if (feats[j].checked) c++;
                                        return c;
                                    }
                                    width: list.width
                                    height: cardCol.implicitHeight + 32
                                    radius: 18
                                    color: rowArea.containsMouse ? Qt.lighter(root.cSurface, 1.12) : root.cSurface
                                    border.color: model.checked ? Qt.rgba(0.714, 0.616, 0.973, 0.55) : Qt.rgba(1, 1, 1, 0.09)
                                    border.width: 1
                                    Behavior on color { ColorAnimation { duration: 120 } }

                                    MouseArea {
                                        id: rowArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: root.toggleAllFeatures(index, !(model.checked && !model.partial))
                                    }

                                    ColumnLayout {
                                        id: cardCol
                                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 16 }
                                        spacing: 14

                                        // ---- başlık: rozet | ad + açıklama | seçim
                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 14

                                            Rectangle {
                                                Layout.alignment: Qt.AlignTop
                                                implicitWidth: 46; implicitHeight: 46; radius: 14
                                                color: root.badgeColor(model.id)
                                                Text {
                                                    anchors.centerIn: parent
                                                    text: root.initialOf(model.title)
                                                    color: root.badgeFg(model.id)
                                                    font.pixelSize: 20; font.weight: Font.Bold
                                                }
                                            }

                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 3
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    Text {
                                                        text: model.title
                                                        color: root.cFg; font.pixelSize: 16; font.weight: Font.DemiBold
                                                        elide: Text.ElideRight
                                                        Layout.maximumWidth: 360
                                                    }
                                                    Rectangle {
                                                        visible: model.terminal
                                                        radius: 8; color: root.cSurface2
                                                        implicitWidth: termLabel.implicitWidth + 14; implicitHeight: 20
                                                        Text { id: termLabel; anchors.centerIn: parent; text: "terminalde"; color: root.cSub; font.pixelSize: 11 }
                                                    }
                                                    Item { Layout.fillWidth: true }
                                                }
                                                Text {
                                                    Layout.fillWidth: true
                                                    wrapMode: Text.WordWrap
                                                    maximumLineCount: 3
                                                    elide: Text.ElideRight
                                                    text: model.desc
                                                    color: root.cSub; font.pixelSize: 12
                                                }
                                                Text {
                                                    visible: model.missing !== ""
                                                    Layout.fillWidth: true
                                                    elide: Text.ElideRight
                                                    text: "Eksik: " + model.missing
                                                    color: root.cDim; font.pixelSize: 11
                                                }
                                            }

                                            ColumnLayout {
                                                Layout.alignment: Qt.AlignTop
                                                spacing: 8
                                                Rectangle {
                                                    Layout.alignment: Qt.AlignRight
                                                    width: 26; height: 26; radius: 9
                                                    color: model.checked ? root.cAccent : "transparent"
                                                    border.color: model.checked ? root.cAccent : root.cDim
                                                    border.width: 2
                                                    Behavior on color { ColorAnimation { duration: 120 } }
                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: model.partial ? "−" : "✓"
                                                        visible: model.checked
                                                        color: root.cBg; font.pixelSize: 15; font.weight: Font.Bold
                                                    }
                                                }
                                                Rectangle {
                                                    visible: card.feats.length > 0
                                                    Layout.alignment: Qt.AlignRight
                                                    radius: 10
                                                    color: expArea.containsMouse ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.07)
                                                    implicitWidth: expRow.implicitWidth + 18; implicitHeight: 26
                                                    RowLayout {
                                                        id: expRow
                                                        anchors.centerIn: parent
                                                        spacing: 5
                                                        Text { text: card.selFeatCount + "/" + card.feats.length + " seçenek"; color: root.cSub; font.pixelSize: 11 }
                                                        Text { text: model.expanded ? "▾" : "▸"; color: root.cFg; font.pixelSize: 12 }
                                                    }
                                                    MouseArea {
                                                        id: expArea
                                                        anchors.fill: parent
                                                        hoverEnabled: true
                                                        cursorShape: Qt.PointingHandCursor
                                                        onClicked: mouse => {
                                                            mouse.accepted = true;
                                                            list.keepScroll(function() { items.setProperty(card.cardIdx, "expanded", !model.expanded); });
                                                        }
                                                    }
                                                }
                                            }
                                        }

                                        // ---- seçenekler: 2 sütunlu katalog kutucukları
                                        GridLayout {
                                            visible: model.expanded && card.feats.length > 0
                                            Layout.fillWidth: true
                                            columns: 2
                                            columnSpacing: 10
                                            rowSpacing: 10

                                            Repeater {
                                                model: card.feats
                                                delegate: Rectangle {
                                                    id: featWrap
                                                    required property var modelData
                                                    required property int index
                                                    readonly property int featIdx: index
                                                    readonly property var subFeats: modelData.features || []
                                                    readonly property bool isGroup: subFeats.length > 0
                                                    readonly property bool open: isGroup && modelData.expanded === true
                                                    readonly property int selSubCount: {
                                                        var c = 0;
                                                        for (var k = 0; k < subFeats.length; k++) if (subFeats[k].checked) c++;
                                                        return c;
                                                    }
                                                    readonly property bool hasNeeds: modelData.needs && modelData.needs.length > 0
                                                    Layout.fillWidth: true
                                                    Layout.preferredWidth: 1
                                                    Layout.columnSpan: open ? 2 : 1
                                                    Layout.alignment: Qt.AlignTop
                                                    implicitHeight: featCol.implicitHeight + 24
                                                    radius: 14
                                                    color: subArea.containsMouse ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(1, 1, 1, 0.04)
                                                    border.color: modelData.checked ? Qt.rgba(0.714, 0.616, 0.973, 0.5) : Qt.rgba(1, 1, 1, 0.08)
                                                    border.width: 1
                                                    Behavior on color { ColorAnimation { duration: 120 } }

                                                    MouseArea {
                                                        id: subArea
                                                        anchors.fill: parent
                                                        hoverEnabled: true
                                                        cursorShape: Qt.PointingHandCursor
                                                        onClicked: mouse => {
                                                            mouse.accepted = true;
                                                            root.toggleSubFeature(card.cardIdx, featWrap.featIdx);
                                                        }
                                                    }

                                                    ColumnLayout {
                                                        id: featCol
                                                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
                                                        spacing: 8

                                                        RowLayout {
                                                            Layout.fillWidth: true
                                                            spacing: 10
                                                            Rectangle {
                                                                Layout.alignment: Qt.AlignTop
                                                                implicitWidth: 32; implicitHeight: 32; radius: 10
                                                                color: root.badgeColor(featWrap.modelData.id)
                                                                Text {
                                                                    anchors.centerIn: parent
                                                                    text: root.initialOf(featWrap.modelData.title)
                                                                    color: root.badgeFg(featWrap.modelData.id)
                                                                    font.pixelSize: 14; font.weight: Font.Bold
                                                                }
                                                            }
                                                            ColumnLayout {
                                                                Layout.fillWidth: true
                                                                spacing: 2
                                                                Text {
                                                                    Layout.fillWidth: true
                                                                    text: featWrap.modelData.title
                                                                    color: root.cFg; font.pixelSize: 13; font.weight: Font.DemiBold
                                                                    wrapMode: Text.WordWrap; maximumLineCount: 2
                                                                    elide: Text.ElideRight
                                                                }
                                                                Text {
                                                                    visible: featWrap.modelData.desc !== ""
                                                                    Layout.fillWidth: true
                                                                    text: featWrap.modelData.desc
                                                                    color: root.cDim; font.pixelSize: 11
                                                                    wrapMode: Text.WordWrap
                                                                    maximumLineCount: featWrap.open ? 5 : 3
                                                                    elide: Text.ElideRight
                                                                }
                                                            }
                                                            Rectangle {
                                                                Layout.alignment: Qt.AlignTop
                                                                width: 22; height: 22; radius: 7
                                                                color: featWrap.modelData.checked ? root.cAccent : "transparent"
                                                                border.color: featWrap.modelData.checked ? root.cAccent : root.cDim
                                                                border.width: 2
                                                                Behavior on color { ColorAnimation { duration: 120 } }
                                                                Text {
                                                                    anchors.centerIn: parent
                                                                    text: featWrap.modelData.partial ? "−" : "✓"
                                                                    visible: featWrap.modelData.checked
                                                                    color: root.cBg; font.pixelSize: 13; font.weight: Font.Bold
                                                                }
                                                            }
                                                        }

                                                        RowLayout {
                                                            visible: featWrap.hasNeeds || featWrap.isGroup
                                                            Layout.fillWidth: true
                                                            spacing: 8
                                                            Rectangle {
                                                                visible: featWrap.hasNeeds
                                                                radius: 8
                                                                color: Qt.rgba(0.96, 0.72, 0.35, 0.16)
                                                                implicitWidth: needLbl.implicitWidth + 16; implicitHeight: 22
                                                                Layout.maximumWidth: 260
                                                                Text {
                                                                    id: needLbl
                                                                    anchors.fill: parent; anchors.leftMargin: 8; anchors.rightMargin: 8
                                                                    verticalAlignment: Text.AlignVCenter
                                                                    text: featWrap.hasNeeds ? "İndirilecek: " + featWrap.modelData.needs.join(", ") : ""
                                                                    color: "#f5b85a"; font.pixelSize: 10; elide: Text.ElideRight
                                                                }
                                                            }
                                                            Item { Layout.fillWidth: true }
                                                            Rectangle {
                                                                visible: featWrap.isGroup
                                                                radius: 9
                                                                color: subExpArea.containsMouse ? Qt.rgba(1, 1, 1, 0.14) : Qt.rgba(1, 1, 1, 0.08)
                                                                implicitWidth: subExpRow.implicitWidth + 16; implicitHeight: 24
                                                                RowLayout {
                                                                    id: subExpRow
                                                                    anchors.centerIn: parent
                                                                    spacing: 4
                                                                    Text { text: featWrap.selSubCount + "/" + featWrap.subFeats.length + " seçenek"; color: root.cSub; font.pixelSize: 10 }
                                                                    Text { text: featWrap.modelData.expanded ? "▾" : "▸"; color: root.cFg; font.pixelSize: 11 }
                                                                }
                                                                MouseArea {
                                                                    id: subExpArea
                                                                    anchors.fill: parent
                                                                    hoverEnabled: true
                                                                    cursorShape: Qt.PointingHandCursor
                                                                    onClicked: mouse => {
                                                                        mouse.accepted = true;
                                                                        root.toggleFeatureExpand(card.cardIdx, featWrap.featIdx);
                                                                    }
                                                                }
                                                            }
                                                        }

                                                        // grubun alt seçenekleri
                                                        GridLayout {
                                                            visible: featWrap.open
                                                            Layout.fillWidth: true
                                                            columns: 2
                                                            columnSpacing: 8
                                                            rowSpacing: 8
                                                            Repeater {
                                                                model: featWrap.subFeats
                                                                delegate: Rectangle {
                                                                    id: nest
                                                                    required property var modelData
                                                                    required property int index
                                                                    readonly property bool hasNeeds: modelData.needs && modelData.needs.length > 0
                                                                    Layout.fillWidth: true
                                                                    Layout.preferredWidth: 1
                                                                    Layout.alignment: Qt.AlignTop
                                                                    implicitHeight: nestCol.implicitHeight + 20
                                                                    radius: 11
                                                                    color: nestArea.containsMouse ? Qt.rgba(1, 1, 1, 0.07) : Qt.rgba(0, 0, 0, 0.2)
                                                                    border.color: modelData.checked ? Qt.rgba(0.714, 0.616, 0.973, 0.45) : Qt.rgba(1, 1, 1, 0.06)
                                                                    border.width: 1

                                                                    MouseArea {
                                                                        id: nestArea
                                                                        anchors.fill: parent
                                                                        hoverEnabled: true
                                                                        cursorShape: Qt.PointingHandCursor
                                                                        onClicked: mouse => {
                                                                            mouse.accepted = true;
                                                                            root.toggleNestedFeature(card.cardIdx, featWrap.featIdx, nest.index);
                                                                        }
                                                                    }
                                                                    ColumnLayout {
                                                                        id: nestCol
                                                                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 10 }
                                                                        spacing: 4
                                                                        RowLayout {
                                                                            Layout.fillWidth: true
                                                                            spacing: 8
                                                                            Text { Layout.fillWidth: true; text: nest.modelData.title; color: root.cFg; font.pixelSize: 12; font.weight: Font.Medium; elide: Text.ElideRight }
                                                                            Rectangle {
                                                                                width: 18; height: 18; radius: 6
                                                                                color: nest.modelData.checked ? root.cAccent : "transparent"
                                                                                border.color: nest.modelData.checked ? root.cAccent : root.cDim
                                                                                border.width: 2
                                                                                Text { anchors.centerIn: parent; text: "✓"; visible: nest.modelData.checked; color: root.cBg; font.pixelSize: 11; font.weight: Font.Bold }
                                                                            }
                                                                        }
                                                                        Text {
                                                                            visible: nest.modelData.desc !== ""
                                                                            Layout.fillWidth: true
                                                                            text: nest.modelData.desc; color: root.cDim; font.pixelSize: 10
                                                                            wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight
                                                                        }
                                                                        Text {
                                                                            visible: nest.hasNeeds
                                                                            Layout.fillWidth: true
                                                                            text: nest.hasNeeds ? "İndirilecek: " + nest.modelData.needs.join(", ") : ""
                                                                            color: "#f5b85a"; font.pixelSize: 10; wrapMode: Text.WordWrap
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                                footer: ColumnLayout {
                                    width: list.width
                                    spacing: 10
                                    visible: installedItems.count > 0

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.topMargin: 10
                                        implicitHeight: 38
                                        radius: 12
                                        color: instHdrArea.containsMouse ? root.cSurface2 : root.cSurface
                                        border.color: Qt.rgba(0.651, 0.890, 0.631, 0.28)
                                        border.width: 1

                                        MouseArea {
                                            id: instHdrArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: list.keepScroll(function() { root.showInstalled = !root.showInstalled; })
                                        }

                                        RowLayout {
                                            anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 14 }
                                            spacing: 8
                                            Text { text: "✓"; color: root.cOk; font.pixelSize: 13; font.weight: Font.Bold }
                                            Text {
                                                text: "Zaten yüklü (" + installedItems.count + ")"
                                                color: root.cFg; font.pixelSize: 13; font.weight: Font.Medium
                                            }
                                            Item { Layout.fillWidth: true }
                                            Text {
                                                text: root.showInstalled ? "▾" : "▸"
                                                color: root.cSub; font.pixelSize: 14
                                            }
                                        }
                                    }

                                    Repeater {
                                        model: root.showInstalled ? installedItems : null
                                        delegate: Rectangle {
                                            id: instCard
                                            readonly property int instIdx: index
                                            readonly property var feats: JSON.parse(model.featuresJson || "[]")
                                            Layout.fillWidth: true
                                            implicitHeight: instCol.implicitHeight + 24
                                            radius: 14
                                            color: root.cSurface
                                            opacity: 0.85
                                            border.color: Qt.rgba(0.651, 0.890, 0.631, 0.25)
                                            border.width: 1

                                            ColumnLayout {
                                                id: instCol
                                                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 16 }
                                                spacing: 4

                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 10
                                                    Rectangle {
                                                        implicitWidth: 34; implicitHeight: 34; radius: 11
                                                        color: root.badgeColor(model.id)
                                                        Text { anchors.centerIn: parent; text: root.initialOf(model.title); color: root.badgeFg(model.id); font.pixelSize: 16; font.weight: Font.Bold }
                                                    }
                                                    Rectangle {
                                                        radius: 6; color: Qt.rgba(0.651, 0.890, 0.631, 0.18)
                                                        implicitWidth: okLbl.implicitWidth + 12; implicitHeight: 20
                                                        Text { id: okLbl; anchors.centerIn: parent; text: "✓ Yüklü"; color: root.cOk; font.pixelSize: 11; font.weight: Font.Medium }
                                                    }
                                                    Text { text: model.title; color: root.cFg; font.pixelSize: 15; font.weight: Font.DemiBold }
                                                    Item { Layout.fillWidth: true }
                                                    Rectangle {
                                                        visible: instCard.feats.length > 0
                                                        radius: 8
                                                        color: instExpArea.containsMouse ? root.cSurface2 : root.cBg
                                                        border.color: Qt.rgba(0.651, 0.890, 0.631, 0.3)
                                                        border.width: 1
                                                        implicitWidth: instExpRow.implicitWidth + 16
                                                        implicitHeight: 24
                                                        RowLayout {
                                                            id: instExpRow
                                                            anchors.centerIn: parent
                                                            spacing: 4
                                                            Text { text: instCard.feats.length + " parça"; color: root.cSub; font.pixelSize: 11 }
                                                            Text { text: model.expanded ? "▾" : "▸"; color: root.cFg; font.pixelSize: 12 }
                                                        }
                                                        MouseArea {
                                                            id: instExpArea
                                                            anchors.fill: parent
                                                            hoverEnabled: true
                                                            cursorShape: Qt.PointingHandCursor
                                                            onClicked: list.keepScroll(function() { installedItems.setProperty(instCard.instIdx, "expanded", !model.expanded); })
                                                        }
                                                    }
                                                }

                                                Text { Layout.fillWidth: true; wrapMode: Text.WordWrap; text: model.desc; color: root.cSub; font.pixelSize: 12 }

                                                GridLayout {
                                                    visible: model.expanded && instCard.feats.length > 0
                                                    Layout.fillWidth: true
                                                    Layout.topMargin: 12
                                                    columns: 2
                                                    columnSpacing: 10
                                                    rowSpacing: 10

                                                    Repeater {
                                                        model: instCard.feats
                                                        delegate: Rectangle {
                                                            id: tile
                                                            required property var modelData
                                                            required property int index
                                                            readonly property var subFeats: modelData.features || []
                                                            readonly property bool isGroup: subFeats.length > 0
                                                            readonly property bool open: isGroup && modelData.expanded === true
                                                            readonly property bool incomplete: !isGroup && modelData.needs && modelData.needs.length > 0
                                                            Layout.fillWidth: true
                                                            Layout.preferredWidth: 1
                                                            Layout.columnSpan: open ? 2 : 1
                                                            Layout.alignment: Qt.AlignTop
                                                            implicitHeight: tileCol.implicitHeight + 26
                                                            radius: 16
                                                            color: tileArea.containsMouse && isGroup ? Qt.rgba(1, 1, 1, 0.07) : Qt.rgba(1, 1, 1, 0.035)
                                                            border.color: open ? Qt.rgba(0.714, 0.616, 0.973, 0.45) : Qt.rgba(1, 1, 1, 0.08)
                                                            border.width: 1
                                                            Behavior on color { ColorAnimation { duration: 120 } }

                                                            MouseArea {
                                                                id: tileArea
                                                                anchors.fill: parent
                                                                hoverEnabled: true
                                                                enabled: tile.isGroup
                                                                cursorShape: Qt.PointingHandCursor
                                                                onClicked: {
                                                                    var f = JSON.parse(installedItems.get(instCard.instIdx).featuresJson || "[]");
                                                                    f[tile.index].expanded = !f[tile.index].expanded;
                                                                    list.keepScroll(function() { installedItems.setProperty(instCard.instIdx, "featuresJson", JSON.stringify(f)); });
                                                                }
                                                            }

                                                            ColumnLayout {
                                                                id: tileCol
                                                                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 13 }
                                                                spacing: 10

                                                                RowLayout {
                                                                    Layout.fillWidth: true
                                                                    spacing: 11
                                                                    Rectangle {
                                                                        implicitWidth: 40; implicitHeight: 40; radius: 12
                                                                        color: root.badgeColor(tile.modelData.id)
                                                                        Text {
                                                                            anchors.centerIn: parent
                                                                            text: root.initialOf(tile.modelData.title)
                                                                            color: root.badgeFg(tile.modelData.id)
                                                                            font.pixelSize: 18; font.weight: Font.Bold
                                                                        }
                                                                    }
                                                                    ColumnLayout {
                                                                        Layout.fillWidth: true
                                                                        spacing: 2
                                                                        Text {
                                                                            Layout.fillWidth: true
                                                                            text: tile.modelData.title
                                                                            color: root.cFg; font.pixelSize: 13; font.weight: Font.DemiBold
                                                                            elide: Text.ElideRight
                                                                        }
                                                                        Text {
                                                                            visible: tile.modelData.desc !== ""
                                                                            Layout.fillWidth: true
                                                                            text: tile.modelData.desc
                                                                            color: root.cDim; font.pixelSize: 11
                                                                            wrapMode: Text.WordWrap
                                                                            maximumLineCount: tile.open ? 6 : 2
                                                                            elide: Text.ElideRight
                                                                        }
                                                                    }
                                                                }

                                                                RowLayout {
                                                                    Layout.fillWidth: true
                                                                    spacing: 8
                                                                    Rectangle {
                                                                        visible: !tile.isGroup
                                                                        radius: 8
                                                                        color: tile.incomplete ? Qt.rgba(0.96, 0.72, 0.35, 0.16) : Qt.rgba(0.651, 0.890, 0.631, 0.16)
                                                                        implicitWidth: stLbl.implicitWidth + 16; implicitHeight: 22
                                                                        Text {
                                                                            id: stLbl; anchors.centerIn: parent
                                                                            text: tile.incomplete ? "İndirilmedi" : "✓ Yüklü"
                                                                            color: tile.incomplete ? "#f5b85a" : root.cOk
                                                                            font.pixelSize: 11; font.weight: Font.Medium
                                                                        }
                                                                    }
                                                                    Text {
                                                                        visible: tile.incomplete
                                                                        Layout.fillWidth: true
                                                                        text: tile.incomplete ? tile.modelData.needs.join(", ") : ""
                                                                        color: root.cDim; font.pixelSize: 10; elide: Text.ElideRight
                                                                    }
                                                                    Item { Layout.fillWidth: true; visible: !tile.incomplete }
                                                                    Rectangle {
                                                                        visible: tile.isGroup
                                                                        radius: 8
                                                                        color: Qt.rgba(1, 1, 1, 0.07)
                                                                        implicitWidth: grpLbl.implicitWidth + 18; implicitHeight: 22
                                                                        Text {
                                                                            id: grpLbl; anchors.centerIn: parent
                                                                            text: tile.subFeats.length + " parça  " + (tile.open ? "▾" : "▸")
                                                                            color: root.cSub; font.pixelSize: 11
                                                                        }
                                                                    }
                                                                }

                                                                // Grubun alt özellikleri (açıkken): ikinci katman kartlar
                                                                GridLayout {
                                                                    visible: tile.open
                                                                    Layout.fillWidth: true
                                                                    columns: 2
                                                                    columnSpacing: 8
                                                                    rowSpacing: 8
                                                                    Repeater {
                                                                        model: tile.subFeats
                                                                        delegate: Rectangle {
                                                                            id: sub
                                                                            required property var modelData
                                                                            readonly property bool incomplete: modelData.needs && modelData.needs.length > 0
                                                                            Layout.fillWidth: true
                                                                            Layout.preferredWidth: 1
                                                                            Layout.alignment: Qt.AlignTop
                                                                            implicitHeight: subCol.implicitHeight + 20
                                                                            radius: 12
                                                                            color: Qt.rgba(0, 0, 0, 0.22)
                                                                            border.color: Qt.rgba(1, 1, 1, 0.06); border.width: 1
                                                                            ColumnLayout {
                                                                                id: subCol
                                                                                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 10 }
                                                                                spacing: 4
                                                                                RowLayout {
                                                                                    Layout.fillWidth: true
                                                                                    spacing: 7
                                                                                    Rectangle { implicitWidth: 8; implicitHeight: 8; radius: 4; color: sub.incomplete ? "#f5b85a" : root.cOk }
                                                                                    Text { Layout.fillWidth: true; text: sub.modelData.title; color: root.cFg; font.pixelSize: 12; font.weight: Font.Medium; elide: Text.ElideRight }
                                                                                }
                                                                                Text {
                                                                                    visible: sub.modelData.desc !== ""
                                                                                    Layout.fillWidth: true; Layout.leftMargin: 15
                                                                                    text: sub.modelData.desc; color: root.cDim; font.pixelSize: 10
                                                                                    wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight
                                                                                }
                                                                                Text {
                                                                                    visible: sub.incomplete
                                                                                    Layout.fillWidth: true; Layout.leftMargin: 15
                                                                                    text: sub.incomplete ? "İndirilmedi: " + sub.modelData.needs.join(", ") : ""
                                                                                    color: "#f5b85a"; font.pixelSize: 10; wrapMode: Text.WordWrap
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12
                                Text {
                                    text: "Reddedilenleri sıfırla"
                                    color: resetArea.containsMouse ? root.cFg : root.cDim
                                    font.pixelSize: 12
                                    MouseArea { id: resetArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: resetProc.running = true }
                                }
                                Item { Layout.fillWidth: true }
                                Rectangle {
                                    id: laterBtn
                                    implicitWidth: laterTxt.implicitWidth + 40; implicitHeight: 42; radius: 21
                                    color: laterArea.containsMouse ? root.cSurface2 : "transparent"
                                    border.color: root.cOutline; border.width: 1
                                    Text { id: laterTxt; anchors.centerIn: parent; text: items.count === 0 ? "Kapat" : "Şimdi değil"; color: root.cFg; font.pixelSize: 14 }
                                    MouseArea { id: laterArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: Qt.quit() }
                                }
                                Rectangle {
                                    implicitWidth: goTxt.implicitWidth + 44; implicitHeight: 42; radius: 21
                                    visible: items.count > 0
                                    enabled: !root.loading && items.count > 0
                                    opacity: enabled ? 1 : 0.4
                                    color: goArea.pressed ? Qt.darker(root.cAccent, 1.15) : root.cAccent
                                    Text {
                                        id: goTxt; anchors.centerIn: parent
                                        text: root.selectedCount > 0 ? "Seçilenleri indir (" + root.selectedCount + ")" : "Hiçbirini indirme"
                                        color: root.cBg; font.pixelSize: 14; font.weight: Font.DemiBold
                                    }
                                    MouseArea { id: goArea; anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.requestApply() }
                                }
                            }
                        }
                    }

                    // ============ Sayfa 2: ilerleme
                    Item {
                        width: viewport.width; height: viewport.height
                        ColumnLayout {
                            anchors { fill: parent; leftMargin: 32; rightMargin: 32; topMargin: 4; bottomMargin: 24 }
                            spacing: 14
                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: "Kuruluyor"; color: root.cFg; font.pixelSize: 24; font.weight: Font.DemiBold; Layout.fillWidth: true }
                                Text {
                                    readonly property int pct: root.applyTotal > 0 ? Math.round(root.applyDone * 100 / root.applyTotal) : 0
                                    text: root.applyDone + " / " + root.applyTotal + " (" + pct + "%)"
                                    color: root.cAccent; font.pixelSize: 14; font.weight: Font.DemiBold
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true; implicitHeight: 6; radius: 3; color: root.cSurface2; clip: true
                                Rectangle {
                                    anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                                    width: root.applyTotal > 0 ? parent.width * (root.applyDone / root.applyTotal) : 0
                                    radius: 3; color: root.cAccent
                                    Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                                }
                                // Çalışırken kayan şerit: uzun süren tek bir paket için de hareket gösterir
                                Rectangle {
                                    id: shimmer
                                    visible: root.applyDone < root.applyTotal
                                    y: 0; height: parent.height; width: parent.width * 0.25; radius: 3
                                    color: Qt.rgba(1, 1, 1, 0.35)
                                    SequentialAnimation on x {
                                        running: shimmer.visible; loops: Animation.Infinite
                                        NumberAnimation { from: -shimmer.width; to: shimmer.parent.width; duration: 1400; easing.type: Easing.InOutQuad }
                                    }
                                }
                            }
                            Text {
                                Layout.fillWidth: true; wrapMode: Text.WordWrap
                                text: root.pwMode ? "Paketler arka planda indiriliyor; bu birkaç dakika sürebilir. Pencereyi kapatma."
                                    : "Terminal gerektirenler ayrı bir pencerede açılır; parolayı orada girersin."
                                color: root.cSub; font.pixelSize: 13
                            }
                            ListView {
                                Layout.fillWidth: true; Layout.fillHeight: true
                                spacing: 8; clip: true
                                model: items
                                delegate: Item {
                                    width: ListView.view.width
                                    height: model.runState === "skip" ? 0 : 44
                                    visible: height > 0
                                    Rectangle {
                                        id: dot
                                        x: 6; anchors.verticalCenter: parent.verticalCenter
                                        width: 22; height: 22; radius: 11
                                        color: model.runState === "ok" ? root.cOk
                                             : model.runState === "fail" ? root.cErr
                                             : "transparent"
                                        border.color: model.runState === "run" ? root.cAccent : root.cOutline
                                        border.width: model.runState === "ok" || model.runState === "fail" ? 0 : 2
                                        Text {
                                            anchors.centerIn: parent
                                            visible: model.runState === "ok" || model.runState === "fail"
                                            text: model.runState === "ok" ? "✓" : "!"
                                            color: root.cBg; font.pixelSize: 13; font.weight: Font.Bold
                                        }
                                        Rectangle {
                                            visible: model.runState === "run"
                                            anchors.centerIn: parent; width: 8; height: 8; radius: 4; color: root.cAccent
                                            SequentialAnimation on opacity {
                                                running: model.runState === "run"; loops: Animation.Infinite
                                                NumberAnimation { to: 0.2; duration: 600; easing.type: Easing.InOutSine }
                                                NumberAnimation { to: 1; duration: 600; easing.type: Easing.InOutSine }
                                            }
                                        }
                                    }
                                    ColumnLayout {
                                        anchors { left: dot.right; leftMargin: 14; right: parent.right; verticalCenter: parent.verticalCenter }
                                        spacing: 1
                                        Text { text: model.title; color: model.runState === "wait" ? root.cDim : root.cFg; font.pixelSize: 14 }
                                        Text {
                                            visible: model.detail.length > 0
                                            Layout.fillWidth: true; elide: Text.ElideRight
                                            text: model.detail
                                            color: model.runState === "fail" ? root.cErr : root.cDim; font.pixelSize: 11
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // ============ Sayfa 3: sonuç
                    Item {
                        width: viewport.width; height: viewport.height
                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 14
                            width: parent.width - 120
                            Rectangle {
                                Layout.alignment: Qt.AlignHCenter
                                width: 72; height: 72; radius: 36
                                color: root.allOk ? root.cOk : root.cErr
                                Text { anchors.centerIn: parent; text: root.allOk ? "✓" : "!"; color: root.cBg; font.pixelSize: 38; font.weight: Font.Bold }
                            }
                            Text {
                                Layout.alignment: Qt.AlignHCenter
                                text: root.nothingToDo ? "Her şey zaten kurulu" : (root.allOk ? "Hazır" : "Bazı adımlar tamamlanamadı")
                                color: root.cFg; font.pixelSize: 26; font.weight: Font.DemiBold
                            }
                            Text {
                                Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
                                text: root.deferredOnly
                                    ? "Daha sonra için bırakıldı. Bir sonraki açılışta tekrar sorulur."
                                    : root.nothingToDo
                                    ? "Bu bilgisayarda eksik bir şey yok. Sonraki açılışlarda yalnızca yeni bir şey eksik kalırsa sorulur."
                                    : root.allOk
                                    ? "Seçtiklerin kuruldu. İndirmediklerin için bir daha sorulmayacak (Reddedilenleri sıfırla ile geri açabilirsin)."
                                    : "Hata veren adımlar açılışta tekrar önerilir. Ayrıntı için ilerleme sayfasındaki satırlara bak."
                                color: root.cSub; font.pixelSize: 13
                            }
                            Rectangle {
                                Layout.alignment: Qt.AlignHCenter
                                Layout.topMargin: 10
                                implicitWidth: doneTxt.implicitWidth + 56; implicitHeight: 42; radius: 21
                                color: doneArea.pressed ? Qt.darker(root.cAccent, 1.15) : root.cAccent
                                Text { id: doneTxt; anchors.centerIn: parent; text: "Kapat"; color: root.cBg; font.pixelSize: 14; font.weight: Font.DemiBold }
                                MouseArea { id: doneArea; anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: Qt.quit() }
                            }
                        }
                    }
                }
            }

            // ---- yönetici onayı: eksik bağımlılıklar -> parola
            Rectangle {
                id: dlgOverlay
                anchors.fill: parent
                z: 100
                visible: root.dlgStep > 0
                color: Qt.rgba(0, 0, 0, 0.62)
                onVisibleChanged: if (visible && root.dlgStep === 2) pwInput.forceActiveFocus()
                MouseArea { anchors.fill: parent; hoverEnabled: true }   // arkadaki sayfayı tıklamaya kapat

                Rectangle {
                    anchors.centerIn: parent
                    width: 500
                    height: dlgCol.implicitHeight + 48
                    radius: 22
                    color: root.cSurface
                    border.color: root.cOutline
                    border.width: 1

                    ColumnLayout {
                        id: dlgCol
                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
                        spacing: 12

                        Text {
                            text: root.dlgStep === 1 ? "Eksik bağımlılıklar" : "Yönetici parolası"
                            color: root.cFg; font.pixelSize: 20; font.weight: Font.DemiBold
                        }
                        Text {
                            Layout.fillWidth: true; wrapMode: Text.WordWrap
                            text: root.dlgStep === 1
                                ? "Bunlar bu bilgisayarda yok. Şimdi indirilsin mi?"
                                : "Paketleri kurmak için parolanı gir. Kurulum arka planda yapılır."
                            color: root.cSub; font.pixelSize: 13
                        }

                        // 1) eksik listesi
                        Repeater {
                            model: root.dlgStep === 1 ? adminItems : null
                            delegate: ColumnLayout {
                                required property string title
                                required property string missing
                                Layout.fillWidth: true
                                spacing: 2
                                Text { text: "• " + title; color: root.cFg; font.pixelSize: 14; font.weight: Font.Medium }
                                Text {
                                    visible: missing !== ""
                                    Layout.fillWidth: true; Layout.leftMargin: 12; wrapMode: Text.WrapAnywhere
                                    text: missing; color: root.cDim; font.pixelSize: 11
                                }
                            }
                        }

                        // 2) parola alanı
                        Rectangle {
                            visible: root.dlgStep === 2
                            Layout.fillWidth: true; implicitHeight: 44; radius: 12
                            color: root.cSurface2
                            border.color: root.dlgError !== "" ? root.cErr : (pwInput.activeFocus ? root.cAccent : root.cOutline)
                            border.width: 1
                            TextInput {
                                id: pwInput
                                anchors { fill: parent; leftMargin: 14; rightMargin: 14 }
                                verticalAlignment: TextInput.AlignVCenter
                                echoMode: TextInput.Password
                                passwordCharacter: "•"
                                color: root.cFg; font.pixelSize: 15
                                enabled: !root.dlgBusy
                                onAccepted: root.submitPassword(text)
                                onTextChanged: root.dlgError = ""
                            }
                        }
                        Text {
                            visible: root.dlgStep === 2 && root.dlgError !== ""
                            text: root.dlgError; color: root.cErr; font.pixelSize: 12
                        }
                        // parola doğrulanırken kayan çubuk
                        Rectangle {
                            visible: root.dlgStep === 2 && root.dlgBusy
                            Layout.fillWidth: true; implicitHeight: 4; radius: 2; color: root.cSurface2; clip: true
                            Rectangle {
                                id: pwShimmer
                                height: parent.height; width: parent.width * 0.3; radius: 2; color: root.cAccent
                                SequentialAnimation on x {
                                    running: pwShimmer.visible; loops: Animation.Infinite
                                    NumberAnimation { from: -pwShimmer.width; to: pwShimmer.parent.width; duration: 1000; easing.type: Easing.InOutQuad }
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.topMargin: 6
                            spacing: 10
                            Item { Layout.fillWidth: true }
                            Rectangle {
                                implicitWidth: backTxt.implicitWidth + 36; implicitHeight: 40; radius: 20
                                color: backArea.containsMouse ? root.cSurface2 : "transparent"
                                border.color: root.cOutline; border.width: 1
                                opacity: root.dlgBusy ? 0.4 : 1
                                Text { id: backTxt; anchors.centerIn: parent; text: root.dlgStep === 1 ? "Daha sonra" : "Geri"; color: root.cFg; font.pixelSize: 14 }
                                MouseArea {
                                    id: backArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    enabled: !root.dlgBusy
                                    onClicked: { if (root.dlgStep === 1) root.deferAdmin(); else { root.dlgStep = 1; root.dlgError = ""; } }
                                }
                            }
                            Rectangle {
                                implicitWidth: okTxt.implicitWidth + 40; implicitHeight: 40; radius: 20
                                color: okArea.pressed ? Qt.darker(root.cAccent, 1.15) : root.cAccent
                                opacity: root.dlgBusy ? 0.5 : 1
                                Text { id: okTxt; anchors.centerIn: parent; text: root.dlgStep === 1 ? "İndir" : "Kur"; color: root.cBg; font.pixelSize: 14; font.weight: Font.DemiBold }
                                MouseArea {
                                    id: okArea; anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                    enabled: !root.dlgBusy
                                    onClicked: {
                                        if (root.dlgStep === 1) { root.dlgStep = 2; pwInput.text = ""; pwInput.forceActiveFocus(); }
                                        else root.submitPassword(pwInput.text)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
