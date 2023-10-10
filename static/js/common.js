Telegram.WebApp.ready();

/**
 * Replaces all date elements with their localized versions.
 */
function replaceDateElements() {
    for (const dateElement of document.getElementsByClassName("displayed-date")) {
        replaceDateElement(dateElement);
    }
}

/**
 * Replaces a date element with its localized version.
 * @param element The element to replace.
 */
function replaceDateElement(element) {
    // We use these two to achieve a smooth transition.
    const original = element.getElementsByClassName("original-date")[0];
    const formatted = element.getElementsByClassName("formatted-date")[0];
    // YYYY-MM-DD
    formatted.textContent = new Date(original.textContent).toLocaleDateString();
    original.style.opacity = 0;
    formatted.style.opacity = 1;
}

/**
 * Executes the given callback if the user's Telegram version is at least the given version.
 * An alternative callback can be specified to be executed otherwise.
 *
 * @param version The minimum version required for the callback to be executed.
 * @param callback The callback to execute if the user's Telegram version is at least the given version.
 * @param alternative The callback to execute if the user's Telegram version is lower than the given version.
 */
function runOnVersion(version, callback, alternative = () => {}) {
    if (Telegram.WebApp.isVersionAtLeast(version)) {
        callback();
    } else {
        alternative();
    }
}

/**
 * Shows an alert to the user and executes the given callback when the alert is closed.
 * We try to show a native alert if possible, otherwise we fall back to a browser alert.
 *
 * @param text The text to show in the alert.
 * @param callback The callback to execute when the alert is closed.
 */
function showAlert(text, callback) {
    runOnVersion('6.2', () => {
        Telegram.WebApp.showAlert(text, callback);
    }, () => {
        alert(text);
        callback();
    });
}