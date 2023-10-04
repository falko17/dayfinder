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
    const parts = original.innerText.split("-");
    formatted.innerText = new Date(parts[0], parts[1] - 1, parts[2]).toLocaleDateString();
    original.style.opacity = 0;
    formatted.style.opacity = 1;
}