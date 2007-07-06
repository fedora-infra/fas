// getElementDimensions, getElementPosition

function updateStatus() {
    var e = getElement("thetestelem");
    
    var dim = getElementDimensions(e);
    var pos = getElementPosition(e);
    
    getElement("dimensions").innerHTML = repr(dim);
    getElement("coordinates").innerHTML = repr(pos);

    getElement("width").value = dim.w;
    getElement("height").value = dim.h;
    
    getElement("x").value = pos.x;
    getElement("y").value = pos.y;
}

// showElement and hideElement

function hideTheTestElem() {
    // Toggles our guinea testelem element
    
    var button = getElement("hidebutton");
    if (button.value == "Hide Element") {
        hideElement("thetestelem");
        button.value = "Show Element";
    } else {
        showElement("thetestelem");
        button.value = "Hide Element";
    }
    updateStatus();
}

// setElementDimensions

function setTestElemDimensions() {
    var e = getElement("thetestelem");
    var dim = new Dimensions(getElement("width").value,
                         getElement("height").value);
    setElementDimensions(e, dim);
    updateStatus();
}

// setElementPosition

function setTestElemPosition() {
    var e = getElement("thetestelem");
    var pos = new Coordinates(getElement("x").value,
                         getElement("y").value);
    setElementPosition(e, pos);
    updateStatus();
}

// setOpacity

function setTestElemOpacity() {
    setOpacity("thetestelem", getElement("opacity").value);
}

// computedStyle

function getTestElemStyle() {
    var prop = getElement("testelemprop").value;
    var style = computedStyle("thetestelem", prop);
    getElement("testelemstyle").innerHTML = style;
}