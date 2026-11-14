import QtQuick
import QtQuick.Effects
import QtQuick.Layouts

// One game in the library. Everything shown comes from the game's port.json, nothing is game specific here.
Card {
    id: card
    required property var game
    signal opened()

    hoverable: true
    pad: 0
    implicitHeight: 292
    scale: tap.pressed ? 0.98 : 1
    Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }

    readonly property string tone: game.blocked !== "" ? "bad" : game.status === "stable" ? "good" : game.status === "beta" ? "info" : "neutral"
    readonly property string label: game.blocked !== "" ? "Update app" : game.status === "stable" ? "Ready" : game.status === "beta" ? "Beta" : "Coming soon"

    Item {
        width: card.width; height: card.height

        // Artwork: the game's icon over a soft wash of its own color.
        Item {
            id: art
            x: 12; y: 12; width: parent.width - 24; height: 168
            Rectangle {
                id: wash; anchors.fill: parent; radius: 12
                color: Theme.dark ? "#0F1217" : "#EEF0F5"
            }
            Rectangle {
                id: glow
                anchors.fill: parent; radius: 12
                readonly property color tint: card.game.accent !== "" ? card.game.accent : Theme.accent
                gradient: Gradient {
                    GradientStop { position: 0; color: Qt.rgba(glow.tint.r, glow.tint.g, glow.tint.b, card.hovered ? 0.34 : 0.22) }
                    GradientStop { position: 1; color: "transparent" }
                }
            }
            Image {
                id: img
                anchors.centerIn: parent
                width: 128; height: 128
                source: card.game.icon
                sourceSize: Qt.size(256, 256)
                fillMode: Image.PreserveAspectCrop
                smooth: true
                opacity: card.game.status === "soon" ? 0.55 : 1
                layer.enabled: true
                layer.effect: MultiEffect { maskEnabled: true; maskSource: maskItem }
                scale: card.hovered ? 1.04 : 1
                Behavior on scale { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
            }
            Item {
                id: maskItem; width: 128; height: 128; visible: false; layer.enabled: true
                Rectangle { anchors.fill: parent; radius: 26 }
            }
            Chip {
                anchors { top: parent.top; right: parent.right; topMargin: 10; rightMargin: 10 }
                text: card.label; tone: card.tone
            }
        }

        Column {
            x: 18; y: 196; width: parent.width - 36; spacing: 4
            Text {
                width: parent.width; text: card.game.name; elide: Text.ElideRight
                color: Theme.text; font.family: Theme.fontDisplay; font.pixelSize: 19; font.weight: Font.DemiBold
                font.letterSpacing: -0.2
            }
            Text {
                width: parent.width; text: card.game.tagline; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight
                color: Theme.textDim; font.family: Theme.font; font.pixelSize: 13
            }
        }
    }

    HoverHandler { cursorShape: Qt.PointingHandCursor }
    TapHandler { id: tap; onTapped: card.opened() }
}
