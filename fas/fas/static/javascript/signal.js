var currentSelected = null;

function changeSelected(e) {
    if (currentSelected != null) {
        logDebug("Disconnecting " + currentSelected);
        disconnectAll(currentSelected);
    }
    var es = getElement("elemselect");
    currentSelected = es.value;
    var ev = getElement("eventselect").value;
    logDebug("Connecting " + currentSelected + " for event " + ev);
    connect(currentSelected, ev, log);
}
