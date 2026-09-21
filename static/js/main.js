/* =========================================
   FoodLoop – Main JavaScript
   ========================================= */

// ── Navbar scroll effect ──
const navbar = document.querySelector(".navbar");
if (navbar) {
  window.addEventListener("scroll", () => {
    navbar.classList.toggle("scrolled", window.scrollY > 20);
  });
}

// ── Mobile hamburger menu ──
const hamburger = document.querySelector(".hamburger");
const mobileNav = document.querySelector(".mobile-nav");
if (hamburger && mobileNav) {
  hamburger.addEventListener("click", () => {
    mobileNav.classList.toggle("open");
    const spans = hamburger.querySelectorAll("span");
    spans[0].style.transform = mobileNav.classList.contains("open") ? "rotate(45deg) translate(5px,5px)" : "";
    spans[1].style.opacity   = mobileNav.classList.contains("open") ? "0" : "";
    spans[2].style.transform = mobileNav.classList.contains("open") ? "rotate(-45deg) translate(5px,-5px)" : "";
  });
}

// ── Sidebar toggle (dashboard) ──
const sidebarToggle = document.querySelector(".sidebar-toggle");
const sidebar       = document.querySelector(".sidebar");
const overlay       = document.querySelector(".sidebar-overlay");
if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  if (overlay) overlay.addEventListener("click", () => sidebar.classList.remove("open"));
}

// ── Active nav link highlight ──
document.querySelectorAll(".sidebar-nav a").forEach(link => {
  link.addEventListener("click", function () {
    document.querySelectorAll(".sidebar-nav a").forEach(l => l.classList.remove("active"));
    this.classList.add("active");
  });
});

// ── Role option selection (register page) ──
document.querySelectorAll(".role-option").forEach(opt => {
  opt.addEventListener("click", function () {
    document.querySelectorAll(".role-option").forEach(o => o.classList.remove("selected"));
    this.classList.add("selected");
    const radio = this.querySelector("input[type=radio]");
    if (radio) radio.checked = true;
  });
});

// ── Toast notification system ──
function showToast(type, title, message, duration = 4000) {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const icons = { success: "✅", error: "❌", warning: "⚠️", info: "ℹ️" };
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || "ℹ️"}</span>
    <div class="toast-text">
      <div class="t-title">${title}</div>
      <div class="t-msg">${message}</div>
    </div>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all .3s ease";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Modal system ──
function openModal(id)  { const m = document.getElementById(id); if (m) m.classList.add("active"); }
function closeModal(id) { const m = document.getElementById(id); if (m) m.classList.remove("active"); }

document.querySelectorAll("[data-modal-open]").forEach(btn => {
  btn.addEventListener("click", () => openModal(btn.dataset.modalOpen));
});
document.querySelectorAll("[data-modal-close]").forEach(btn => {
  btn.addEventListener("click", () => closeModal(btn.dataset.modalClose));
});
document.querySelectorAll(".modal-overlay").forEach(overlay => {
  overlay.addEventListener("click", function (e) {
    if (e.target === this) this.classList.remove("active");
  });
});

// ── Counter animation ──
function animateCounter(el) {
  const target = parseFloat(el.dataset.target || el.textContent.replace(/[^0-9.]/g, ""));
  const suffix = el.dataset.suffix || el.textContent.replace(/[0-9.]/g, "");
  const duration = 1500;
  const step = target / (duration / 16);
  let current = 0;
  const timer = setInterval(() => {
    current += step;
    if (current >= target) { current = target; clearInterval(timer); }
    el.textContent = Number.isInteger(target) ? Math.round(current) + suffix : current.toFixed(1) + suffix;
  }, 16);
}

// ── Intersection observer for counters ──
const counters = document.querySelectorAll("[data-counter]");
if (counters.length > 0) {
  const io = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  counters.forEach(el => io.observe(el));
}

