function cancelEdit(element) {
    switchOff(element + 'Form')
    appear(element)
}

function formEdit(element) {
    var elements = Array("givenName", "mail", "fedoraPersonBugzillaMail", "fedoraPersonIrcNick", "fedoraPersonKeyId", "telephoneNumber", "postalAddress", "description")
    for(var i = 0; i != elements.length; i++) {
        if (elements[i] != element) {
            var form = document.getElementById(elements[i] + 'Form');
            if ( form.style.display != 'none') {
                new Highlight(elements[i] + 'Form');
                return false;
            }
        }
    }
    switchOff(element);
    appear(element + 'Form');
}

function displayHelp(helpID) {
    grow('helpMessageMain');
    getElement('helpMessage').innerHTML = 'Please Wait...';
    //d = MochiKit.Async.doSimpleXMLHttpRequest('/fas/help', {});
    var d = loadJSONDoc('/fas/help', {helpID: helpID});
    var gotMetadata = function (meta) {
        getElement('helpMessage').innerHTML = meta.help
    };
    //getElement('helpMessage').innerHTML = d.help;
    var metadataFetchFailed = function (err) {
        getElement('helpMessage').innerHTML = 'Could not fetch help message!'
    };
    d.addCallbacks(gotMetadata, metadataFetchFailed)
    return false;
}