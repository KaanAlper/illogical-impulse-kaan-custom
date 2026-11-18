pragma Singleton
pragma ComponentBehavior: Bound

import qs.modules.common
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    readonly property string homeDir: (Quickshell.env("HOME") || "/home").replace(/\/$/, "")
    readonly property string cacheDir: (Quickshell.env("XDG_CACHE_HOME") || (homeDir + "/.cache")) + "/everything"
    readonly property string dbPath: cacheDir + "/plocate.db"
    readonly property string updateScript: Quickshell.shellPath("scripts/everything-update.sh")

    property string pendingQuery: ""
    property string lastCompletedQuery: ""
    property list<string> results: []
    property bool indexingStarted: false

    function ensureIndex() {
        if (root.indexingStarted)
            return;
        root.indexingStarted = true;
        ensureProc.running = true;
    }

    function updateQuery(rawQuery: string) {
        const q = (rawQuery ?? "").trim();
        if (q === root.pendingQuery && (q === root.lastCompletedQuery || searchProc.running || debounceTimer.running))
            return;
        root.pendingQuery = q;
        if (q === "") {
            debounceTimer.stop();
            return;
        }
        debounceTimer.restart();
    }

    function openFile(path: string) {
        Quickshell.execDetached(["xdg-open", path]);
    }

    function openFolder(path: string) {
        const idx = path.lastIndexOf("/");
        const dir = idx > 0 ? path.slice(0, idx) : "/";
        Quickshell.execDetached(["xdg-open", dir]);
    }

    function copyPath(path: string) {
        Quickshell.clipboardText = path;
    }

    function displayDir(path: string): string {
        const idx = path.lastIndexOf("/");
        const dir = idx > 0 ? path.slice(0, idx) : "/";
        if (dir === root.homeDir)
            return "~";
        if (dir.startsWith(root.homeDir + "/"))
            return "~" + dir.slice(root.homeDir.length);
        return dir;
    }

    function fileName(path: string): string {
        const idx = path.lastIndexOf("/");
        return idx >= 0 ? path.slice(idx + 1) : path;
    }

    function rankResults(paths: list<string>, query: string): list<string> {
        const qLower = query.toLowerCase();
        const terms = qLower.split(/\s+/).filter(Boolean);
        const primary = terms[0] ?? "";
        const homePrefix = root.homeDir + "/";

        const scored = [];
        for (let i = 0; i < paths.length; i++) {
            const p = paths[i];
            if (!p)
                continue;
            const slash = p.lastIndexOf("/");
            const base = (slash >= 0 ? p.slice(slash + 1) : p).toLowerCase();
            let score = 0;
            if (p.startsWith(homePrefix) || p === root.homeDir)
                score += 1000;
            if (primary.length > 0) {
                if (base === primary)
                    score += 500;
                else if (base.startsWith(primary))
                    score += 300;
                else if (base.includes(primary))
                    score += 200;
            }
            score -= p.length * 0.1;
            scored.push({ path: p, score: score });
        }
        scored.sort((a, b) => b.score - a.score);
        return scored.slice(0, 40).map(item => item.path);
    }

    function runSearch() {
        const q = root.pendingQuery;
        if (q === "")
            return;
        const terms = q.split(/\s+/).filter(Boolean);
        if (terms.length === 0)
            return;

        searchProc.running = false;
        searchProc.queryAtLaunch = q;
        searchProc.buffer = [];
        // Use plocate if DB exists; otherwise trigger background index build and fall back to fd in $HOME.
        searchProc.command = [
            "bash", "-c",
            "db=\"$1\"; script=\"$2\"; shift 2; " +
            "if [ -s \"$db\" ]; then exec plocate -d \"$db\" -i -l 200 -- \"$@\"; " +
            "else [ -x \"$script\" ] && nohup \"$script\" >/dev/null 2>&1 & " +
            "exec fd -i -L --max-results 100 -- \"$1\" \"$HOME\"; fi",
            "_", root.dbPath, root.updateScript, ...terms
        ];
        searchProc.running = true;
    }

    Timer {
        id: debounceTimer
        interval: 35
        onTriggered: root.runSearch()
    }

    Process {
        id: ensureProc
        command: ["bash", "-c", "[ -s \"$1\" ] || { [ -x \"$2\" ] && \"$2\"; }", "_", root.dbPath, root.updateScript]
    }

    Process {
        id: searchProc
        property string queryAtLaunch: ""
        property list<string> buffer: []

        stdout: SplitParser {
            onRead: data => {
                if (data && data.length > 0)
                    searchProc.buffer.push(data);
            }
        }

        onExited: (exitCode, exitStatus) => {
            root.lastCompletedQuery = searchProc.queryAtLaunch;
            root.results = root.rankResults(searchProc.buffer, searchProc.queryAtLaunch);
            if (root.pendingQuery !== searchProc.queryAtLaunch && root.pendingQuery !== "")
                debounceTimer.restart();
        }
    }
}
