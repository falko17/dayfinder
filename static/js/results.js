Telegram.WebApp.MainButton.setText('Share with chat').show().onClick(share);

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
        deleteButton.style.display = "block";
        deleteButton.onclick = askDeletePoll;
    }

    // We only want non-empty groups to be expandable.
    collapseElements = Array.from(document.getElementsByClassName('collapse'))
        .filter(element => element.getElementsByClassName('badge').length > 0);
    expandButton = document.getElementById("expandButton");
    expandButton.onclick = expandCollapseAll;

    // We initialize all badges to display the vote's date in the user's locale.
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
    for (const popoverTriggerEl of popoverTriggerList) {
        popoverTriggerEl.dataset.bsContent = new Date(popoverTriggerEl.dataset.bsContent).toLocaleString();
        new bootstrap.Popover(popoverTriggerEl, {trigger: "focus",});
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
function share() {
    const pollId = document.getElementById("pollId").value;
    Telegram.WebApp.switchInlineQuery(pollId, ["users", "groups", "channels"]);
}

/**
 * Asks the user if they really want to delete the poll and calls deletePoll if they confirm.
 */
function askDeletePoll() {
    Telegram.WebApp.showPopup({
        title: "Delete poll?",
        message: "Are you sure you want to delete this poll and all of its responses? This cannot be undone!",
        buttons: [
            {id: "ok", type: "destructive", text: "Delete Poll"},
            {id: "cancel", type: "cancel"},
        ]
    }, (id) => deletePoll(id === "ok"));
}

/**
 * Deletes the poll if the user confirmed the deletion.
 * @param okay Whether the user confirmed the deletion.
 */
async function deletePoll(okay) {
    if (!okay) {
        return;
    }

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
    if (!response.ok) {
        const text = await response.text();
        Telegram.WebApp.showAlert("An error occurred while deleting the poll: " + text, Telegram.WebApp.close);
    } else {
        Telegram.WebApp.close();
    }
}