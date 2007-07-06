function getSelected() {
    return getElement("foreback").value;
}

function updateDisplay() {
    var textbox = getElement("as_string");
    var current = getSelected();
    
    if (current == "Foreground") {
        textbox.value = Color.fromText("sample").toString();
    } else {
        textbox.value = Color.fromBackground("sample").toString();
    }
}

function setSampleFromElement(elem, toSet) {
    var elem = getElement(elem);
    var samplediv = getElement("sample");
    var color = Color.fromString(elem.value);
    if (color == null) {
        alert("Unknown color string");
        return;
    }
    samplediv.style[toSet] = color;
    updateDisplay();
}

function setColor() {
    var current = getSelected();
    if (current == "Foreground") {
        setSampleFromElement("as_string", "color");
    } else {
        setSampleFromElement("as_string", "background");
    }
}

function setForeground() {
    setSampleFromElement("foreground", "color");
}

function setBackground() {
    setSampleFromElement("background", "background");
}

function cloneColor() {
    var samplediv = getElement("sample");
    var current = getSelected();
    
    if (current == "Foreground") {
        samplediv.style.color = Color.fromText("header");
    } else {
        samplediv.style.background = Color.fromBackground("header");
    }
    
    updateDisplay();
    
}
