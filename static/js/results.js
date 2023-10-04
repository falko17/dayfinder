Telegram.WebApp.MainButton.setText('Share with chat').show().onClick(share);

window.addEventListener('load', function () {
    // We want to display all dates in the user's locale.
    replaceDateElements();

    const ownerId = Number(document.getElementById("ownerId").value);
    // It's fine to use the unsafe version of initData here – the server will validate the ID on deletion.
    if (Object.keys(Telegram.WebApp.initDataUnsafe).length > 0 && Telegram.WebApp.initDataUnsafe.user.id === ownerId) {
        const deleteButton = document.getElementById("deleteButton");
        deleteButton.style.display = "block";
        deleteButton.onclick = askDeletePoll;
    }

    Telegram.WebApp.expand();
});

/**
 * Closes the webapp and allows the user to share the poll with a chat.
 */
function share() {
    const pollId = document.getElementById("pollId").value;
    Telegram.WebApp.switchInlineQuery(pollId, ["users", "groups", "channels"]);
}

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