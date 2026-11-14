pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: Qt.styleHints.colorScheme !== Qt.ColorScheme.Light

    readonly property color bg: dark ? "#0E1014" : "#F4F5F8"
    readonly property color sidebar: dark ? "#12151B" : "#EBEDF2"
    readonly property color surface: dark ? "#171B22" : "#FFFFFF"
    readonly property color surfaceHi: dark ? "#1F242D" : "#F6F7FA"
    readonly property color border: dark ? "#272D38" : "#E1E4EA"
    readonly property color borderHi: dark ? "#3A4252" : "#CBD0DA"
    readonly property color text: dark ? "#EEF0F5" : "#14171D"
    readonly property color textDim: dark ? "#98A1B1" : "#5C6573"
    readonly property color textFaint: dark ? "#667085" : "#8A93A2"

    readonly property color accent: dark ? "#00C3E3" : "#0094B3"
    readonly property color accentHi: dark ? "#3BD6EE" : "#00A9CC"
    readonly property color accentInk: dark ? "#00222B" : "#FFFFFF"
    readonly property color accentSoft: dark ? "#0C2831" : "#DDF4FA"
    readonly property color good: "#34C77B"
    readonly property color goodSoft: dark ? "#14281D" : "#E3F7EC"
    readonly property color bad: "#F2566F"
    readonly property color badSoft: dark ? "#2C161B" : "#FDE7EB"
    readonly property color info: "#5B8DEF"
    readonly property color infoSoft: dark ? "#16213A" : "#E6EEFD"

    readonly property int radius: 16
    readonly property int radiusSm: 10
    readonly property string font: "Segoe UI Variable Text"
    readonly property string fontDisplay: "Segoe UI Variable Display"
    readonly property string mono: "Cascadia Mono"
    readonly property string icons: "Segoe Fluent Icons"

    // Strong ease-out: starts fast so the interface feels like it heard the click.
    readonly property var easeOut: [0.23, 1, 0.32, 1, 1, 1]
    readonly property int fast: 140
    readonly property int base: 220
    readonly property int slow: 360
}
