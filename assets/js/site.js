/* Certek — comportamento da página.
 *
 * Quatro coisas apenas:
 *   1. menu mobile
 *   2. animação de entrada das seções
 *   3. fallback do formulário enquanto não existe endpoint
 *   4. filtro por segmento e caixa de detalhes das obras
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

  /* -------------------------------------------- obras: filtro e detalhes -- */

  var workCards = Array.prototype.slice.call(document.querySelectorAll(".works .work"));

  // Filtro por segmento. A barra nasce com hidden no HTML: sem JS ela não
  // aparece e todas as obras ficam visíveis — nada depende daqui para existir.
  var worksFilter = document.querySelector("[data-works-filter]");

  if (worksFilter && workCards.length) {
    worksFilter.hidden = false;

    worksFilter.addEventListener("click", function (event) {
      var botao = event.target.closest("[data-filter]");
      if (!botao) return;
      var filtro = botao.getAttribute("data-filter");

      Array.prototype.forEach.call(
        worksFilter.querySelectorAll("[data-filter]"),
        function (b) {
          b.setAttribute("aria-pressed", String(b === botao));
        }
      );

      workCards.forEach(function (card) {
        var segmentos = (card.getAttribute("data-segments") || "").split(/\s+/);
        card.hidden = filtro !== "all" && segmentos.indexOf(filtro) === -1;
      });
    });
  }

  // Caixa de detalhes. O conteúdo vem do próprio card (sector, título, texto)
  // mais as fotos listadas em data-gallery; o <dialog> cuida de foco e Esc.
  var workModal = document.getElementById("work-modal");

  if (workModal && typeof workModal.showModal === "function" && workCards.length) {
    var modalSector = document.getElementById("work-modal-sector");
    var modalTitle = document.getElementById("work-modal-title");
    var modalText = document.getElementById("work-modal-text");
    var modalGallery = document.getElementById("work-modal-gallery");
    var modalMeta = document.getElementById("work-modal-meta");

    var abreDetalhes = function (card) {
      var sector = card.querySelector(".work__sector");
      var titulo = card.querySelector("h3");
      var meta = card.querySelector(".work__meta");
      var texto = card.querySelector(".work__body p:not(.work__sector):not(.work__meta)");
      modalSector.textContent = sector ? sector.textContent : "";
      modalTitle.textContent = titulo ? titulo.textContent : "";
      modalText.textContent = texto ? texto.textContent : "";

      // Ficha técnica (cidade/UF · m²): nem todo card tem, e o parágrafo pode
      // nem existir no HTML. Nos dois casos não sobra o texto da obra anterior.
      if (modalMeta) {
        modalMeta.textContent = meta ? meta.textContent.trim() : "";
        modalMeta.hidden = !meta;
      }

      modalGallery.textContent = "";
      (card.getAttribute("data-gallery") || "").split(",").forEach(function (caminho) {
        caminho = caminho.trim();
        if (!caminho) return;
        var img = document.createElement("img");
        img.src = caminho;
        // decorativas: a informação (título, setor, descrição) já está no texto
        img.alt = "";
        img.loading = "lazy";
        img.decoding = "async";
        modalGallery.appendChild(img);
      });

      workModal.showModal();
    };

    // Trava a rolagem do fundo enquanto a caixa está aberta. Observar o
    // atributo open (em vez do evento "close") cobre qualquer forma de
    // fechar — X, backdrop, Esc ou close() — mesmo onde o evento não chega.
    new MutationObserver(function () {
      document.body.style.overflow = workModal.open ? "hidden" : "";
    }).observe(workModal, { attributes: true, attributeFilter: ["open"] });

    workCards.forEach(function (card) {
      var botao = card.querySelector("[data-work-more]");
      if (!botao) return;
      botao.hidden = false;
      botao.addEventListener("click", function () {
        abreDetalhes(card);
      });
    });

    workModal.addEventListener("click", function (event) {
      // clique no backdrop (o alvo é o próprio dialog), no X, ou num link
      // interno (ex.: "fale com a Certek" leva ao contato) — tudo fecha
      if (
        event.target === workModal ||
        event.target.closest("[data-modal-close]") ||
        event.target.closest("a")
      ) {
        workModal.close();
      }
    });
  }
})();
