// Set the main button to send the data when clicked.
Telegram.WebApp.MainButton.setText('Create poll').show().onClick(pressCreate);

// Contains the HTML element with the list of days that the user has selected.
let dayList;

// Contains the HTML element of the button to add a new day.
let addDayButton;

// Contains the HTML element of the form.
let createForm;

// Whether the closing confirmation is enabled.
let closingConfirmationEnabled = false;

window.addEventListener('load', function () {
    // Expand the web app to full screen when loaded.
    Telegram.WebApp.expand();
    dayList = document.getElementById("selectedDaysList");
    addDayButton = document.getElementById("addDayButton");
    createForm = document.getElementById("createForm");

    // As soon as a title or description is entered, we want to enable the closing confirmation.
    document.getElementById("eventTitle").addEventListener("input", enableClosingConfirmation);
    document.getElementById("eventDescription").addEventListener("input", enableClosingConfirmation);
});

/**
 * Enables the webapp's closing confirmation (if it is not enabled already).
 */
function enableClosingConfirmation() {
    if (!closingConfirmationEnabled) {
        Telegram.WebApp.enableClosingConfirmation();
        closingConfirmationEnabled = true;
    }
}

/**
 * Shows the datepicker for the given input element.
 * @param inputElement The input element for which the datepicker should be shown.
 */
function showPicker(inputElement) {
    try {
        inputElement.showPicker();
    } catch {
        // showPicker is not completely supported yet by Safari.
        inputElement.click();
    }
}

/**
 * Validates the form. This may cause feedback messages to be shown to the user.
 * @returns {boolean} Whether the form is valid.
 */
function validateForm() {
    let formValid = true;

    // At least two days must be selected.
    addDayButton.classList.remove("is-invalid", "is-valid");
    if (dayList.children.length < 2) {
        addDayButton.classList.add("is-invalid");
        formValid = false;
    } else {
        addDayButton.classList.add("is-valid");
    }

    const existingDates = new Set();
    for (const dayElement of document.getElementsByClassName("day-item")) {
        const dateInput = dayElement.getElementsByTagName("input")[0];
        dateInput.classList.remove("is-invalid", "is-valid");
        if (existingDates.has(dateInput.value)) {
            dateInput.classList.add("is-invalid");
            formValid = false;
        }
        existingDates.add(dateInput.value);
    }

    if (!createForm.classList.contains("was-validated")) {
        createForm.classList.add("was-validated");
    }
    formValid = createForm.checkValidity() && formValid;
    return formValid;

}

/**
 * Validates the form and shows the popup to ask the user whether they want to save the poll.
 */
function pressCreate() {
    if (!validateForm()) {
        return;
    }

    Telegram.WebApp.showConfirm("Do you want to save the poll? You cannot edit it later.", savePoll);
}

/**
 * Sends the data for the newly created poll to the bot and closes the web app.
 * @param okay Whether the user wants to save the poll.
 */
async function savePoll(okay) {
    if (!okay) {
        return;
    }

    Telegram.WebApp.MainButton.showProgress();
    const title = document.getElementById("eventTitle").value;
    const description = document.getElementById("eventDescription").value;
    const notification = document.getElementById("eventNotification").checked;
    const days = Array.from(dayList.children).map(day => day.getElementsByTagName("input")[0].value);

    try {
        const response = await fetch("/poll", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title: title,
                description: description,
                notification: notification,
                days: days,
                initData: Telegram.WebApp.initData,
            })
        });
        if (!response.ok) {
            const text = await response.text();
            Telegram.WebApp.showAlert("An error occurred while sending the poll: " + text, () => Telegram.WebApp.close());
        } else {
            Telegram.WebApp.close();
        }
    } catch (e) {
        console.error(e);
        Telegram.WebApp.MainButton.hideProgress();
        Telegram.WebApp.showAlert("An error occurred while sending the poll: " + e);
    }
}

/**
 * Adds a new day to the list of selected days.
 */
function addDay() {
    // We can remove the validation class because the user has changed the input.
    createForm.classList.remove("was-validated");

    const day = document.createElement("li");
    day.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center", "day-item")
    // We only want dates after today to be selectable, hence, we set the min attribute to today's date.
    const today = new Date().toISOString().split('T')[0];

    day.innerHTML = `
    <label>
        <div class="input-group has-validation">
            <!-- The label is only here for accessibility reasons, thus we hide it by default -->
            <span class="d-none">Date</span>
            <input type="date" value="${today}" min="${today}" required/>
            <div class="invalid-feedback">
                Please enter a date that is unique and after today.
            </div>
        </div>
    </label>
    <button type="button" class="btn-close" aria-label="Delete"></button>`;
    const removeButton = day.getElementsByTagName("button")[0];
    if (Telegram.WebApp.colorScheme === "dark") {
        removeButton.classList.add("btn-close-white");
    }
    removeButton.addEventListener("click", () => removeDay(day));
    // If the value of the input element changes, we want to reorder the day in the list.
    day.getElementsByTagName("input")[0].addEventListener("change", () => reorderDay(day));
    reorderDay(day);  // This also adds the day to the list.
    // The setTimeout is needed to wait until the DOM has been updated.
    setTimeout(() => {
        showPicker(day.getElementsByTagName("input")[0]);
    });
}

/**
 * Reorders the given day in the list of selected days.
 * @param day The day that should be reordered.
 */
function reorderDay(day) {
    // We can remove the validation class because the user has changed the input.
    createForm.classList.remove("was-validated");

    const dayDate = day.getElementsByTagName("input")[0].value;
    // If the value has been removed, we can remove the day from the list.
    if (dayDate === "") {
        removeDay(day);
        return;
    }

    // We want to add the new day before the next-bigger day, hence, we iterate over all days and compare their dates.
    for (let child of dayList.children) {
        // We know the existing list is sorted already because this function adds the days in the correct order.
        // Hence, as soon as we find a day that is bigger than the new day, we insert the new day before it.
        const date = child.getElementsByTagName("input")[0].value;
        if (date > dayDate) {
            dayList.insertBefore(day, child);
            return;
        }
    }
    // If there is no day bigger than the new day, we can put it at the end of the list.
    dayList.appendChild(day);
}

/**
 * Removes the given day from the list of selected days.
 * @param day The day that should be removed.
 */
function removeDay(day) {
    dayList.removeChild(day);
}