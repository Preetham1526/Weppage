// client-side JavaScript (e.g., in your home.html or a separate script file)

document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");
  const logoutBtn = document.getElementById("logoutBtn");
  const loginError = document.getElementById("loginError");
  const signupError = document.getElementById("signupError");
  const welcomeMessage = document.getElementById("welcomeMessage");
  const authButtons = document.getElementById("authButtons");
  const userContent = document.getElementById("userContent");

  function updateAuthDisplay() {
    fetch("/user-session")
      .then((response) => response.json())
      .then((data) => {
        if (data.userId) {
          authButtons.style.display = "none";
          logoutBtn.style.display = "block";
          welcomeMessage.textContent = `Welcome, User ID: ${data.userId}`;
          userContent.style.display = "block";
        } else {
          authButtons.style.display = "block";
          logoutBtn.style.display = "none";
          welcomeMessage.textContent = "Welcome, Guest";
          userContent.style.display = "none";
        }
      })
      .catch((error) => {
        console.error("Session check error:", error);
      });
  }

  updateAuthDisplay(); // Initial check on page load

  if (loginForm) {
    loginForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const email = document.getElementById("loginEmail").value;
      const password = document.getElementById("loginPassword").value;

      fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            updateAuthDisplay();
          } else {
            loginError.textContent = data.message;
          }
        })
        .catch((error) => {
          console.error("Login error:", error);
          loginError.textContent = "An error occurred during login.";
        });
    });
  }
  //Example login function.
  function login(userId) {
    localStorage.setItem("loggedInUser", userId);
    updateAuthDisplay();
  }

  //Example signup function.
  function signup(userId) {
    localStorage.setItem("loggedInUser", userId);
    updateAuthDisplay();
  }

  if (signupForm) {
    signupForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const firstName = document.getElementById("firstName").value;
      const lastName = document.getElementById("lastName").value;
      const email = document.getElementById("signupEmail").value;
      const password = document.getElementById("signupPassword").value;
      const confirmPassword = document.getElementById("confirmPassword").value;
      const countryCode = document.getElementById("countryCode").value;
      const contact = document.getElementById("contact").value;
      const gender = document.getElementById("gender").value;

      fetch("/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email: email,
          password: password,
          confirm_password: confirmPassword,
          country_code: countryCode,
          contact: contact,
          gender: gender,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            updateAuthDisplay();
          } else {
            signupError.textContent = data.message;
          }
        })
        .catch((error) => {
          console.error("Signup error:", error);
          signupError.textContent = "An error occurred during signup.";
        });
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", function () {
      fetch("/logout")
        .then(() => {
          updateAuthDisplay();
        })
        .catch((error) => {
          console.error("Logout error:", error);
        });
    });
  }
});
