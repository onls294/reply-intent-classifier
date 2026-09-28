# Guía de etiquetado — intención de la respuesta

Para etiquetar a mano las respuestas de WhatsApp de [A]: una etiqueta por respuesta,
leída **junto al mensaje de la empresa al que responde**.

**Versión 2 — 27 sep 2026.** Clases aprobadas por Luis el 26 sep. La v2 añade la sección 5
(casos frontera) con los 9 huecos que encontraron los etiquetadores de la v1. Las clases y la
prioridad no cambian. Cambios y hashes: `LABELING_GUIDE_CHANGELOG.md`.

---

## 1 · Qué se etiqueta y qué no

**Unidad:** un mensaje entrante, respuesta a un mensaje automático de uno de cuatro flujos
(`no_contesto`, `volver_llamar`, `seguimiento`, `no_show`), dentro de las 24 h siguientes.

**Deduplicación.** Si el mismo mensaje entrante quedó atribuido a más de un flujo, se
conserva **una sola fila: la del flujo cuyo envío es el más reciente antes de la
respuesta** (menor `hours_since_outbound`). Las demás salen del dataset; la equivalencia
queda en `mapping.local.json` → `duplicados`. En la ventana de agosto: **7 duplicados, de
182 filas a 175 mensajes**. Los 7 se quedaron en `no_contesto`.

**`mensaje_saliente`** es el **último mensaje que la empresa envió a esa persona antes de su
respuesta**, sea la plantilla de la secuencia, un mensaje manual de una vendedora u otro
automático del CRM. No es necesariamente el de la secuencia: cuando hubo otro saliente en
medio, la columna `saliente_intermedio` vale `si`. **Se etiqueta contra ese texto.** Solo
vive en el CSV local, seudonimizado.

**Filtros — la fila se queda en el dataset pero NO se etiqueta:**

| Filtro | Cuándo |
|---|---|
| `respuesta_automatica` | Contestador o mensaje de bienvenida de un negocio: "gracias por comunicarte, en un momento te atiendo", horario de atención, menú. Lo escribió una máquina, no la persona. |
| `sin_texto` | El mensaje no tiene texto: audio, imagen, vídeo. No se puede leer la intención. Se reporta como **límite de cobertura**, con su conteo por tipo. |

---

## 2 · Las clases

| Clase | Criterio |
|---|---|
| `pide_informacion` | Pregunta por el producto, el precio, el método, de qué se trata o dónde están. Si menciona el canal ("por acá"), **el canal es incidental**: lo que pide es información. |
| `quiere_contacto` | Quiere que la llamen o que la contacten: da una hora o un día concretos, pide que la llamen, o reclama que no la han llamado. |
| `prefiere_escrito` | **Rechaza la llamada de forma explícita** ("no puedo recibir llamadas", "no atiendo llamadas") o el mensaje entero es la preferencia de canal ("solo por WhatsApp"). |
| `pospone` | No rechaza la oferta: aplaza la conversación sin fijar momento ("estoy ocupada", "en una reunión", "luego te aviso", "lo consulto con mi esposo"). |
| `no_interesado` | Rechaza la oferta: no le interesa, ya no lo necesita, se le sale del presupuesto, no aplica (no tiene bebé). Incluye "por ahora no", aunque añada "quizás más adelante". |
| `sin_intencion` | No expresa nada accionable: saludo suelto, "ok", "sí" sin contexto, emoji, signo suelto, una explicación de por qué no contestó sin pedir nada. |
| `fuera_de_tema` | El mensaje **no va dirigido a este negocio**: se equivocó de chat, o es otro negocio ofreciendo lo suyo. |

**Marca aparte: `baja_explicita = si`.** Solo en `no_interesado`, cuando **pide
explícitamente** que no la contacten más: que no escriban, que no llamen, que la borren de
la base. Un simple "no, gracias" es `no_interesado` **sin** baja.

---

## 3 · Regla de etiqueta única, con prioridad

**Una sola etiqueta por respuesta.** Cuando un mensaje encaja en varias, gana la primera de
esta lista:

1. `fuera_de_tema`, porque si no va dirigido al negocio, lo demás no aplica.
2. `no_interesado`, porque rechazar la oferta pesa más que cómo quiere que se le hable.
3. `prefiere_escrito`, **si rechaza la llamada de forma explícita**, aunque además pida
   información.
4. `quiere_contacto`.
5. `pospone`.
6. `pide_informacion`, incluido el caso en que menciona el canal **de pasada**.
7. `sin_intencion`.

Las dos fronteras que más se confunden:

- **`prefiere_escrito` o `pide_informacion`.** ¿Dice que **no** a la llamada? Entonces es
  `prefiere_escrito`. ¿Pide la información y el canal solo acompaña? Entonces es
  `pide_informacion`.
- **`quiere_contacto` o `pospone`.** ¿Propone un momento concreto para hablar? Entonces es
  `quiere_contacto`. ¿Solo aplaza? Entonces es `pospone`.

Si después de aplicar la lista sigue habiendo duda, se elige y se escribe el motivo en
`nota`. Esas notas son las que dicen si hay que afinar un criterio.

---

## 4 · Ejemplos

Son **frases inventadas que imitan el patrón de cada clase. No son paráfrasis de filas
concretas del dataset**, a propósito: un ejemplo sacado de una fila del conjunto de
evaluación, aunque esté parafraseado, dejaría que el clasificador viera la respuesta antes
del examen. Por la misma razón, **los ejemplos few-shot de un prompt nunca salen de leads
que estén en el conjunto de evaluación**. 4 leads tienen dos respuestas distintas, así que
separar por fila no basta: se separa por lead.

