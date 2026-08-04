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
  var ENDPOINT_PLACEHOLDER = "TODO_FORM_ENDPOINT";

  /* ---------------------------------------------------------------- menu -- */

  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("nav");

  if (toggle && nav) {
    var isMobile = function () {
      return window.matchMedia("(max-width: " + BREAKPOINT + "px)").matches;
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
    window.addEventListener("resize", sync);

    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    // Clicar num link fecha o menu (é uma página só, tudo é âncora).
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a") && isMobile()) setOpen(false);
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
            "This form is not connected to a mail service yet. Your message has been " +
            "put into an e-mail — just hit send.",
          sent: "Thank you. We will get back to you shortly.",
          failed: "We could not send it. Please e-mail certek@certek.com.br directly.",
          subject: "Enquiry from the website"
        }
      : {
          missing: "Preencha nome, e-mail e uma breve descrição.",
          noEndpoint:
            "O formulário ainda não está ligado a um serviço de envio. Sua mensagem " +
            "foi colocada num e-mail — é só enviar.",
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