// ── Animate on scroll ──
const animateEls = document.querySelectorAll(".card, .step-card, .feature-card, .team-card, .stat-card, .role-card");
if (animateEls.length > 0) {
  animateEls.forEach(el => {
    el.style.opacity = "0";
    el.style.transform = "translateY(24px)";
    el.style.transition = "opacity .5s ease, transform .5s ease";
  });
  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
        }, 80);
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  animateEls.forEach(el => revealObserver.observe(el));
}

// ── Form validation helper ──
function validateForm(formEl) {
  let valid = true;
  formEl.querySelectorAll("[required]").forEach(field => {
    const group = field.closest(".form-group");
    if (!field.value.trim()) {
      valid = false;
      field.style.borderColor = "var(--danger)";
      if (group && !group.querySelector(".err-msg")) {
        const msg = document.createElement("span");
        msg.className = "err-msg";
        msg.style.cssText = "color:var(--danger);font-size:.78rem;margin-top:4px;display:block;";
        msg.textContent = "This field is required";
        group.appendChild(msg);
      }
    } else {
      field.style.borderColor = "";
      const old = group && group.querySelector(".err-msg");
      if (old) old.remove();
    }
  });
  return valid;
}

// ── Login form ──
const loginForm = document.getElementById("loginForm");
if (loginForm) {
  loginForm.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!validateForm(this)) return;
    const role    = document.getElementById("loginRole")?.value || "business";
    const loading = document.getElementById("loginBtn");
    if (loading) { loading.textContent = "Signing in…"; loading.disabled = true; }
    setTimeout(() => {
      const pages = {
        business:  "dashboard-business.html",
        ngo:       "dashboard-ngo.html",
        customer:  "dashboard-customer.html",
        volunteer: "dashboard-volunteer.html",
        admin:     "dashboard-admin.html"
      };
      window.location.href = pages[role] || "dashboard-business.html";
    }, 1200);
  });
}

// ── Register form ──
const registerForm = document.getElementById("registerForm");
if (registerForm) {
  registerForm.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!validateForm(this)) return;
    showToast("success", "Account Created!", "Redirecting to login…");
    setTimeout(() => { window.location.href = "login.html"; }, 2000);
  });
}

// ── Food listing form (dashboard) ──
const foodForm = document.getElementById("foodForm");
if (foodForm) {
  foodForm.addEventListener("submit", function (e) {
    e.preventDefault();
    closeModal("addFoodModal");
    showToast("success", "Food Listed!", "Your surplus food has been added successfully.");
    const tbody = document.querySelector("#foodTable tbody");
    if (tbody) {
      const name     = document.getElementById("foodName")?.value || "New Item";
      const qty      = document.getElementById("foodQty")?.value  || "0";
      const unit     = document.getElementById("foodUnit")?.value  || "kg";
      const dest     = document.getElementById("foodDest")?.value  || "DONATE";
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="food-name">${name}</td>
        <td>${qty} ${unit}</td>
        <td><span class="badge badge-warning">${dest}</span></td>
        <td><span class="badge badge-info">Pending</span></td>
        <td><button class="btn btn-sm btn-outline" onclick="showToast('info','Details','Feature coming soon.')">View</button></td>`;
      tbody.prepend(tr);
      this.reset();
    }
  });
}

// ── Progress bar animate on load ──
window.addEventListener("load", () => {
  document.querySelectorAll(".progress-bar[data-width]").forEach(bar => {
    bar.style.width = "0%";
    setTimeout(() => { bar.style.width = bar.dataset.width; }, 300);
  });
});

// ── Tab switching (dashboard tabs) ──
document.querySelectorAll("[data-tab]").forEach(btn => {
  btn.addEventListener("click", function () {
    const group = this.dataset.tabGroup;
    document.querySelectorAll(`[data-tab][data-tab-group="${group}"]`).forEach(b => b.classList.remove("active"));
    document.querySelectorAll(`[data-tab-content][data-tab-group="${group}"]`).forEach(c => c.classList.add("hidden"));
    this.classList.add("active");
    const content = document.querySelector(`[data-tab-content="${this.dataset.tab}"][data-tab-group="${group}"]`);
    if (content) content.classList.remove("hidden");
  });
});

console.log("🍃 FoodLoop JS loaded – Group 17, LJ University");
