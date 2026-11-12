/*
 * Editor de texto formatado do caderno de laboratório (research R1 da feature 008).
 *
 * Cada textarea[data-rich] ganha uma barra e uma área editável; o HTML volta para o textarea a
 * cada alteração e o servidor aplica a lista branca ao gravar. Imagens coladas ou arrastadas são
 * enviadas como anexo da entrada (data-upload-url) e entram no texto pelo endereço devolvido.
 * Sem JavaScript, o textarea continua aceitando texto simples.
 */
(function () {
  "use strict";

  var TABLE_HTML =
    "<table><thead><tr><th>Coluna 1</th><th>Coluna 2</th><th>Coluna 3</th></tr></thead>" +
    "<tbody><tr><td><br></td><td><br></td><td><br></td></tr>" +
    "<tr><td><br></td><td><br></td><td><br></td></tr></tbody></table><p><br></p>";

  var BUTTONS = [
    ["bold", "N", "Negrito"],
    ["italic", "I", "Itálico"],
    ["underline", "S", "Sublinhado"],
    ["superscript", "x²", "Sobrescrito"],
    ["subscript", "x₂", "Subscrito"],
    ["insertUnorderedList", "• Lista", "Lista com marcadores"],
    ["insertOrderedList", "1. Lista", "Lista numerada"],
    ["heading", "Título", "Título de seção"],
    ["paragraph", "Parágrafo", "Texto normal"],
    ["table", "Tabela", "Inserir tabela"],
    ["removeFormat", "Limpar", "Limpar formatação"]
  ];

  function csrfToken(form) {
    var input = form ? form.querySelector("input[name=csrfmiddlewaretoken]") : null;
    return input ? input.value : "";
  }

  function run(command) {
    if (command === "heading") {
      document.execCommand("formatBlock", false, "h3");
    } else if (command === "paragraph") {
      document.execCommand("formatBlock", false, "p");
    } else if (command === "table") {
      document.execCommand("insertHTML", false, TABLE_HTML);
    } else {
      document.execCommand(command, false, null);
    }
  }

  function imageFiles(list) {
    var files = [];
    for (var i = 0; list && i < list.length; i++) {
      if (list[i].type && list[i].type.indexOf("image/") === 0) {
        files.push(list[i]);
      }
    }
    return files;
  }

  function insertImage(area, url, name) {
    var image = document.createElement("img");
    image.src = url;
    image.alt = name || "imagem";
    var selection = window.getSelection();
    if (selection && selection.rangeCount && area.contains(selection.anchorNode)) {
      var range = selection.getRangeAt(0);
      range.deleteContents();
      range.insertNode(image);
      range.setStartAfter(image);
      range.collapse(true);
      selection.removeAllRanges();
      selection.addRange(range);
    } else {
      area.appendChild(image);
    }
  }

  function setup(textarea) {
    var form = textarea.form;
    var uploadUrl = textarea.getAttribute("data-upload-url");
    var wrapper = document.createElement("div");
    wrapper.className = "editor-rico";
    var bar = document.createElement("div");
    bar.className = "editor-barra";
    bar.setAttribute("role", "toolbar");
    var area = document.createElement("div");
    area.className = "editor-area";
    area.contentEditable = "true";
    area.setAttribute("role", "textbox");
    area.setAttribute("aria-multiline", "true");
    var label = textarea.id ? document.querySelector("label[for='" + textarea.id + "']") : null;
    if (label) {
      area.setAttribute("aria-label", label.textContent.trim());
      bar.setAttribute("aria-label", "Formatação de " + label.textContent.trim());
    }
    var status = document.createElement("p");
    status.className = "editor-aviso";
    status.setAttribute("aria-live", "polite");

    BUTTONS.forEach(function (item) {
      var button = document.createElement("button");
      button.type = "button";
      button.textContent = item[1];
      button.title = item[2];
      button.setAttribute("aria-label", item[2]);
      button.addEventListener("mousedown", function (event) {
        event.preventDefault();
      });
      button.addEventListener("click", function () {
        area.focus();
        run(item[0]);
        sync();
      });
      bar.appendChild(button);
    });

    function sync() {
      textarea.value = area.innerHTML;
    }

    function upload(files) {
      if (!uploadUrl) {
        status.textContent = "Imagens só entram pela edição da entrada aberta (como anexo).";
        return;
      }
      files.forEach(function (file) {
        var data = new FormData();
        data.append("arquivo", file, file.name || "imagem-colada.png");
        data.append("no_texto", "1");
        status.textContent = "Enviando a imagem…";
        fetch(uploadUrl, {
          method: "POST",
          body: data,
          credentials: "same-origin",
          headers: { "X-CSRFToken": csrfToken(form), Accept: "application/json" }
        })
          .then(function (response) {
            return response.json().then(function (body) {
              return { ok: response.ok, body: body };
            });
          })
          .then(function (result) {
            if (!result.ok) {
              status.textContent = result.body.erro || "A imagem não foi aceita.";
              return;
            }
            area.focus();
            insertImage(area, result.body.url, result.body.name);
            sync();
            status.textContent = "Imagem anexada (" + result.body.name + "). Grave a entrada.";
          })
          .catch(function () {
            status.textContent = "Falha ao enviar a imagem; tente de novo.";
          });
      });
    }

    area.innerHTML = textarea.value;
    area.addEventListener("input", sync);
    area.addEventListener("blur", sync);
    area.addEventListener("paste", function (event) {
      var files = imageFiles(event.clipboardData ? event.clipboardData.files : null);
      if (files.length) {
        event.preventDefault();
        upload(files);
      }
    });
    area.addEventListener("drop", function (event) {
      var files = imageFiles(event.dataTransfer ? event.dataTransfer.files : null);
      if (files.length) {
        event.preventDefault();
        upload(files);
      }
    });
    if (form) {
      form.addEventListener("submit", sync);
    }

    textarea.hidden = true;
    textarea.removeAttribute("required");
    wrapper.appendChild(bar);
    wrapper.appendChild(area);
    wrapper.appendChild(status);
    textarea.parentNode.insertBefore(wrapper, textarea.nextSibling);
  }

  function init() {
    try {
      document.execCommand("defaultParagraphSeparator", false, "p");
    } catch (error) {
      /* navegador sem suporte: o servidor converte div em parágrafo */
    }
    var fields = document.querySelectorAll("textarea[data-rich]");
    for (var i = 0; i < fields.length; i++) {
      setup(fields[i]);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
