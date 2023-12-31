Telegram.WebApp.MainButton.setText('Share with chat').show().onClick(shareResults);

// The button to expand or collapse all elements.
let expandButton;

// Contains the collapse elements.
let collapseElements;

window.addEventListener('load', function () {

    if (Telegram.WebApp.colorScheme === "dark") {
        document.body.classList.add("dark");
    }

    // We want to display all dates in the user's locale.
    replaceDateElements();


    const ownerId = Number(document.getElementById("ownerId").value);
    // It's fine to use the unsafe version of initData here – the server will validate the ID on deletion.
    if (Object.keys(Telegram.WebApp.initDataUnsafe).length > 0 && Telegram.WebApp.initDataUnsafe.user.id === ownerId) {
        const deleteButton = document.getElementById("deleteButton");
        deleteButton.classList.remove("d-none");
        deleteButton.classList.add("d-block");
        deleteButton.onclick = askDeletePoll;
    }

    const isAnonymous = document.getElementById("isAnonymous").value === "True";
    if (!isAnonymous) {
        // We only want non-empty groups to be expandable.
        collapseElements = Array.from(document.getElementsByClassName('collapse'))
            .filter(element => element.getElementsByClassName('badge').length > 0);
        expandButton = document.getElementById("expandButton");
        expandButton.classList.remove("d-none");
        expandButton.classList.add("d-block");
        expandButton.onclick = expandCollapseAll;

        // We initialize all badges to display the vote's date in the user's locale.
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
        for (const popoverTriggerEl of popoverTriggerList) {
            popoverTriggerEl.dataset.bsContent = new Date(popoverTriggerEl.dataset.bsContent).toLocaleString();
            new bootstrap.Popover(popoverTriggerEl, {trigger: "focus"});
        }
    }

    Telegram.WebApp.expand();
});

/**
 * Expands or collapses all elements, depending on the current state.
 */
function expandCollapseAll() {
    const collapse = expandButton.textContent === "Expand all";
    if (collapse) {
        expandButton.textContent = "Collapse all";
    } else {
        expandButton.textContent = "Expand all";
    }

    // When expanding all elements, we want to allow expanding multiple accordions per group.
    // Therefore, we remove the data-bs-parent attribute first.
    // Then, we can actually expand or collapse all elements.
    for (const element of collapseElements) {
        // NOTE: The bootstrap.Collapse element must be constructed *after* bsParent has been modified.
        if (collapse) {
            delete element.dataset.bsParent;
            new bootstrap.Collapse(element, {toggle: false}).show();
        } else {
            element.dataset.bsParent = element.dataset.parent;
            new bootstrap.Collapse(element, {toggle: false}).hide();
        }
    }
}

/**
 * Closes the webapp and allows the user to share the poll with a chat.
 */
function shareResults() {
    const pollId = document.getElementById("pollId").value;
    // We prefer sharing the results via inline query, but if that's not possible, we fall back to sharing the link.
    if (Telegram.WebApp.isVersionAtLeast("6.7")) {
        Telegram.WebApp.switchInlineQuery(pollId, ["users", "groups", "channels"]);
    } else {const pollId = document.getElementById("pollId").value;
        const botUsername = document.getElementById("botUsername").value;
        const resultsUrl = encodeURIComponent(`https://t.me/${botUsername}/results?startapp=${pollId}`);
        Telegram.WebApp.openTelegramLink(`https://t.me/share/url?url=${resultsUrl}`);
    }
}


/**
 * Asks the user if they really want to delete the poll and calls deletePoll if they confirm.
 */
function askDeletePoll() {
    runOnVersion('6.1', () => Telegram.WebApp.HapticFeedback.notificationOccurred("warning"));
    const confirmText = "Are you sure you want to delete this poll and all of its responses? This cannot be undone!";
    runOnVersion('6.2', () => Telegram.WebApp.showPopup({
        title: "Delete poll?",
        message: confirmText,
        buttons: [
            {id: "ok", type: "destructive", text: "Delete Poll"},
            {id: "cancel", type: "cancel"},
        ]
    }, (id) => deletePoll(id === "ok")),
        // On older versions, we use the browser's confirm dialog.
        () => deletePoll(confirm(confirmText)));
}

/**
 * Deletes the poll if the user confirmed the deletion.
 * @param okay Whether the user confirmed the deletion.
 */
async function deletePoll(okay) {
    if (!okay) {
        return;
    }

    Telegram.WebApp.MainButton.showProgress();
    const pollId = document.getElementById("pollId").value;
    const response = await fetch("/poll", {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            pollId: pollId,
            initData: Telegram.WebApp.initData,
        })
    });
    Telegram.WebApp.MainButton.hideProgress();
    if (!response.ok) {
        const text = await response.text();
        runOnVersion('6.1', () => Telegram.WebApp.HapticFeedback.notificationOccurred("error"));
        showAlert("An error occurred while deleting the poll: " + text, Telegram.WebApp.close);
    } else {
        runOnVersion('6.1', () => Telegram.WebApp.HapticFeedback.notificationOccurred("success"));
        Telegram.WebApp.close();
    }
}
