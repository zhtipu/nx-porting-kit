import QtQuick

// Segoe Fluent Icons glyph. Pass the code point as a string, e.g. "".
Text {
    property color tint: Theme.text
    property int size: 18
    color: tint
    font.family: Theme.icons
    font.pixelSize: size
    horizontalAlignment: Text.AlignHCenter
    verticalAlignment: Text.AlignVCenter
    renderType: Text.NativeRendering
}
