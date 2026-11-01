// Sugerencias del buscador de exámenes.
// Mientras la enfermera escribe, se piden al servidor los exámenes parecidos
// y se muestran en una lista. Nunca se elige un examen solo: hay que hacer
// clic en la sugerencia, o marcarla con las flechas y presionar Enter.
(function () {
  const campo = document.getElementById("buscador");
  if (!campo) return; // no hay listado cargado

  const lista = document.getElementById("sugerencias");
  const estado = document.getElementById("estado-busqueda");
  const formAgregar = document.getElementById("form-agregar");

  let sugerencias = [];  // lo último que respondió el servidor
  let marcada = -1;      // posición marcada con las flechas (-1 = ninguna)
  let espera = null;     // para no buscar en cada tecla, sino al hacer una pausa

  campo.addEventListener("input", function () {
    clearTimeout(espera);
    espera = setTimeout(pedirSugerencias, 150);
  });

  campo.addEventListener("keydown", function (evento) {
    if (evento.key === "ArrowDown" && sugerencias.length) {
      evento.preventDefault();
      marcar(Math.min(marcada + 1, sugerencias.length - 1));
    } else if (evento.key === "ArrowUp" && sugerencias.length) {
      evento.preventDefault();
      marcar(Math.max(marcada - 1, 0));
    } else if (evento.key === "Enter") {
      evento.preventDefault();
      // Solo se agrega si hay una sugerencia marcada
      if (marcada >= 0) elegir(marcada);
    } else if (evento.key === "Escape") {
      mostrar([]);
    }
  });

  async function pedirSugerencias() {
    const consulta = campo.value.trim();
    if (consulta.replace(/\s/g, "").length < 2) {
      mostrar([]);
      estado.textContent = consulta ? "Escriba al menos 2 letras" : "";
      return;
    }

    estado.textContent = "Buscando…";
    let datos;
    try {
      const respuesta = await fetch(campo.dataset.url + "?q=" + encodeURIComponent(consulta));
      if (!respuesta.ok) throw new Error(respuesta.status);
      datos = await respuesta.json();
    } catch (error) {
      estado.textContent = "No se pudo buscar. Recargue la página e intente de nuevo";
      return;
    }

    // Si mientras tanto se siguió escribiendo, esta respuesta ya no sirve
    if (consulta !== campo.value.trim()) return;

    mostrar(datos);
    estado.textContent = datos.length
      ? "Haga clic en el examen para agregarlo, o use las flechas y Enter"
      : "No se encontraron exámenes parecidos. Revise lo escrito";
  }

  function mostrar(datos) {
    sugerencias = datos;
    marcada = -1;
    lista.innerHTML = "";
    campo.removeAttribute("aria-activedescendant");

    datos.forEach(function (examen, posicion) {
      const item = document.createElement("li");
      item.id = "sugerencia-" + posicion;
      item.className = "sugerencia";
      item.setAttribute("role", "option");
      item.setAttribute("aria-selected", "false");

      // textContent (y no innerHTML) evita que un texto se interprete como código
      const nombre = document.createElement("span");
      nombre.className = "sugerencia-nombre";
      nombre.textContent = examen.nombre;
      item.appendChild(nombre);

      const etiquetas = document.createElement("span");
      etiquetas.className = "sugerencia-etiquetas";
      etiquetas.appendChild(crearEtiqueta(examen.etiqueta.tipo, examen.etiqueta.texto));
      if (examen.ya_seleccionado) {
        etiquetas.appendChild(crearEtiqueta("agregado", "Ya agregado"));
        item.setAttribute("aria-disabled", "true");
        item.classList.add("sugerencia-agregada");
      }
      item.appendChild(etiquetas);

      item.addEventListener("click", function () { elegir(posicion); });
      lista.appendChild(item);
    });

    lista.hidden = datos.length === 0;
    campo.setAttribute("aria-expanded", datos.length ? "true" : "false");
  }

  function crearEtiqueta(tipo, texto) {
    const etiqueta = document.createElement("span");
    etiqueta.className = "etiqueta etiqueta-" + tipo;
    etiqueta.textContent = texto;
    return etiqueta;
  }

  function marcar(posicion) {
    marcada = posicion;
    Array.from(lista.children).forEach(function (item, i) {
      item.classList.toggle("sugerencia-marcada", i === posicion);
      item.setAttribute("aria-selected", i === posicion ? "true" : "false");
    });
    const item = lista.children[posicion];
    campo.setAttribute("aria-activedescendant", item.id);
    item.scrollIntoView({ block: "nearest" });
  }

  function elegir(posicion) {
    const examen = sugerencias[posicion];
    if (!examen || examen.ya_seleccionado) return;
    formAgregar.elements.id.value = examen.id;
    formAgregar.submit();
  }
})();
