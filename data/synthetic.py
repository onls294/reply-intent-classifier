"""Public synthetic evaluation set (label_source = synthetic).

70 invented replies written from data/LABELING_GUIDE.md (v2), never paraphrased from real
rows. The class mix follows the v2 reference labels (164 real rows) scaled to 70. The
outbound messages are invented too and use the same pseudonymization markers as the real
data ([NAME], [COMPANY]). Labels were assigned by the author of this set from the guide.

This is what lets anyone re-run the evaluation without the private customer text.
Similarity to the real rows is checked by data/check_synthetic_similarity.py (outside the repo
data, it needs the private file) and reported in eval/results.md.
"""
import csv
from pathlib import Path

O1 = "Hola [NAME], te llamamos de [COMPANY] y no logramos hablar. ¿En qué horario te podemos marcar?"
O2 = "Hola [NAME], seguimos pendientes de tu consulta sobre el programa para bebés. ¿Te interesa que te contemos más?"
O3 = "[NAME], mañana a las 11 te llama tu asesora para resolver tus dudas. ¡Hasta pronto!"
O4 = "Hola [NAME], vimos que no pudiste conectarte a la cita de hoy. ¿Quieres que la reprogramemos?"
O5 = "Hola [NAME], ¿cómo vas? Te escribimos para saber si pudiste revisar la información que te enviamos."

