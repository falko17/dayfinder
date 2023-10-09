// Link to the results page. Will be set by the server.
let resultsLink;

window.addEventListener('load', function () {
    // We want to display all dates in the user's locale.
    replaceDateElements();

    Telegram.WebApp.enableClosingConfirmation();

    loadExistingVote().then(() => {});  // then-clause exists only to avoid warning about unresolved promise.
});

/**
 * Loads an existing vote from the server and displays it, if it exists.
 */
async function loadExistingVote() {
    // If a vote already exists, we want to load it so the user can edit the vote.
    const response = await fetch("/poll?" + Telegram.WebApp.initData);
    if (!response.ok) {
        const text = await response.text();
        Telegram.WebApp.showAlert("An error occurred while loading your vote: " + text, Telegram.WebApp.close);
        return;
    }

    const data = await response.json();
    resultsLink = data["results"];
    const vote = data["votes"];
    let buttonTitle;
    if (vote === null || Object.keys(vote).length === 0) {
        buttonTitle = "Confirm vote";
    } else {
        buttonTitle = "Edit vote";
        // We need to display a warning that the user has already voted, along with the option to view the results.
        document.getElementById("alreadyVoted").style.display = "block";
        document.getElementById("viewResults").addEventListener("click", () => leave(true));
        for (const dayElement of document.getElementsByClassName("day-item")) {
            const optionsName = "options-" + dayElement.dataset.day;
            const selectedOption = dayElement.querySelector(`input[name="${optionsName}"][data-choice="${vote[dayElement.dataset.day]}"]`);
            // Should be true due to form validation.
            selectedOption.checked = true;
        }
    }

    Telegram.WebApp.MainButton.setText(buttonTitle).show().onClick(confirmVote);
}

/**
 * Validates the form. This may display feedback messages to the user.
 * @returns {boolean} Whether the form is valid.
 */
function validateForm() {
    const voteForm = document.getElementById("voteForm");
    if (!voteForm.classList.contains("was-validated")) {
        voteForm.classList.add("was-validated");
    }
    return voteForm.checkValidity();
}

/**
 * Validates the form and sends the vote to the server.
 */
function confirmVote() {
    if (validateForm()) {
        // Since users can edit their votes, we do not need to ask for confirmation.
        saveVote().then(() => {});  // then-clause exists only to avoid warning about unresolved promise.
    }
}

/**
 * Sends the vote to the server, and asks the user whether they want to view the results afterwards.
 */
async function saveVote() {
    const days = {};
    for (const dayElement of document.getElementsByClassName("day-item")) {
        const optionsName = "options-" + dayElement.dataset.day;
        const selectedOption = dayElement.querySelector(`input[name="${optionsName}"]:checked`);
        // Should be true due to form validation.
        console.assert(selectedOption !== null, "No option selected for day " + dayElement.dataset.day);
        days[dayElement.dataset.day] = selectedOption.dataset.choice;
    }

    Telegram.WebApp.MainButton.showProgress();

    try {
        const response = await fetch("/poll", {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                days: days,
                initData: Telegram.WebApp.initData,
            })
        });
        if (!response.ok) {
            const text = await response.text();
            Telegram.WebApp.showAlert("An error occurred while sending your vote: " + text, Telegram.WebApp.close);
        } else {
            Telegram.WebApp.showPopup({
                title: "Vote sent",
                message: "Your vote has been sent. Do you want to view the results now?",
                buttons: [
                    {
                        id: "viewResults",
                        text: "View results",
                        type: "default",
                    },
                    {
                        id: "close",
                        type: "close",
                    }
                ]
            }, id => leave(id === "viewResults"));
        }
    } catch (e) {
        console.error(e);
        Telegram.WebApp.showAlert("An error occurred while sending your vote: " + e);
    } finally {
        Telegram.WebApp.MainButton.hideProgress();
    }
}

/**
 * Leaves the web app. If viewResults is true, the user will be redirected to the results page.
 * @param viewResults Whether the user should be redirected to the results page.
 */
function leave(viewResults) {
    if (viewResults && resultsLink !== undefined) {
        Telegram.WebApp.openTelegramLink(resultsLink);
    } else {
        Telegram.WebApp.close();
    }
}