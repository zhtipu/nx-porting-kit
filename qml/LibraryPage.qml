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

    readonly property int gap: 16
    readonly property int cols: Math.max(1, Math.floor((width - 64 + gap) / (240 + gap)))
    readonly property real cardW: (width - 64 - gap * (cols - 1)) / cols

    ColumnLayout {
        id: col
        x: 32; y: 20
        width: page.width - 64
        spacing: 14

        PageHeader {
            Layout.fillWidth: true
            title: "Library"
            subtitle: "Pick a game to set up its Switch port"
        }

        Item { Layout.preferredHeight: 6 }

        Flow {
            Layout.fillWidth: true
            spacing: page.gap
            Repeater {
                model: page.app.library
                delegate: GameCard {
                    required property var modelData
                    required property int index
                    game: modelData
                    width: page.cardW
                    revealOn: page.active
                    order: index
                    onOpened: page.app.openGame(modelData.id)
                }
            }
        }

        Text {
            visible: page.app.library.length === 0
            text: "No games yet. Add a port folder to " + (page.app.settingsState.home || "") + "\\ports."
            color: Theme.textDim; font.family: Theme.font; font.pixelSize: 14
        }
    }
}
