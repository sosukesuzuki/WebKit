//@ requireOptions("--useRegExpModifiers=1")

function shouldThrow(func, errorMessage) {
    var errorThrown = false;
    var error = null;
    try {
        func();
    } catch (e) {
        errorThrown = true;
        error = e;
    }
    if (!errorThrown)
        throw new Error('not thrown');
    if (errorMessage) {
        if (String(error) !== errorMessage)
            throw new Error(`bad error: ${String(error)}`);
    }
}

function checkInvalidScriptSyntax(sourceCode, errorMessage) {
    shouldThrow(() => checkScriptSyntax(sourceCode), errorMessage);
}

checkScriptSyntax("/(?i:ba)r/");
checkScriptSyntax("/(?-i:ba)r/i");
checkScriptSyntax("/F(?i:oo(?-i:b)a)r/");
checkScriptSyntax("/F(?i:oo(?i:b)a)r/");
checkScriptSyntax("/^[a-z](?-i:[a-z])$/i");
checkScriptSyntax("/^(?i:[a-z])[a-z]$/");
checkScriptSyntax("/(?m:^foo$)/");
checkScriptSyntax("/(?s:^.$)/");
checkScriptSyntax("/(?ms-i:^f.o$)/i");
checkScriptSyntax("/(?m:^f(?si:.o)$)/");
checkScriptSyntax("/(?i:abc)/");
checkScriptSyntax("/(?-i:abc)/");
checkScriptSyntax("/(?ms:abc)/");
checkScriptSyntax("/(?-ms:abc)/");
checkScriptSyntax("/(?i-ms:abc)/");
checkScriptSyntax("/(?ms-i:abc)/");
checkScriptSyntax("/(?i:(?-m:abc))/");
checkScriptSyntax("/(?ms:(?i:abc))/");
checkScriptSyntax("/(?i:)/");
checkScriptSyntax("/(?i:a|b|c)/");
checkScriptSyntax("/(?ms:abc)+/");
checkScriptSyntax("/(?-i:\\w+)/");

checkInvalidScriptSyntax("/(?-:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?--:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?mm:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?ii:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?ss:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?-mm:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?-ii:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?-ss:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?g-:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?-u:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?m-m:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?i-i:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?s-s:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?msi-ims:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?i--m:.)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?z:abc)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?i-m+abc)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?abc)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?-:abc)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?i:(?-z:abc))/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/abc(?i)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?i)/", "SyntaxError: Invalid regular expression: unrecognized character after (?:1");
checkInvalidScriptSyntax("/(?i:a(b/", "SyntaxError: Invalid regular expression: missing ):1");