| Clase | Ejemplo 1 | Ejemplo 2 |
|---|---|---|
| `pide_informacion` | "¿Qué incluye el programa y en cuánto queda?" | "Me cuentas por aquí de qué se trata, porfa" |
| `quiere_contacto` | "Llámame el miércoles después del almuerzo" | "Nadie me ha marcado todavía" |
| `prefiere_escrito` | "Por teléfono no puedo, escríbeme mejor" | "Solo por chat, las llamadas no las contesto" |
| `pospone` | "Ahorita estoy manejando, más tarde te escribo" | "Déjame hablarlo en casa y te cuento" |
| `no_interesado` | "Lo vamos a dejar así, gracias" (sin baja) | "No me sigan escribiendo, por favor" (**baja_explicita = si**) |
| `sin_intencion` | "Recibido 🙏" | "👌" |
| `fuera_de_tema` | "Te mando el pedido de mañana: dos cajas" (chat equivocado) | "Le ofrecemos nuestro software de facturación" (otro negocio) |

Y para los filtros:

| Filtro | Ejemplo |
|---|---|
| `respuesta_automatica` | "Gracias por escribirnos. Nuestro horario es de lunes a viernes; te responderemos pronto." |
| `sin_texto` | (una nota de voz) |

---

## 5 · Casos frontera (v2)

Reglas para los casos que la v1 dejaba abiertos. **Si un caso de esta sección choca con una
regla anterior, manda esta sección.** Los ejemplos son frases inventadas.

**5.1 · Afirmación corta o emoji que responde a una pregunta del mensaje saliente.**
- **Una afirmación explícita** ("sí", "claro", "dale") que responde a una pregunta cerrada
  sobre contactar ("¿te llamamos?", "¿hablamos mañana?") es **`quiere_contacto`**.
  Ejemplo: al "¿Te marcamos esta tarde?" responde *"Sí, a esa hora me sirve"*.
- **Un emoji solo o un monosílabo que no afirma nada** ("ya", "ok", "mmm") sigue siendo
  **`sin_intencion`**, aunque el saliente preguntara algo. No se lee como una hora concreta.
  Ejemplo: al "¿Cuándo te va bien?" responde *"Mmm"*.
- **Si el saliente no preguntaba nada**, una afirmación suelta es **`sin_intencion`**.

**5.2 · Ocupada ahora, o explicación de por qué no contestó.**
- **Describe algo que le impide hablar AHORA** (conduciendo, en clase, sin cobertura en este
  momento) → **`pospone`**. Ejemplo: *"Voy en el bus, luego hablamos"*.
- **Explica por qué no contestó ANTES** y no pide nada → **`sin_intencion`**. Ejemplo:
  *"Es que el celular estaba en silencio"*.

**5.3 · Mensaje que solo indica el canal.**
- **Si el mensaje entero es la preferencia de canal escrito** ("por aquí", "¿se puede por
  chat?"), es **`prefiere_escrito`** aunque no rechace la llamada con palabras. Ejemplo:
  *"Mejor por este chat"*.
- **Si además pide información**, sin rechazar la llamada, es **`pide_informacion`**.
  Ejemplo: *"Por acá mándame los detalles del plan"*.

**5.4 · Rechazo de la llamada temporal o permanente.**
- La distinción no cambia la clase. **Si pide seguir por escrito** porque ahora no puede
  hablar (viaje, trabajo), es **`prefiere_escrito`**. Ejemplo: *"Estoy de viaje, escríbeme
  mejor"*.
- **Si solo dice que ahora no puede**, sin pedir el canal escrito, es **`pospone`**.
  Ejemplo: *"Esta semana imposible"*.

**5.5 · No aplica del todo.**
- **Lo da como motivo para no seguir**, por ejemplo un hijo fuera de la edad o un bebé que
  aún no nace → **`no_interesado`**. Ejemplo: *"Mi hija ya tiene seis años, gracias"*.
- **Pregunta si le sirve igual** → **`pide_informacion`**. Ejemplo: *"¿Sirve para un niño
  de cuatro?"*.
- **No es madre ni padre pero pregunta por un producto** → **`pide_informacion`**.
  Ejemplo: *"Es para regalar a mi sobrino, ¿qué trae?"*.

**5.6 · Intención de compra, o mensaje prellenado de la página.**
- Los dos son **`pide_informacion`**. Ejemplo: *"Lo quiero, ¿cómo pago?"*.
- **Si además da un momento para hablar** → **`quiere_contacto`**. Ejemplo: *"Quiero
  comprarlo, llámame a las cinco"*.

**5.7 · Confirmar una cita o llamada que ya propuso la empresa.**
- Aceptar un momento concreto que ofreció la empresa es **`quiere_contacto`**. Ejemplo: al
  "Te llamamos el jueves a las 10" responde *"Perfecto, ahí estaré"*.
- **Un "ok" o un emoji sin afirmar nada** sigue la regla 5.1.

**5.8 · Palabras ambiguas de rechazo.**
- **"Cancelar", "no" o "ya no"** sin pedir que no la contacten → **`no_interesado`**, sin
  baja.
- **`baja_explicita = si` solo** si pide de forma explícita que no la contacten más.
  Ejemplo con baja: *"Bórrenme de su lista"*.
- **Una objeción de precio** sin pedir nada más ("es muy caro") → **`no_interesado`**.
- **"Ya me atendieron"** → **`sin_intencion`**.
- **Preguntar cómo se agenda, o qué número llama** para poder contestar →
  **`quiere_contacto`**.

**5.9 · Dónde van las dudas.**
- La duda se escribe en la columna de notas del formato que se use: `nota` en el etiquetado
  humano, `motivo` en el de Claude.
- **Máximo 12 palabras, sin citar al cliente.**
