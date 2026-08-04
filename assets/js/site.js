/* Certek — comportamento da página.
 *
 * Três coisas apenas:
 *   1. menu mobile
 *   2. animação de entrada das seções
 *   3. fallback do formulário enquanto não existe endpoint
 *
 * Tudo aqui é progressivo: com JS desativado a página continua completa e
 * navegável, e os canais de contato diretos continuam clicáveis.
 */
(function () {
  "use strict";

  var BREAKPOINT = 900;
  var mq = window.matchMedia("(max-width: " + BREAKPOINT + "px)");
  var ENDPOINT_PLACEHOLDER = "TODO_FORM_ENDPOINT";

  /* ---------------------------------------------------------------- menu -- */

  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("nav");

  if (toggle && nav) {
    var isMobile = function () {
      return mq.matches;
    };

    var setOpen = function (open) {
      toggle.setAttribute("aria-expanded", String(open));
      nav.hidden = !open;
    };

    // Estado inicial: no mobile começa fechado; no desktop o nav é sempre visível.
    var sync = function () {
      if (isMobile()) {
        setOpen(toggle.getAttribute("aria-expanded") === "true" && !nav.hidden);
        if (toggle.getAttribute("aria-expanded") !== "true") setOpen(false);
      } else {
        toggle.setAttribute("aria-expanded", "false");
        nav.hidden = false;
      }
    };
    sync();
    // Só ao cruzar o breakpoint — não a cada frame de resize.
    if (mq.addEventListener) {
      mq.addEventListener("change", sync);
    } else {
      mq.addListener(sync);
    }

    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    // Clicar num link fecha o menu (é uma página só, tudo é âncora).
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a") && isMobile()) setOpen(false);
    });

    // Tocar fora fecha o menu.
    document.addEventListener("click", function (event) {
      if (!isMobile()) return;
      if (event.target.closest(".nav") || event.target.closest(".nav-toggle")) return;
      if (toggle.getAttribute("aria-expanded") === "true") setOpen(false);
    });

    // Esc fecha e devolve o foco ao botão.
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  /* ------------------------------------------------------------- reveal -- */

  var reveals = document.querySelectorAll("[data-reveal]");
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (reveals.length && !reduced && "IntersectionObserver" in window) {
    // A classe só entra agora: sem JS, o CSS de reveal nunca se aplica e nada
    // fica preso em opacity 0.
    document.documentElement.classList.add("js-reveal");

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -5% 0px", threshold: 0.02 }
    );

    Array.prototype.forEach.call(reveals, function (el, i) {
      el.style.transitionDelay = (i % 4) * 60 + "ms";
      observer.observe(el);
    });
  }

  /* --------------------------------------------------------------- form -- */

  var form = document.getElementById("contact-form");
  var status = document.getElementById("form-status");

  if (form && status) {
    var t = document.documentElement.lang.indexOf("en") === 0
      ? {
          missing: "Please fill in your name, e-mail and a short description.",
          noEndpoint:
            "We've opened an email with your message. If nothing opened, write to " +
            "certek@certek.com.br directly.",
          sent: "Thank you. We will get back to you shortly.",
          failed: "We could not send it. Please e-mail certek@certek.com.br directly.",
          subject: "Enquiry from the website"
        }
      : {
          missing: "Preencha nome, e-mail e uma breve descrição.",
          noEndpoint:
            "Abrimos um e-mail com a sua mensagem. Se nada abrir, escreva direto " +
            "para certek@certek.com.br.",
          sent: "Obrigado. Retornaremos em breve.",
          failed: "Não foi possível enviar. Escreva direto para certek@certek.com.br.",
          subject: "Contato pelo site"
        };

    var say = function (text, state) {
      status.textContent = text;
      if (state) {
        status.setAttribute("data-state", state);
      } else {
        status.removeAttribute("data-state");
      }
    };

    form.addEventListener("submit", function (event) {
      var data = new FormData(form);
      var nome = (data.get("nome") || "").trim();
      var email = (data.get("email") || "").trim();
      var mensagem = (data.get("mensagem") || "").trim();

      if (!nome || !email || !mensagem) {
        event.preventDefault();
        say(t.missing, "error");
        // Aponta o primeiro campo vazio e leva o foco até ele: num viewport de
        // 375px a mensagem de erro fica abaixo do botão, fora da tela.
        var faltando = ["#f-nome", "#f-email", "#f-mensagem"]
          .map(function (sel) { return form.querySelector(sel); })
          .filter(function (el) { return el && !el.value.trim(); })[0];
        if (faltando) {
          faltando.setAttribute("aria-invalid", "true");
          faltando.focus();
          faltando.addEventListener("input", function limpa() {
            faltando.removeAttribute("aria-invalid");
            faltando.removeEventListener("input", limpa);
          });
        }
        return;
      }

      var action = form.getAttribute("action") || "";

      // Sem endpoint configurado: em vez de postar para lugar nenhum e mostrar
      // um "enviado!" mentiroso, montamos um mailto já preenchido.
      if (!action || action === ENDPOINT_PLACEHOLDER) {
        event.preventDefault();
        var corpo =
          nome +
          (data.get("empresa") ? " — " + data.get("empresa") : "") +
          "\n" +
          email +
          "\n\n" +
          mensagem;
        say(t.noEndpoint);
        window.location.href =
          "mailto:certek@certek.com.br?subject=" +
          encodeURIComponent(t.subject) +
          "&body=" +
          encodeURIComponent(corpo);
        return;
      }

      // Com endpoint: envia por fetch para não perder a página.
      event.preventDefault();
      var button = form.querySelector('button[type="submit"]');
      if (button) button.disabled = true;

      fetch(action, { method: "POST", body: data, headers: { Accept: "application/json" } })
        .then(function (response) {
          if (!response.ok) throw new Error(String(response.status));
          form.reset();
          say(t.sent);
        })
        .catch(function () {
          say(t.failed, "error");
        })
        .then(function () {
          if (button) button.disabled = false;
        });
    });
  }
})();
