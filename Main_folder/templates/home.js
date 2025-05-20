document.addEventListener("DOMContentLoaded", function () {
  const loginBtn = document.getElementById("loginBtn");
  const signupBtn = document.getElementById("signupBtn");
  const logoutBtn = document.getElementById("logoutBtn");
  const usernameEl = document.getElementById("username-display");
  const userEmailEl = document.getElementById("user-email");
  const userPhoneEl = document.getElementById("user-phone");

  // Check user session from backend
  fetch("/user-session")
    .then((res) => res.json())
    .then((data) => {
      if (!data.userId) {
        window.location.href = "/login";
        return;
      }

      // Fetch full user info
      fetch(`/profile/${data.userId}`)
        .then((res) => res.json())
        .then((user) => {
          if (usernameEl)
            usernameEl.textContent = user.firstname || user.email.split("@")[0];
          if (userEmailEl) userEmailEl.textContent = user.email;
          if (userPhoneEl) userPhoneEl.textContent = user.phone;

          // Toggle buttons visibility
          if (loginBtn) loginBtn.style.display = "none";
          if (signupBtn) signupBtn.style.display = "none";
          if (logoutBtn) logoutBtn.style.display = "block";
        });
    });

  // Logout
  if (logoutBtn) {
    logoutBtn.addEventListener("click", function () {
      fetch("/logout").then(() => {
        window.location.href = "/login";
      });
    });
  }

  // Dynamic page loading from sidebar
  const sidebarLinks = document.querySelectorAll(".sidebar a[data-page]");
  const pageContent = document.getElementById("pageContent");

  if (sidebarLinks.length && pageContent) {
    sidebarLinks.forEach((link) => {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        const page = this.getAttribute("data-page");

        fetch(page)
          .then((res) => res.text())
          .then((html) => {
            pageContent.innerHTML = html;
          })
          .catch((err) => {
            pageContent.innerHTML = `<p>Error loading page: ${err.message}</p>`;
          });
      });

      if (link === sidebarLinks[0]) link.click(); // Auto-load first
    });
  }
});
