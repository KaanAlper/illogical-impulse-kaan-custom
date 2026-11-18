#!/usr/bin/env python3
"""Idempotently patch Quickshell ii overview & search for Everything-style (#) file search."""

import pathlib
import sys


def patch_file(path: pathlib.Path, replacements: list[tuple[str, str, str]]) -> bool:
    """Apply (guard, target, replacement) tuples idempotently. Returns True if OK."""
    if not path.exists():
        sys.stderr.write(f"  UYARI: {path} bulunamadi.\n")
        return False
    src = path.read_text(encoding="utf-8")
    changed = False
    for guard, target, replacement in replacements:
        if guard in src:
            continue
        if target not in src:
            sys.stderr.write(f"  UYARI: {path.name} icinde hedef bulunamadi ({guard}).\n")
            return False
        src = src.replace(target, replacement, 1)
        changed = True
    if changed:
        path.write_text(src, encoding="utf-8")
        print(f"  {path.name}: Everything (#) yamasi uygulandi")
    else:
        print(f"  {path.name}: zaten yamali")
    return True


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write("Kullanim: patch-everything.py <quickshell-ii-dir>\n")
        return 2
    ii = pathlib.Path(sys.argv[1])
    ok = True

    # 1. Config.qml: add search.prefix.files = "#"
    ok &= patch_file(
        ii / "modules/common/Config.qml",
        [
            (
                'property string files: "#"',
                'property string emojis: ":"',
                'property string emojis: ":"\n                    property string files: "#"',
            ),
        ],
    )

    # 2. Overview.qml: toggleFiles(), IPC filesToggle(), GlobalShortcut overviewFilesToggle
    ok &= patch_file(
        ii / "modules/ii/overview/Overview.qml",
        [
            (
                "function toggleFiles()",
                "    function toggleEmojis() {",
                "    function toggleFiles() {\n"
                "        if (GlobalStates.overviewOpen && overviewScope.dontAutoCancelSearch) {\n"
                "            GlobalStates.overviewOpen = false;\n"
                "            return;\n"
                "        }\n"
                "        overviewScope.dontAutoCancelSearch = true;\n"
                "        panelWindow.setSearchingText(Config.options.search.prefix.files);\n"
                "        GlobalStates.overviewOpen = true;\n"
                "    }\n\n"
                "    function toggleEmojis() {",
            ),
            (
                "function filesToggle()",
                "        function clipboardToggle() {\n            overviewScope.toggleClipboard();\n        }",
                "        function clipboardToggle() {\n            overviewScope.toggleClipboard();\n        }\n"
                "        function filesToggle() {\n            overviewScope.toggleFiles();\n        }",
            ),
            (
                'name: "overviewFilesToggle"',
                "    GlobalShortcut {\n        name: \"overviewEmojiToggle\"",
                "    GlobalShortcut {\n"
                "        name: \"overviewFilesToggle\"\n"
                "        description: \"Toggle file search (Everything) on overview widget\"\n\n"
                "        onPressed: {\n"
                "            overviewScope.toggleFiles();\n"
                "        }\n"
                "    }\n\n"
                "    GlobalShortcut {\n        name: \"overviewEmojiToggle\"",
            ),
        ],
    )

    # 3. SearchBar.qml: SearchPrefixType.Files + shape + material icon
    ok &= patch_file(
        ii / "modules/ii/overview/SearchBar.qml",
        [
            (
                "Clipboard, Emojis, Files,",
                "enum SearchPrefixType { Action, App, Clipboard, Emojis, Math, ShellCommand, WebSearch, DefaultSearch }",
                "enum SearchPrefixType { Action, App, Clipboard, Emojis, Files, Math, ShellCommand, WebSearch, DefaultSearch }",
            ),
            (
                "SearchBar.SearchPrefixType.Files;",
                "if (root.searchingText.startsWith(Config.options.search.prefix.emojis)) return SearchBar.SearchPrefixType.Emojis;",
                "if (root.searchingText.startsWith(Config.options.search.prefix.emojis)) return SearchBar.SearchPrefixType.Emojis;\n"
                "        if (root.searchingText.startsWith(Config.options.search.prefix.files)) return SearchBar.SearchPrefixType.Files;",
            ),
            (
                "case SearchBar.SearchPrefixType.Files: return MaterialShape.Shape.Pentagon;",
                "case SearchBar.SearchPrefixType.Emojis: return MaterialShape.Shape.Sunny;",
                "case SearchBar.SearchPrefixType.Emojis: return MaterialShape.Shape.Sunny;\n"
                "            case SearchBar.SearchPrefixType.Files: return MaterialShape.Shape.Pentagon;",
            ),
            (
                'case SearchBar.SearchPrefixType.Files: return "folder_open";',
                'case SearchBar.SearchPrefixType.Emojis: return "add_reaction";',
                'case SearchBar.SearchPrefixType.Emojis: return "add_reaction";\n'
                '            case SearchBar.SearchPrefixType.Files: return "folder_open";',
            ),
        ],
    )

    # 4. SearchWidget.qml: cleanOnePrefix includes prefix.files
    ok &= patch_file(
        ii / "modules/ii/overview/SearchWidget.qml",
        [
            (
                "Config.options.search.prefix.files",
                "Config.options.search.prefix.emojis, Config.options.search.prefix.math",
                "Config.options.search.prefix.emojis, Config.options.search.prefix.files, Config.options.search.prefix.math",
            ),
        ],
    )

    # 5. LauncherSearch.qml: ensurePrefix + # file search branch
    ok &= patch_file(
        ii / "services/LauncherSearch.qml",
        [
            (
                "Config.options.search.prefix.files, Config.options.search.prefix.math",
                "Config.options.search.prefix.emojis, Config.options.search.prefix.math",
                "Config.options.search.prefix.emojis, Config.options.search.prefix.files, Config.options.search.prefix.math",
            ),
            (
                "FileSearch.updateQuery",
                "        }\n\n        ////////////////// Init ///////////////////",
                "        } else if (root.query.startsWith(Config.options.search.prefix.files)) {\n"
                "            // Everything-style file search\n"
                "            const searchString = StringUtils.cleanPrefix(root.query, Config.options.search.prefix.files);\n"
                "            if (searchString.trim() === \"\") {\n"
                "                FileSearch.ensureIndex();\n"
                "                return [];\n"
                "            }\n"
                "            FileSearch.updateQuery(searchString);\n"
                "            return FileSearch.results.map(filePath => {\n"
                "                return resultComp.createObject(null, {\n"
                "                    rawValue: filePath,\n"
                "                    name: FileSearch.fileName(filePath),\n"
                "                    type: FileSearch.displayDir(filePath),\n"
                "                    verb: Translation.tr(\"Open\"),\n"
                "                    iconName: \"description\",\n"
                "                    iconType: LauncherSearchResult.IconType.Material,\n"
                "                    execute: () => {\n"
                "                        FileSearch.openFile(filePath);\n"
                "                    },\n"
                "                    actions: [\n"
                "                        resultComp.createObject(null, {\n"
                "                            name: Translation.tr(\"Open folder\"),\n"
                "                            iconName: \"folder_open\",\n"
                "                            iconType: LauncherSearchResult.IconType.Material,\n"
                "                            execute: () => {\n"
                "                                FileSearch.openFolder(filePath);\n"
                "                            }\n"
                "                        }),\n"
                "                        resultComp.createObject(null, {\n"
                "                            name: Translation.tr(\"Copy path\"),\n"
                "                            iconName: \"content_copy\",\n"
                "                            iconType: LauncherSearchResult.IconType.Material,\n"
                "                            execute: () => {\n"
                "                                FileSearch.copyPath(filePath);\n"
                "                            }\n"
                "                        })\n"
                "                    ]\n"
                "                });\n"
                "            }).filter(Boolean);\n"
                "        }\n\n"
                "        ////////////////// Init ///////////////////",
            ),
        ],
    )

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
