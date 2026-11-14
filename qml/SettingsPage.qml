import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic

Flickable {
    id: page
    required property var app
    property bool active: false
    clip: true
    contentWidth: width
    contentHeight: col.implicitHeight + 56
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { }

    ColumnLayout {
        id: col
        x: 32; y: 20
        width: page.width - 64
        spacing: 14

        PageHeader { Layout.fillWidth: true; title: "Settings"; subtitle: "Keys, folders and updates" }

        Card {
            Layout.fillWidth: true; revealOn: page.active; order: 0
            ColumnLayout {
                width: parent.width; spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Switch keys"; color: Theme.text; font.family: Theme.font; font.pixelSize: 16; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    Chip { text: page.app.settingsState.keys ? "Saved" : "Not set up"; tone: page.app.settingsState.keys ? "good" : "accent"; glyph: page.app.settingsState.keys ? "" : "" }
                }
                Text {
                    Layout.fillWidth: true; wrapMode: Text.WordWrap
                    text: "Needed to build an NSP. Stored privately on this PC and never shared."
                    color: Theme.textDim; font.family: Theme.font; font.pixelSize: 13
                }
                RowLayout {
                    spacing: 8
                    Btn { text: page.app.settingsState.keys ? "Replace keys" : "Choose prod.keys"; glyph: ""; kind: "primary"
                          onClicked: {
                              var p = dialogs.pickFile("Choose your prod.keys", "Keys (*.keys);;All files (*)")
                              if (!p) return
                              var r = JSON.parse(bridge.importKeys(p))
                              page.app.toast(r.message, r.ok ? "good" : "bad"); page.app.reloadSettings()
                          } }
                    Btn { visible: page.app.settingsState.keys; text: "Remove"; kind: "danger"
                          onClicked: page.app.confirm("Remove your keys?", "NX Porting Kit deletes its own copy. Your original file is not touched.", "Remove", true,
                                                      function () { bridge.removeKeys(); page.app.reloadSettings(); page.app.toast("Keys removed", "info") }) }
                }
            }
        }

        Card {
            Layout.fillWidth: true; revealOn: page.active; order: 1
            ColumnLayout {
                width: parent.width; spacing: 12
                Text { text: "Output folder"; color: Theme.text; font.family: Theme.font; font.pixelSize: 16; font.weight: Font.DemiBold }
                RowLayout {
                    Layout.fillWidth: true; spacing: 8
                    Field { Layout.fillWidth: true; mono: true; readOnly: true; text: page.app.settingsState.output_dir || "" }
                    Btn { text: "Change"; onClicked: { var p = dialogs.pickFolder(page.app.settingsState.output_dir || ""); if (p) page.app.saveSettings({ output_dir: p.replace(/\//g, "\\") }) } }
                    Btn { text: "Open"; kind: "ghost"; onClicked: bridge.reveal(page.app.settingsState.output_dir) }
                }
            }
        }

        Card {
            Layout.fillWidth: true; revealOn: page.active; order: 2
            ColumnLayout {
                width: parent.width; spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Games"; color: Theme.text; font.family: Theme.font; font.pixelSize: 16; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    Text { text: "Check on start"; color: Theme.textDim; font.family: Theme.font; font.pixelSize: 13 }
                    Toggle { checked: page.app.settingsState.check_catalog; controlled: true; onToggled: page.app.saveSettings({ check_catalog: !page.app.settingsState.check_catalog }) }
                }
                Text {
                    Layout.fillWidth: true; wrapMode: Text.WordWrap
                    text: "Get new games and port updates."
                    color: Theme.textDim; font.family: Theme.font; font.pixelSize: 13
                }
                RowLayout {
                    spacing: 12
                    Btn { text: "Check for new games"; glyph: "\uE72C"; busy: page.app.checkingGames; enabled: !page.app.checkingGames; onClicked: page.app.checkGames() }
                    Text { visible: text !== ""; text: page.app.gamesResult; color: page.app.gamesResultBad ? Theme.bad : Theme.textDim; font.family: Theme.font; font.pixelSize: 13 }
                }
            }
        }

        Card {
            Layout.fillWidth: true; revealOn: page.active; order: 3
            ColumnLayout {
                width: parent.width; spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "NX Porting Kit " + (page.app.settingsState.version || ""); color: Theme.text; font.family: Theme.font; font.pixelSize: 16; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    Chip { visible: page.app.update.available === true; text: "Version " + (page.app.update.version || "") + " available"; tone: "accent"; glyph: "\uE896" }
                    Chip { visible: page.app.update.ok === true && page.app.update.available !== true; text: "Up to date"; tone: "good"; glyph: "\uE73E" }
                }
                Text {
                    visible: page.app.update.available === true && (page.app.update.notes || "") !== ""
                    Layout.fillWidth: true; wrapMode: Text.WordWrap
                    text: page.app.update.notes || ""
                    color: Theme.textDim; font.family: Theme.font; font.pixelSize: 13
                }
                Rectangle {
                    visible: page.app.updating
                    Layout.fillWidth: true; height: 6; radius: 3; color: Theme.surfaceHi; clip: true
                    Rectangle { height: parent.height; radius: 3; color: Theme.accent; width: parent.width * page.app.updateProgress
                                Behavior on width { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } } }
                }
                Text { visible: page.app.updateError !== ""; text: page.app.updateError; color: Theme.bad; font.family: Theme.font; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                RowLayout {
                    spacing: 8
                    Btn { visible: page.app.update.available !== true; text: "Check for updates"; glyph: "\uE72C"; busy: page.app.checkingUpdate; enabled: !page.app.checkingUpdate; onClicked: page.app.checkUpdate(true) }
                    Btn { visible: page.app.update.available === true && page.app.update.can_install === true; kind: "primary"; glyph: "\uE896"
                          text: page.app.updating ? "Updating" : "Update and restart"; busy: page.app.updating; enabled: !page.app.updating && !bridge.busy
                          onClicked: page.app.installUpdate() }
                }
            }
        }
    }
}
