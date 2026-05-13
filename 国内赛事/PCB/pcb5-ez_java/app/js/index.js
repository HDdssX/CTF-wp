// å¨æèæ¯æ°æ³¡çæ
const colors = ['#ffffff', '#c3ecff', '#90f7ec', '#a0eaff'];
const numBubbles = 30;

for (let i = 0; i < numBubbles; i++) {
    const bubble = document.createElement('div');
    bubble.classList.add('bubble');
    const size = Math.random() * 20 + 10;
    bubble.style.width = size + 'px';
    bubble.style.height = size + 'px';
    bubble.style.left = Math.random() * window.innerWidth + 'px';
    bubble.style.background = colors[Math.floor(Math.random() * colors.length)];
    bubble.style.animationDuration = (Math.random() * 10 + 10) + 's';
    bubble.style.animationDelay = Math.random() * 5 + 's';
    document.body.appendChild(bubble);
}

// ç»å½è¡¨åæäº¤ç¤ºä¾ï¼AJAXï¼
document.getElementById("loginForm").addEventListener("submit", async function(e){
    e.preventDefault();
    const form = e.target;
    const data = new URLSearchParams(new FormData(form));
    try {
        const res = await fetch("login", {
            method: "POST",
            body: data
        });
        if (res.redirected) {
            window.location.href = res.url;
        } else {
            document.getElementById("errorMsg").innerText = await res.text();
        }
    } catch (err) {
        document.getElementById("errorMsg").innerText = "Server error!";
    }
});

// å¨æçææ°æ³¡èæ¯
document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("bubbleContainer");

    for (let i = 0; i < 25; i++) {
        let bubble = document.createElement("div");
        bubble.classList.add("bubble");

        let size = Math.random() * 60 + 20;
        bubble.style.width = size + "px";
        bubble.style.height = size + "px";

        bubble.style.left = Math.random() * 100 + "vw";
        bubble.style.animationDuration = 10 + Math.random() * 10 + "s";
        bubble.style.animationDelay = Math.random() * 5 + "s";
        bubble.style.opacity = Math.random() * 0.4 + 0.3;

        container.appendChild(bubble);
    }
});


window.onload = function () {
    const infoMsg = document.getElementById("infoMsg");
    const errorMsg = document.getElementById("errorMsg");

    // å¦ææ¥èª registerServlet ç ?register=success
    const params = new URLSearchParams(window.location.search);
    if (params.get("register") === "success") {
        infoMsg.innerHTML = "Register success! Please login.";
        infoMsg.style.color = "green";
    }

    // å¦æç»å½å¤±è´¥ï¼?error=1ï¼
    if (params.get("error") === "1") {
        errorMsg.textContent = "Wrong username or password.";
    }
};
