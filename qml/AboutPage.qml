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

        PageHeader { Layout.fillWidth: true; title: "About" }

        // App
        Card {
            Layout.fillWidth: true; revealOn: page.active; order: 0
            RowLayout {
                width: parent.width; spacing: 22
                Image { Layout.preferredWidth: 84; Layout.preferredHeight: 84; Layout.alignment: Qt.AlignTop
                        source: "../assets/icon.png"; sourceSize: Qt.size(168, 168); smooth: true; mipmap: true }
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 10
                    Text { text: "NX Porting Kit"; color: Theme.text; font.family: Theme.fontDisplay; font.pixelSize: 28; font.weight: Font.DemiBold; font.letterSpacing: -0.5 }
                    Row {
                        spacing: 8
                        Chip { text: "App " + (page.app.settingsState.version || ""); tone: "accent" }
                        Chip { text: "Windows" }
                    }
                    Text {
                        Layout.fillWidth: true; wrapMode: Text.WordWrap; lineHeight: 1.25
                        text: "Native Nintendo Switch ports of Xbox 360 games. Pick a game, add your copy, and get an installable NSP."
                        color: Theme.textDim; font.family: Theme.font; font.pixelSize: 14
                    }
                }
            }
        }

        // Developer
        Card {
            Layout.fillWidth: true; revealOn: page.active; order: 1
            ColumnLayout {
                width: parent.width; spacing: 8
                Text { text: "DEVELOPED BY"; color: Theme.textFaint; font.family: Theme.font; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 0.8 }
                Text { text: "Zahidul Haque Tipu"; color: Theme.text; font.family: Theme.fontDisplay; font.pixelSize: 22; font.weight: Font.DemiBold; font.letterSpacing: -0.3 }
                RowLayout {
                    Layout.fillWidth: true; Layout.topMargin: 10
                    Text { text: "github.com/zhtipu"; color: Theme.textDim; font.family: Theme.mono; font.pixelSize: 13; Layout.fillWidth: true }
                    Btn { text: "Open on GitHub"; kind: "primary"; onClicked: bridge.openUrl("https://github.com/zhtipu") }
                }
            }
        }

        // Fine print
        Card {
            Layout.fillWidth: true; revealOn: page.active; order: 2
            RowLayout {
                width: parent.width; spacing: 16
                Text {
                    Layout.fillWidth: true; wrapMode: Text.WordWrap; lineHeight: 1.25
                    text: "No games or Switch keys are included. You need your own copy of each game and your own prod.keys."
                    color: Theme.textDim; font.family: Theme.font; font.pixelSize: 13
                }
                Btn { text: "Open-source notices"; kind: "primary"; onClicked: bridge.openNotices() }
            }
        }
    }
}
