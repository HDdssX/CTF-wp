window.onload = function () {
    const regMsg = document.getElementById("regMsg");

    const params = new URLSearchParams(window.location.search);
    if (params.get("error") === "exists") {
        regMsg.textContent = "Username already exists!";
    } else if (params.get("error") === "invalid") {
        regMsg.textContent = "The server appears to be experiencing an unknown error.";
    } else if (params.get("error") === "empty") {
        regMsg.textContent = "Username or password cannot be empty!";
    }
};