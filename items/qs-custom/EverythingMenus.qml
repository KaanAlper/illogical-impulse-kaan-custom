pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets

Rectangle {
    id: root
    implicitHeight: contentCol.implicitHeight + 16
    color: Appearance.colors.colLayer1

    readonly property var sortOptions: [
        { id: "relevance", label: "Eşleşme", icon: "auto_awesome" },
        { id: "name",      label: "İsim", icon: "sort_by_alpha" },
        { id: "size",      label: "Boyut", icon: "straighten" },
        { id: "type",      label: "Dosya tipi", icon: "category" },
        { id: "mtime",     label: "Değiştirme tarihi", icon: "schedule" }
    ]

    readonly property var filterOptions: [
        { id: "all",     label: "Tümü", icon: "select_all" },
        { id: "dir",     label: "Klasörler", icon: "folder" },
        { id: "file",    label: "Dosyalar", icon: "description" },
        { id: "image",   label: "Görseller", icon: "image" },
        { id: "video",   label: "Videolar", icon: "movie" },
        { id: "audio",   label: "Ses", icon: "music_note" },
        { id: "doc",     label: "Belgeler", icon: "article" },
        { id: "archive", label: "Arşivler", icon: "folder_zip" },
        { id: "exec",    label: "Uygulama / Exe / AppImage", icon: "sports_esports" },
        { id: "code",    label: "Kod / Config", icon: "code" }
    ]

    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 1
        color: Appearance.colors.colOutlineVariant
    }

    ColumnLayout {
        id: contentCol
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 10
        spacing: 8

        StyledText {
            Layout.leftMargin: 4
            font.pixelSize: Appearance.font.pixelSize.smaller
            color: Appearance.colors.colSubtext
            text: FileSearch.sortMenuOpen
                ? "Sırala (aynı öğeye tekrar tıkla: ↑ Artan / ↓ Azalan)"
                : "Dosya tipi filtresi"
        }

        Flow {
            Layout.fillWidth: true
            spacing: 6
            visible: FileSearch.sortMenuOpen

            Repeater {
                model: root.sortOptions
                delegate: RippleButton {
                    required property var modelData
                    readonly property bool active: FileSearch.sortBy === modelData.id
                    implicitWidth: sortRow.implicitWidth + 18
                    implicitHeight: 32
                    buttonRadius: Appearance.rounding.full
                    colBackground: active ? Appearance.colors.colPrimaryContainer : Appearance.colors.colSurfaceContainerHigh
                    colBackgroundHover: active ? Appearance.colors.colPrimaryContainer : Appearance.colors.colLayer2Hover
                    onClicked: FileSearch.setSort(modelData.id)

                    contentItem: RowLayout {
                        id: sortRow
                        anchors.centerIn: parent
                        spacing: 6
                        MaterialSymbol {
                            text: modelData.icon
                            iconSize: 17
                            color: active ? Appearance.colors.colOnPrimaryContainer : Appearance.m3colors.m3onSurface
                        }
                        StyledText {
                            font.pixelSize: Appearance.font.pixelSize.small
                            color: active ? Appearance.colors.colOnPrimaryContainer : Appearance.m3colors.m3onSurface
                            text: modelData.label
                        }
                        MaterialSymbol {
                            visible: active
                            text: FileSearch.sortOrder === "asc" ? "arrow_upward" : "arrow_downward"
                            iconSize: 17
                            color: Appearance.colors.colPrimary
                        }
                    }
                }
            }
        }

        Flow {
            Layout.fillWidth: true
            spacing: 6
            visible: FileSearch.filterMenuOpen

            Repeater {
                model: root.filterOptions
                delegate: RippleButton {
                    required property var modelData
                    readonly property bool active: FileSearch.filterType === modelData.id
                    implicitWidth: filterRow.implicitWidth + 18
                    implicitHeight: 32
                    buttonRadius: Appearance.rounding.full
                    colBackground: active ? Appearance.colors.colPrimaryContainer : Appearance.colors.colSurfaceContainerHigh
                    colBackgroundHover: active ? Appearance.colors.colPrimaryContainer : Appearance.colors.colLayer2Hover
                    onClicked: {
                        FileSearch.setFilter(modelData.id);
                        FileSearch.filterMenuOpen = false;
                    }

                    contentItem: RowLayout {
                        id: filterRow
                        anchors.centerIn: parent
                        spacing: 6
                        MaterialSymbol {
                            text: modelData.icon
                            iconSize: 17
                            color: active ? Appearance.colors.colOnPrimaryContainer : Appearance.m3colors.m3onSurface
                        }
                        StyledText {
                            font.pixelSize: Appearance.font.pixelSize.small
                            color: active ? Appearance.colors.colOnPrimaryContainer : Appearance.m3colors.m3onSurface
                            text: modelData.label
                        }
                    }
                }
            }
        }
    }
}
