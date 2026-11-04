(function () {
  function togglePassword(button) {
    var targetId = button.getAttribute("data-target");
    var input = document.getElementById(targetId);
    if (!input) return;
    var showing = input.type === "text";
    input.type = showing ? "password" : "text";
    button.setAttribute("aria-pressed", showing ? "false" : "true");
    button.textContent = showing ? "Show" : "Hide";
  }

  function scorePassword(value) {
    var score = 0;
    if (!value) return 0;
    if (value.length >= 10) score += 1;
    if (value.length >= 14) score += 1;
    if (/[a-z]/.test(value) && /[A-Z]/.test(value)) score += 1;
    if (/\d/.test(value)) score += 1;
    if (/[^A-Za-z0-9]/.test(value)) score += 1;
    return Math.min(score, 4);
  }

  function updateStrength(input, meter, label) {
    var score = scorePassword(input.value);
    var labels = ["Too weak", "Weak", "Fair", "Strong", "Excellent"];
    meter.setAttribute("data-score", String(score));
    meter.style.setProperty("--strength", String((score / 4) * 100) + "%");
    label.textContent = input.value ? labels[score] : "Enter a password";
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-password-toggle]");
    if (button) {
      event.preventDefault();
      togglePassword(button);
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    var password = document.getElementById("id_password");
    var meter = document.getElementById("password-strength-meter");
    var label = document.getElementById("password-strength-label");
    if (password && meter && label) {
      updateStrength(password, meter, label);
      password.addEventListener("input", function () {
        updateStrength(password, meter, label);
      });
    }
  });
})();
