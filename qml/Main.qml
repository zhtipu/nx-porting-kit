import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1160; height: 780
    minimumWidth: 980; minimumHeight: 660
    visible: true
    title: "NX Porting Kit"
    color: Theme.bg

    // 0 library, 1 settings, 2 about, 3 game (the sidebar keeps "Library" lit while a game is open)
    property int cur: typeof startPage !== "undefined" ? startPage : 0
    property var library: []
    property var game: null
    property var settingsState: ({})
    property var update: ({})
    property bool checkingGames: false
    property bool checkingUpdate: false
    property bool updating: false
    property real updateProgress: 0
    property string updateError: ""
    property string gamesResult: ""
    property bool gamesResultBad: false
    readonly property Item overlayRoot: overlay
    readonly property var op: opSheet
    readonly property int navIndex: cur === 3 ? 0 : cur

    function go(i) { cur = i }
    function toast(msg, kind) { toaster.show(msg, kind || "info") }
    function confirm(title, msg, label, danger, cb) { confirmSheet.ask(title, msg, label, danger, cb) }
    function reloadLibrary() { library = JSON.parse(bridge.library()) }
    function reloadSettings() { settingsState = JSON.parse(bridge.settingsState()) }
    function saveSettings(patch) { settingsState = JSON.parse(bridge.saveSettings(JSON.stringify(patch))) }
    function checkGames() { checkingGames = true; gamesResult = ""; bridge.refreshCatalog(true) }
    function checkUpdate(manual) { checkingUpdate = true; updateError = ""; bridge.checkUpdate() }
    function installUpdate() { updating = true; updateProgress = 0; updateError = ""; bridge.installUpdate() }
    function openGame(id) {
        for (var i = 0; i < library.length; i++) if (library[i].id === id) { game = library[i]; cur = 3; return }
    }

    Component.onCompleted: {
        reloadSettings(); reloadLibrary()
        if (typeof startGame !== "undefined" && startGame !== "") openGame(startGame)
        bridge.refreshCatalog(false)
        bridge.checkUpdate()
    }
    Connections {
        target: bridge
        function onOpEvent(s) { opSheet.handle(JSON.parse(s)) }
        function onCatalogChecked(s) {
            var r = JSON.parse(s)
            root.checkingGames = false
            if (r.new.length || r.updated.length) root.reloadLibrary()
            if (!r.manual) return
            root.gamesResultBad = !r.ok
            if (!r.ok) root.gamesResult = r.error
            else if (r.new.length) root.gamesResult = r.new.length === 1 ? r.new[0] + " was added" : r.new.length + " new games added"
            else if (r.updated.length) root.gamesResult = r.updated.join(", ") + " updated"
            else root.gamesResult = "Your library is up to date"
            root.toast(root.gamesResult, r.ok ? "good" : "bad")
        }
        function onUpdateInfo(s) { root.update = JSON.parse(s); root.checkingUpdate = false }
        function onUpdateProgress(v) { root.updateProgress = v }
        function onUpdateFailed(m) { root.updating = false; root.updateError = m }
        function onQuitForUpdate() { Qt.quit() }
    }

    Row {
        anchors.fill: parent

        Rectangle {
            id: side
            width: 240; height: parent.height
            color: Theme.sidebar
            Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: Theme.border }

            Row {
                x: 22; y: 26; spacing: 10
                Image { width: 30; height: 30; source: "../assets/icon.png"; sourceSize: Qt.size(64, 64); smooth: true; mipmap: true }
                Text { text: "NX Porting Kit"; color: Theme.text; font.family: Theme.fontDisplay; font.pixelSize: 18; font.weight: Font.DemiBold; anchors.verticalCenter: parent.verticalCenter }
            }

            Rectangle {
                id: updPill
                visible: root.update.available === true
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 12 }
                height: 44; radius: 11; color: Theme.accentSoft; border.width: 1
                border.color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.5)
                scale: updTap.pressed ? 0.97 : 1
                Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
                Row {
                    anchors.centerIn: parent; spacing: 10
                    Icon { text: "\uE896"; size: 16; tint: Theme.accent; anchors.verticalCenter: parent.verticalCenter }
                    Text { text: "Update available"; color: Theme.text; font.family: Theme.font; font.pixelSize: 13; font.weight: Font.DemiBold; anchors.verticalCenter: parent.verticalCenter }
                }
                HoverHandler { cursorShape: Qt.PointingHandCursor }
                TapHandler { id: updTap; onTapped: root.cur = 1 }
            }

            Item {
                id: nav
                x: 12; y: 100; width: parent.width - 24; height: model.length * 48
                readonly property var model: [ { t: "Library", g: "\uE80F" }, { t: "Settings", g: "\uE713" }, { t: "About", g: "\uE946" } ]

                Rectangle {
                    width: parent.width; height: 42; radius: 11
                    y: root.navIndex * 48 + 3
                    color: Theme.accentSoft; border.width: 1; border.color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.5)
                    Behavior on y { SpringAnimation { spring: 4.2; damping: 0.38; mass: 0.7 } }
                    Rectangle { anchors.verticalCenter: parent.verticalCenter; width: 3; height: 18; radius: 2; color: Theme.accent }
                }
                Repeater {
                    model: nav.model
                    delegate: Item {
                        y: index * 48; width: nav.width; height: 48
                        Row {
                            x: 16; anchors.verticalCenter: parent.verticalCenter; spacing: 14
                            Icon { text: modelData.g; size: 17; tint: root.navIndex === index ? Theme.accent : Theme.textDim; anchors.verticalCenter: parent.verticalCenter }
                            Text { text: modelData.t; color: root.navIndex === index || hh.hovered ? Theme.text : Theme.textDim; font.family: Theme.font; font.pixelSize: 14; font.weight: root.navIndex === index ? Font.DemiBold : Font.Medium; anchors.verticalCenter: parent.verticalCenter
                                Behavior on color { ColorAnimation { duration: Theme.fast } } }
                        }
                        HoverHandler { id: hh; cursorShape: Qt.PointingHandCursor }
                        TapHandler { onTapped: root.cur = index }
                    }
                }
            }
        }

        Item {
            width: parent.width - side.width; height: parent.height

            LibraryPage { app: root; anchors.fill: parent; active: root.cur === 0; opacity: active ? 1 : 0; visible: opacity > 0.01
                Behavior on opacity { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } } }
            SettingsPage { app: root; anchors.fill: parent; active: root.cur === 1; opacity: active ? 1 : 0; visible: opacity > 0.01
                Behavior on opacity { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } } }
            AboutPage { app: root; anchors.fill: parent; active: root.cur === 2; opacity: active ? 1 : 0; visible: opacity > 0.01
                Behavior on opacity { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } } }
            GamePage { app: root; anchors.fill: parent; active: root.cur === 3; opacity: active ? 1 : 0; visible: opacity > 0.01
                Behavior on opacity { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } } }
        }
    }

    Item { id: overlay; anchors.fill: parent; z: 40 }
    ConfirmSheet { id: confirmSheet; parent: overlay }
    OpSheet {
        id: opSheet; parent: overlay
        onCancelRequested: bridge.cancel()
        onRevealRequested: function (p) { bridge.reveal(p) }
    }

    Rectangle {
        id: toaster
        property string kind: "info"
        property string msg: ""
        property bool shown: false
        function show(m, k) { msg = m; kind = k; hide.restart(); shown = true }
        z: 100
        anchors.horizontalCenter: parent.horizontalCenter
        y: shown ? parent.height - height - 28 : parent.height + 8
        Behavior on y { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
        opacity: shown ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 200 } }
        height: 44; width: Math.min(toastRow.implicitWidth + 36, root.width - 40); radius: 22
        color: Theme.dark ? "#262C38" : "#1A1D24"; border.width: 1; border.color: Theme.borderHi
        Row {
            id: toastRow; anchors.centerIn: parent; spacing: 10
            Rectangle { width: 8; height: 8; radius: 4; anchors.verticalCenter: parent.verticalCenter; color: toaster.kind === "good" ? Theme.good : toaster.kind === "bad" ? Theme.bad : Theme.info }
            Text { text: toaster.msg; color: "#F2F4F8"; font.family: Theme.font; font.pixelSize: 14; anchors.verticalCenter: parent.verticalCenter; elide: Text.ElideRight; width: Math.min(implicitWidth, root.width - 100) }
        }
        Timer { id: hide; interval: 3500; onTriggered: toaster.shown = false }
    }
}
