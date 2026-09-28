"""Pruebas en negativo de data/prepare.py con datos SINTETICOS inventados.

Ningun nombre, telefono ni correo pertenece a una persona real: telefonos del bloque 555,
correos del dominio reservado .test, marcas inventadas ("acme", "zorbo").
"""
import csv
import unittest


from data import prepare as s

FAKE_NAMES = ["Zenaida Oquendo Pérez", "Luz Yolima Quintero", "Belarmino Tovar",
              "Maria de los Angeles", "Mama de Sofi", "Dios es amor", "Floribel de Agosto",
              "Julio Rendon"]
FAKE_NAMES += ["Ana Peña", "Informacion Pedida", "Pilar Mora"]
# Perfiles de tienda INVENTADOS que meten palabras comunes en el diccionario, como en [A].
FAKE_NAMES += ["Entre Nubes", "Hogar Dulce Hogar", "Sistema Pos", "Segun Dios",
               "Clara Quiñonero"]
FAKE_CORPUS_COMMON = ["informacion", "pedida", "pilar"]
# Marcas INVENTADAS: la real nunca va en un archivo que se publica.
FAKE_BRANDS = ["COMPANY|acme kids", "COMPANY|acme", "PRODUCT|zorbo zorbo"]
PATTERN, TOKENS = s.build_name_pattern(FAKE_NAMES, FAKE_CORPUS_COMMON)
BRANDS = s.build_brand_patterns(FAKE_BRANDS)


def run(text):
    return s.scrub(text, PATTERN, BRANDS)


class Estructural(unittest.TestCase):
    def test_telefonos_en_varios_formatos(self):
        for t in ["+57 310 555 0101", "3105550101", "310-555-0101", "(310) 555 0101"]:
            self.assertEqual(run(f"mi numero {t} gracias")[0], "mi numero [PHONE] gracias", t)

    def test_numeros_cortos_no_son_telefono(self):
        self.assertEqual(run("puedo a las 3 o el 25")[0], "puedo a las 3 o el 25")

    def test_correo_y_url(self):
        self.assertEqual(run("escribo a zq@ejemplo.test")[0], "escribo a [EMAIL]")
        self.assertEqual(run("mira www.ejemplo.test/x")[0], "mira [URL]")

    def test_importes(self):
        for t in ["$250.000", "300 mil", "USD 50", "120.000 pesos"]:
            self.assertIn("[AMOUNT]", run(f"cuesta {t}")[0], t)

    def test_direcciones(self):
        for t in ["Calle 45 # 12-30", "Cra 7 No. 20-15", "av 68"]:
            self.assertIn("[ADDRESS]", run(f"vivo en {t}")[0], t)


class Nombres(unittest.TestCase):
    def test_nombre_en_cualquier_forma(self):
        for t in ["Zenaida", "zenaida", "ZENAIDA", "Zenáida", "Oquendo", "Perez", "Pérez"]:
            self.assertEqual(run(f"hola soy {t}")[0], "hola soy [NAME]", t)

    def test_no_sustituye_dentro_de_otra_palabra(self):
        # "tovar" es apellido del diccionario; "tovarich" no debe tocarse
        self.assertEqual(run("dijo tovarich")[0], "dijo tovarich")

    def test_colision_con_palabra_comun_se_sustituye_y_se_marca(self):
        text, flags = run("no hay luz en la casa")
        self.assertEqual(text, "no hay [NAME] en la casa")
        self.assertIn("name_collision:luz", flags)

    def test_mayuscula_desconocida_se_marca_no_se_borra(self):
        text, flags = run("vivo en Medellín desde enero")
        self.assertIn("Medellín", text)
        self.assertIn("cap:Medellín", flags)

    def test_particulas_y_perfiles_no_borran_palabras_comunes(self):
        text, _ = run("gracias, los ninos de la casa van a la cita con amor")
        self.assertEqual(text, "gracias, los ninos de la casa van a la cita con amor")

    def test_nombre_de_perfil_si_se_sustituye(self):
        self.assertEqual(run("saludos de sofi")[0], "saludos de [NAME]")

    def test_los_meses_no_son_nombres_salvo_julio_y_abril(self):
        self.assertEqual(run("puedo en agosto o en mayo")[0], "puedo en agosto o en mayo")
        text, flags = run("el 3 de julio")
        self.assertEqual(text, "el 3 de [NAME]")
        self.assertIn("name_collision:julio", flags)

    def test_la_ñ_es_otra_letra(self):
        self.assertEqual(run("que pena contigo")[0], "que pena contigo")
        self.assertEqual(run("soy Ana Peña")[0], "soy [NAME] [NAME]")

    def test_palabras_comunes_medidas_en_el_corpus_no_se_borran(self):
        self.assertEqual(run("me envias la informacion")[0], "me envias la informacion")

    def test_colision_frecuente_en_corpus_sigue_siendo_nombre(self):
        self.assertEqual(run("soy pilar")[0], "soy [NAME]")


