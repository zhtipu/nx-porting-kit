import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import QtQuick.Controls.Basic

// The porting page. Generic: it reads everything from the selected game's port.json.
Flickable {
    id: page
    required property var app
    property bool active: false
    readonly property var g: app.game
    property string path: ""
    property var check: ({ ok: false, error: "" })
    readonly property bool soon: g ? g.status === "soon" : false
    readonly property bool needKeys: g ? g.needs_keys && !app.settingsState.keys : false
    readonly property bool ready: g && check.ok && g.blocked === "" && !soon && !needKeys

    clip: true
    contentWidth: width
    contentHeight: col.implicitHeight + 56
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { }

    onGChanged: { path = ""; check = ({ ok: false, error: "" }); contentY = 0 }
    onPathChanged: validate.restart()
    Timer {
        id: validate; interval: 220
        onTriggered: {
            if (!page.g || page.path.trim() === "") { page.check = ({ ok: false, error: "" }); return }
            page.check = JSON.parse(bridge.inspectGame(JSON.stringify({ id: page.g.id, path: page.path.trim() })))
        }
    }

    function setPathFromUrl(u) {
        var s = decodeURIComponent(u.toString().replace(/^file:\/\/\//, ""))
        path = s.replace(/\//g, "\\")
    }
    function begin(dry) {
        var r = JSON.parse(bridge.start(JSON.stringify({ id: g.id, path: path.trim() }), dry))
        if (!r.ok) { app.toast(r.error, "bad"); return }
        app.op.begin((dry ? "Preview: " : "Setting up ") + g.name, dry)
    }

    ColumnLayout {
        id: col
        x: 32; y: 20
        width: page.width - 64
        spacing: 14

        // Header: back, icon, title
        RowLayout {
            Layout.fillWidth: true; spacing: 16
            Btn { kind: "ghost"; glyph: ""; text: "Library"; onClicked: page.app.go(0) }
            Item { Layout.fillWidth: true }
        }
        RowLayout {
            Layout.fillWidth: true; spacing: 18
            Item {
                Layout.preferredWidth: 84; Layout.preferredHeight: 84
                Image {
                    anchors.fill: parent; source: page.g ? page.g.icon : ""; sourceSize: Qt.size(192, 192)
                    fillMode: Image.PreserveAspectCrop
                    layer.enabled: true; layer.effect: MultiEffect { maskEnabled: true; maskSource: gmask }
                }
                Item { id: gmask; width: 84; height: 84; visible: false; layer.enabled: true
                    Rectangle { anchors.fill: parent; radius: 18 } }
            }
            ColumnLayout {
                spacing: 4
                RowLayout {
                    spacing: 10
                    Text { text: page.g ? page.g.name : ""; color: Theme.text; font.family: Theme.fontDisplay; font.pixelSize: 30; font.weight: Font.DemiBold; font.letterSpacing: -0.5 }
                    Chip { visible: page.g && page.g.version !== ""; text: page.g ? "v" + page.g.version : ""; tone: "neutral" }
                    Chip { visible: page.soon; text: "Coming soon"; tone: "accent" }
                    Chip { visible: page.g && page.g.blocked !== ""; text: "Update app"; tone: "bad" }
                }
                Text { text: page.g ? page.g.tagline : ""; color: Theme.textDim; font.family: Theme.font; font.pixelSize: 15 }
            }
            Item { Layout.fillWidth: true }
        }

        Text {
            Layout.fillWidth: true; wrapMode: Text.WordWrap
            text: page.g ? page.g.about : ""
            color: Theme.textDim; font.family: Theme.font; font.pixelSize: 14; lineHeight: 1.25
        }

        // 1. Game files
        Card {
            Layout.fillWidth: true; revealOn: page.active; order: 1
            visible: !page.soon
            ColumnLayout {
                width: parent.width; spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Your game files"; color: Theme.text; font.family: Theme.font; font.pixelSize: 16; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    Chip { visible: page.check.ok; text: "Found: " + (page.check.label || ""); tone: "good"; glyph: "" }
                }
                Text { text: page.g && page.g.input ? page.g.input.hint : ""; color: Theme.textDim; font.family: Theme.font; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                RowLayout {
                    Layout.fillWidth: true; spacing: 8
                    Field {
                        id: pathField
                        Layout.fillWidth: true; mono: true
                        placeholderText: "Drop the package or folder here, or browse"
                        text: page.path
                        invalid: page.path.trim() !== "" && !page.check.ok
                        onTextEdited: page.path = text
                    }
                    Btn { text: "File"; glyph: ""; onClicked: { var p = dialogs.pickFile("Choose the game package", "All files (*)"); if (p) page.path = p.replace(/\//g, "\\") } }
                    Btn { text: "Folder"; glyph: ""; onClicked: { var p = dialogs.pickFolder(""); if (p) page.path = p.replace(/\//g, "\\") } }
                }
                Text {
                    visible: page.path.trim() !== "" && !page.check.ok && (page.check.error || "") !== ""
                    text: page.check.error || ""; color: Theme.bad
                    font.family: Theme.font; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap
                }
            }
            DropArea {
                anchors.fill: parent
                onDropped: function (d) { if (d.hasUrls) page.setPathFromUrl(d.urls[0]) }
            }
        }

        // 2. What will happen
        Card {
            Layout.fillWidth: true; revealOn: page.active; order: 2
            ColumnLayout {
                width: parent.width; spacing: 10
                Text { text: page.soon ? "Status" : "What happens"; color: Theme.text; font.family: Theme.font; font.pixelSize: 16; font.weight: Font.DemiBold }
                Repeater {
                    model: page.soon ? [] : (page.g ? page.g.steps : [])
                    delegate: RowLayout {
                        required property string modelData
                        required property int index
                        spacing: 12
                        Rectangle { Layout.preferredWidth: 22; Layout.preferredHeight: 22; radius: 11; color: Theme.surfaceHi
                            Text { anchors.centerIn: parent; text: index + 1; color: Theme.textDim; font.family: Theme.font; font.pixelSize: 11; font.weight: Font.DemiBold } }
                        Text { text: modelData; color: Theme.text; font.family: Theme.font; font.pixelSize: 14 }
                    }
                }
                Repeater {
                    model: page.g ? page.g.notes : []
                    delegate: Text { required property string modelData; text: modelData; color: Theme.textDim; font.family: Theme.font; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                }
                Text { visible: page.g && page.g.blocked !== ""; text: "This port " + (page.g ? page.g.blocked : "") + "."; color: Theme.bad; font.family: Theme.font; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            }
        }

        // 3. Output
        Card {
            Layout.fillWidth: true; revealOn: page.active; order: 3
            visible: !page.soon
            ColumnLayout {
                width: parent.width; spacing: 10
                Text { text: "Result"; color: Theme.text; font.family: Theme.font; font.pixelSize: 16; font.weight: Font.DemiBold }
                Text { text: page.g ? page.g.outputs : ""; color: Theme.textDim; font.family: Theme.font; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                RowLayout {
                    Layout.fillWidth: true; spacing: 8
                    Field { Layout.fillWidth: true; mono: true; readOnly: true; text: page.app.settingsState.output_dir || "" }
                    Btn { text: "Change"; onClicked: { var p = dialogs.pickFolder(page.app.settingsState.output_dir || ""); if (p) page.app.saveSettings({ output_dir: p.replace(/\//g, "\\") }) } }
                }
                RowLayout {
                    visible: page.needKeys; spacing: 10
                    Chip { text: "prod.keys needed"; tone: "accent"; glyph: "" }
                    Btn { text: "Open Settings"; kind: "ghost"; onClicked: page.app.go(1) }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true; spacing: 10
            visible: !page.soon
            Item { Layout.fillWidth: true }
            Btn { text: "Build NSP"; kind: "primary"; glyph: ""; enabled: page.ready && !bridge.busy; busy: bridge.busy; onClicked: page.begin(false) }
        }
    }
}