# (outbound, reply, label, explicit_opt_out)
ROWS = [
    # sin_intencion (17)
    (O2, "Saludos 😊", "sin_intencion", False),
    (O1, "Qué tal todo por allá", "sin_intencion", False),
    (O3, "Recibido, gracias", "sin_intencion", False),
    (O5, "👌", "sin_intencion", False),
    (O1, "😀😀", "sin_intencion", False),
    (O5, "Anotado", "sin_intencion", False),
    (O3, "Ah, entendido", "sin_intencion", False),
    (O1, "Es que tenía el teléfono cargando", "sin_intencion", False),
    (O2, "Ya me contactó otra asesora hace días", "sin_intencion", False),
    (O4, "Feliz tarde para ti", "sin_intencion", False),
    (O1, "...", "sin_intencion", False),
    (O5, "Jajaja", "sin_intencion", False),
    (O1, "Estaba en la ducha cuando llamaron", "sin_intencion", False),
    (O3, "Gracias igualmente", "sin_intencion", False),
    (O1, "Mmmm 🤔", "sin_intencion", False),
    (O2, "Hey 👋", "sin_intencion", False),
    (O3, "🙏🏼", "sin_intencion", False),
    # pide_informacion (15)
    (O2, "¿Cuánto vale la suscripción mensual?", "pide_informacion", False),
    (O2, "Me interesa, ¿qué incluye el paquete?", "pide_informacion", False),
    (O5, "¿Tienen sede física o todo es en línea?", "pide_informacion", False),
    (O2, "¿Desde qué edad sirve el material?", "pide_informacion", False),
    (O1, "Mándame por aquí los precios y formas de pago", "pide_informacion", False),
    (O5, "¿Aceptan pago con tarjeta en cuotas?", "pide_informacion", False),
    (O1, "No recuerdo haber pedido nada, ¿de qué es esto?", "pide_informacion", False),
    (O2, "¿Funciona con gemelos de dos años?", "pide_informacion", False),
    (O5, "Quiero comprarlo para mi nieta, ¿cómo lo pido?", "pide_informacion", False),
    (O2, "¿El programa trae libros físicos?", "pide_informacion", False),
    (O1, "Hola, ¿cuánto dura el curso completo?", "pide_informacion", False),
    (O5, "¿Hay descuento si pago de contado?", "pide_informacion", False),
    (O1, "Me llegó un mensaje suyo, ¿qué venden exactamente?", "pide_informacion", False),
    (O5, "Quisiera ver un video de cómo funciona", "pide_informacion", False),
    (O2, "¿En qué idiomas viene el contenido?", "pide_informacion", False),
    # no_interesado (11)
    (O2, "Lo descarto de momento", "no_interesado", False),
    (O5, "Ya compramos algo parecido, gracias igual", "no_interesado", False),
    (O2, "Está fuera de mi presupuesto", "no_interesado", False),
    (O5, "Por favor no me vuelvan a escribir", "no_interesado", True),
    (O2, "No, gracias, mi bebé ya pasó esa etapa", "no_interesado", False),
    (O4, "Cancelen todo, gracias", "no_interesado", False),
    (O1, "Nop, paso", "no_interesado", False),
    (O5, "Lo pensé mejor y no", "no_interesado", False),
    (O2, "Muy caro para nosotros", "no_interesado", False),
    (O5, "Mi esposo dice que no, gracias", "no_interesado", False),
    (O2, "Ya no estoy buscando eso", "no_interesado", False),
    # prefiere_escrito (11)
    (O1, "No contesto llamadas de números desconocidos, escríbeme", "prefiere_escrito", False),
    (O1, "Por chat mejor", "prefiere_escrito", False),
    (O1, "¿Se puede todo por mensaje?", "prefiere_escrito", False),
    (O1, "Trabajo todo el día, solo puedo leer mensajes", "prefiere_escrito", False),
    (O3, "Prefiero que me escriban, no me llamen", "prefiere_escrito", False),
    (O1, "Todo por este chat si se puede", "prefiere_escrito", False),
    (O1, "Estoy en otro país, sigamos por WhatsApp", "prefiere_escrito", False),
    (O1, "No puedo hablar por teléfono, pero pregúntame por acá", "prefiere_escrito", False),
    (O3, "Sin llamadas, solo texto", "prefiere_escrito", False),
    (O4, "Mejor escríbeme los detalles, no alcanzo a contestar", "prefiere_escrito", False),
    (O1, "Por este medio está bien", "prefiere_escrito", False),
    # quiere_contacto (11)
    (O1, "Llámenme hoy después de las 6", "quiere_contacto", False),
    (O1, "El sábado en la mañana me queda bien", "quiere_contacto", False),
    (O3, "Sí, a esa hora estoy libre", "quiere_contacto", False),
    (O4, "Sí, reprogramemos para el martes", "quiere_contacto", False),
    (O1, "Sigo esperando la llamada que me dijeron", "quiere_contacto", False),
    (O2, "Claro, márquenme", "quiere_contacto", False),
    (O1, "A las 3 pm estoy disponible", "quiere_contacto", False),
    (O3, "¿Qué número me va a llamar? Para no rechazarlo", "quiere_contacto", False),
    (O4, "Mejor el jueves a las 10", "quiere_contacto", False),
    (O1, "Ahora mismo puedo atender", "quiere_contacto", False),
    (O2, "Sí, quiero la llamada con la asesora", "quiere_contacto", False),
    # pospone (4)
    (O1, "Estoy en junta, luego reviso", "pospone", False),
    (O4, "Estos días ando a full, más adelante hablamos", "pospone", False),
    (O5, "Tengo que verlo con mi pareja, después te digo", "pospone", False),
    (O1, "Estoy cocinando, en un rato te escribo", "pospone", False),
    # fuera_de_tema (1)
    (O5, "Amiga, ¿me pasas la receta del pastel?", "fuera_de_tema", False),
]


def rows():
    """[{id, outbound_text, reply_text, label, explicit_opt_out, label_source}]"""
    return [{"id": f"syn_{i:03d}", "outbound_text": o, "reply_text": r, "label": lab,
             "explicit_opt_out": opt, "label_source": "synthetic"}
            for i, (o, r, lab, opt) in enumerate(ROWS, 1)]


def write_csv(path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows()[0]))
        w.writeheader()
        w.writerows(rows())


if __name__ == "__main__":
    write_csv(Path(__file__).with_name("synthetic.csv"))