class PalabrasComunesEnElDiccionario(unittest.TestCase):
    """Casos vistos en [A] el 26 sep, con frases PARAFRASEADAS (nunca el texto real)."""

    def test_0059_preposicion_no_se_borra(self):
        self.assertEqual(run("entre mas me cuentes mejor")[0], "entre mas me cuentes mejor")

    def test_segun_con_tilde_no_se_borra(self):
        self.assertEqual(run("según lo que me digas")[0], "según lo que me digas")

    def test_0097_sustantivo_comun_no_se_borra(self):
        self.assertEqual(run("cosas para el hogar y el bebe")[0], "cosas para el hogar y el bebe")

    def test_0104_sigla_comun_no_se_borra(self):
        self.assertEqual(run("le ofrezco un pos para su negocio")[0],
                         "le ofrezco un pos para su negocio")

    def test_0018_un_nombre_propio_sigue_borrado(self):
        # Invertida a proposito: en 0018 la palabra borrada ERA un nombre.
        self.assertEqual(run("aun no sabemos si sera Belarmino")[0], "aun no sabemos si sera [NAME]")

    def test_0145_colision_se_sustituye_y_se_marca(self):
        # Invertida a proposito: "clara" tambien es nombre frecuente. Privacidad primero.
        text, flags = run("la foto un poco mas clara")
        self.assertEqual(text, "la foto un poco mas [NAME]")
        self.assertIn("name_collision:clara", flags)

    def test_cada_sustitucion_queda_registrada_sin_el_nombre(self):
        text, flags = run("hola soy Zenaida Oquendo")
        self.assertEqual(text, "hola soy [NAME] [NAME]")
        self.assertEqual(flags, ["name:w3", "name:w4"])
        self.assertFalse(any("zenaida" in s.fold(f) or "oquendo" in s.fold(f) for f in flags))


class FirmaDeVendedora(unittest.TestCase):
    """Mensajes manuales de vendedoras (26 sep): nombre, inicial, telefono. Sinteticos."""

    def test_inicial_del_apellido_tras_el_nombre_se_absorbe(self):
        text, flags = run("un gusto saludarte, Zenaida Q, asesora")
        self.assertEqual(text, "un gusto saludarte, [NAME], asesora")
        self.assertIn("firma_inicial", flags)

    def test_inicial_con_punto_se_absorbe(self):
        self.assertEqual(run("te escribe Belarmino T. del equipo")[0], "te escribe [NAME] del equipo")

    def test_dos_iniciales_seguidas_se_absorben_las_dos(self):
        self.assertEqual(run("hola Zenaida Q. R. te llamamos")[0], "hola [NAME] te llamamos")

    def test_conjuncion_y_no_es_una_inicial(self):
        self.assertEqual(run("Zenaida Y Belarmino")[0], "[NAME] Y [NAME]")

    def test_firma_con_nombre_completo_y_telefono(self):
        self.assertEqual(run("Le saluda Belarmino Tovar, escribeme al 310 555 0199")[0],
                         "Le saluda [NAME] [NAME], escribeme al [PHONE]")


class Marca(unittest.TestCase):
    def test_marca_y_producto(self):
        self.assertEqual(run("conocer Acme Kids hoy")[0], "conocer [COMPANY] hoy")
        self.assertEqual(run("quiero el zorbo zorbo")[0], "quiero el [PRODUCT]")

    def test_marca_con_tildes_mayusculas_y_pegada(self):
        self.assertEqual(run("sobre ÁCME Kidsbuenas tardes")[0], "sobre [COMPANY] tardes")

    def test_marca_de_varias_palabras_escrita_pegada(self):
        # 27 sep: con \s+ entre palabras, la forma pegada ("zorbozorbo") pasaba sin sustituir.
        self.assertEqual(run("el zorbozorbo llego")[0], "el [PRODUCT] llego")

    def test_palabra_que_empieza_por_la_marca_se_sustituye_entera(self):
        # A proposito: asi se atrapa la marca pegada a otra palabra. Privacidad primero.
        self.assertEqual(run("un acmeista")[0], "un [COMPANY]")

    def test_marca_en_medio_de_otra_palabra_no(self):
        self.assertEqual(run("la palabra placmeta")[0], "la palabra placmeta")


class Nombres2(unittest.TestCase):
    def test_mensaje_limpio_queda_intacto(self):
        self.assertEqual(run("si quiero reagendar la cita"), ("si quiero reagendar la cita", []))




class FugasYCli(unittest.TestCase):
    def test_en_negativo_la_marca_bloquea_la_publicacion(self):
        row = {"id": "x1", "flujo": "acme_flujo"}
        self.assertTrue(s.leak_check([row], ["id", "flujo"], TOKENS, BRANDS))

    def test_en_negativo_un_nombre_o_un_telefono_bloquean(self):
        self.assertTrue(s.leak_check([{"id": "zenaida"}], ["id"], TOKENS))
        self.assertTrue(s.leak_check([{"id": "3105550101"}], ["id"], TOKENS))
        self.assertTrue(s.leak_check([{"id": "x", "extra": ""}], ["id"], TOKENS))

    def test_en_negativo_una_arroba_bloquea(self):
        # Faltaba: apagar esta comprobacion no hacia fallar ninguna prueba (27 sep).
        self.assertTrue(s.leak_check([{"id": "zq@ejemplo"}], ["id"], set()))

    def test_fila_limpia_pasa(self):
        self.assertEqual(s.leak_check([{"id": "reply_0001"}], ["id"], TOKENS, BRANDS), [])


def test_cli_de_extremo_a_extremo(tmp_path):
    (tmp_path / "names.csv").write_text("name\n" + "\n".join(FAKE_NAMES), encoding="utf-8")
    (tmp_path / "brands.txt").write_text("\n".join(FAKE_BRANDS), encoding="utf-8")
    with open(tmp_path / "in.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "text", "outbound_text"])
        w.writerow(["m1", "soy Zenaida, 3105550101", "Hola Belarmino, te escribe Acme Kids"])
    s.main(["--input", str(tmp_path / "in.csv"), "--names", str(tmp_path / "names.csv"),
            "--brands", str(tmp_path / "brands.txt"), "--output", str(tmp_path / "out.csv")])
    row = next(csv.DictReader(open(tmp_path / "out.csv", encoding="utf-8")))
    assert row["text"] == "soy [NAME], [PHONE]"
    assert row["outbound_text"] == "Hola [NAME], te escribe [COMPANY]"
    assert "zenaida" not in row["scrub_flags"].lower()
