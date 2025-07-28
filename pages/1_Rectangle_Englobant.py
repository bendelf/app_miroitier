import streamlit as st
import math
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import ezdxf
import tempfile
import os

# --- Fonctions de formes géométriques ---
def losange_points_cote_angle(cote, angle_deg):
    angle_rad = math.radians(angle_deg)
    dx = cote * math.cos(angle_rad / 2)
    dy = cote * math.sin(angle_rad / 2)

    attributs = {
    }
    return [(-dx, 0), (0, dy), (dx, 0), (0, -dy)], attributs

def losange_points_diagonales(d1, d2):
    attributs = {
        "Diagonale 1 (mm)": d1,
        "Diagonale 2 (mm)": d2
    }
    return [(-d1 / 2, 0), (0, d2 / 2), (d1 / 2, 0), (0, -d2 / 2)], attributs

def trapeze_points(base1, base2, hauteur):
    dx = (base1 - base2) / 2
    attributs = {
        "Base 1 (mm)": base1,
        "Base 2 (mm)": base2,
        "Hauteur (mm)": hauteur
    }
    return [(-base1 / 2, 0), (base1 / 2, 0), (base2 / 2, hauteur), (-base2 / 2, hauteur)], attributs

def trapeze_rectangle_points(hauteur1, hauteur2, base):
    """
    Trapèze rectangle avec l'angle droit en bas à gauche.
    """
    attributs = {
        "Hauteur 1 (mm)": hauteur1,
        "Hauteur 2 (mm)": hauteur2,
        "Base (mm)": base
    }
    return [
        (0, 0),  # A
        (base, 0),  # B
        (base, hauteur2),  # C
        (0, hauteur1)  # D
    ], attributs

def parallelogramme_points(base, cote, angle_deg):
    angle_rad = math.radians(angle_deg)
    dx = cote * math.cos(angle_rad)
    dy = cote * math.sin(angle_rad)
    attributs = {
    }
    return [(0, 0), (base, 0), (base + dx, dy), (dx, dy)], attributs


def construire_quadrilatere_ab_parallele_cd(ab, bc, cd, da, angle_a_deg, angle_b_deg):
    """Construit un quadrilatère avec AB ‖ CD et vérifie la fermeture."""
    A = (0, 0)
    B = (ab, 0)

    angle_a_rad = math.radians(180 - angle_a_deg)
    angle_b_rad = math.radians(180 - angle_b_deg)

    Dx = A[0] - da * math.cos(angle_a_rad)
    Dy = A[1] + da * math.sin(angle_a_rad)
    D = (Dx, Dy)

    Cx = B[0] + bc * math.cos(angle_b_rad)
    Cy = B[1] + bc * math.sin(angle_b_rad)
    C = (Cx, Cy)

    # Repositionne C pour que CD soit parallèle à AB (horizontal)
    Cx_corrected = Dx + cd
    Cy_corrected = Dy
    C_corrected = (Cx_corrected, Cy_corrected)

    ecart = math.hypot(C_corrected[0] - C[0], C_corrected[1] - C[1])
    ferme = ecart < 0.9

    attributs = {
    }

    return [A, B, C_corrected, D], ferme, ecart, attributs

def construire_quadrilatere_general(ab, bc, cd, da, angle_a_deg, angle_b_deg):
    """
    Construit un quadrilatère général (non parallèle) défini par :
    - longueurs : AB, BC, CD, DA
    - angles intérieurs : angle_A (entre DA et AB), angle_B (entre AB et BC)
    """
    A = (0, 0)
    B = (ab, 0)

    angle_a_rad = math.radians(180 - angle_a_deg)
    angle_b_rad = math.radians(180 - angle_b_deg)

    # Point D à partir de A et DA orienté à pi - angle_A
    D = (
        A[0] + da * math.cos(math.pi - angle_a_rad),
        A[1] + da * math.sin(math.pi - angle_a_rad)
    )

    # Point C à partir de B et BC orienté à angle_B
    C = (
        B[0] + bc * math.cos(angle_b_rad),
        B[1] + bc * math.sin(angle_b_rad)
    )

    # Vérification de fermeture
    cd_calc = math.hypot(C[0] - D[0], C[1] - D[1])
    ecart = abs(cd_calc - cd)
    ferme = ecart < 0.9

    attributs = {
    }

    return [A, B, C, D], ferme, ecart, attributs

# --- Calcul du rectangle englobant ---
def minimum_bounding_rectangle(points):
    poly = Polygon(points)
    rect = poly.minimum_rotated_rectangle
    return list(rect.exterior.coords)[:-1]

# --- Dessin de la forme et du rectangle ---
def draw_shape_and_rectangle(shape_pts, rect_pts):
    fig, ax = plt.subplots()

    # Tracer la forme
    shape_poly = Polygon(shape_pts)
    x, y = shape_poly.exterior.xy
    ax.fill(x, y, alpha=0.5, label="Forme")

    # Tracer le rectangle englobant
    rect_poly = Polygon(rect_pts)
    x_rect, y_rect = rect_poly.exterior.xy
    ax.plot(x_rect, y_rect, 'r--', label="Rectangle englobant")

    # Affichage des dimensions sur les côtés
    # Supposé : ordre des points rect_pts = [p0, p1, p2, p3]
    p0, p1, p2, p3 = rect_pts
    mid_top = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    mid_right = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

    width = round(math.dist(p0, p1), 2)
    height = round(math.dist(p1, p2), 2)

    ax.text(*mid_top, f"{width}", color='red', fontsize=12, ha='center', va='bottom', backgroundcolor='white')
    ax.text(*mid_right, f"{height}", color='red', fontsize=12, ha='left', va='center', backgroundcolor='white')

    ax.axis('equal')
    ax.legend()
    return fig


# --- Export PDF ---

def export_forme_pdf(points, rect, ref="", observation="", attributs=None, titre="Fiche technique", filename="forme.pdf"):
    """
    points : liste de tuples (points de la forme)
    rect : rectangle englobant (liste de 4 points)
    ref : texte de référence
    observation : texte libre
    attributs : dictionnaire de paramètres spécifiques à la forme
    """
    # 1. Redessiner et sauvegarder le schéma
    fig = draw_shape_and_rectangle(points, rect)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png', mode="wb") as tmpfile:
        fig.savefig(tmpfile.name, bbox_inches='tight', dpi=200)
        image_path = tmpfile.name
    plt.close(fig)

    # 2. Créer le PDF
    pdf_path = os.path.join(tempfile.gettempdir(), filename)
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width_pdf, height_pdf = A4

    y = height_pdf - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, titre)
    y -= 25

    c.setFont("Helvetica", 10)
    if ref:
        c.drawString(40, y, f"Référence : {ref}")
        y -= 15
    if observation:
        c.drawString(40, y, f"Observation : {observation}")
        y -= 15

    # Afficher les attributs spécifiques à la forme
    if attributs:
        for key, value in attributs.items():
            c.drawString(40, y, f"{key} : {value}")
            y -= 15

    # Dimensions rectangle englobant
    rect_width = round(math.dist(rect[0], rect[1]), 2)
    rect_height = round(math.dist(rect[1], rect[2]), 2)
    y -= 5
    c.drawString(40, y, f"Largeur rectangle englobant : {rect_width} mm")
    y -= 15
    c.drawString(40, y, f"Hauteur rectangle englobant : {rect_height} mm")
    y -= 25

    # 3. Insertion image
    image_width = 450
    image_height = 300
    c.drawImage(image_path, 80, 100, width=image_width, height=image_height, preserveAspectRatio=True)

    c.save()
    os.unlink(image_path)
    return pdf_path


def export_quadrilatere_to_dxf(points, filename="quadrilatere.dxf", ref="", observation=""):
    """
    Exporte les points d'un quadrilatère vers un fichier DXF avec une référence et une observation.
    Les points doivent être dans l'ordre [A, B, C, D].
    """
    doc = ezdxf.new()
    msp = doc.modelspace()

    # Fermer la boucle : A→B→C→D→A
    ordered_points = points + [points[0]]
    for i in range(len(ordered_points) - 1):
        msp.add_line(ordered_points[i], ordered_points[i + 1])

    # Position de base pour les annotations (au-dessus du point A)
    base_x, base_y = points[0]
    text_height = 2.5

    if ref:
        msp.add_text(f"Réf : {ref}", dxfattribs={"height": text_height}).set_placement(
            (base_x, base_y + 10),
            align="LEFT"
        )

    if observation:
        msp.add_text(f"Note : {observation}", dxfattribs={"height": text_height}).set_placement(
            (base_x, base_y + 7),
            align="LEFT"
        )

    # Créer un fichier temporaire et retourner le chemin
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    doc.saveas(temp_path)
    return temp_path


# --- Interface Streamlit ---
def main():
    st.set_page_config(page_title="Rectangle Englobant", page_icon="📐")
    st.title("📐 Calcul du rectangle englobant")
    st.info("Calcule le plus petit rectangle possible dans laquelle la forme est englobée")

    # Zone de saisie de texte (une seule ligne)
    ref = st.text_input("Entrez une référence")

    # Zone de texte multiligne
    observation = st.text_area("Entrez une observation")
    forme = st.selectbox("Choisir une forme :", [
        "Losange (côté + angle)",
        "Losange (2 diagonales)",
        "Trapèze isocèle",
        "Trapèze rectangle",
        "Parallélogramme",
        "Quadrilatère général",
        "Charger un DXF"
    ])

    points = []
    if forme == "Losange (côté + angle)":
        cote = st.number_input("Longueur du côté (mm)", value=1000, min_value=1)
        angle = st.number_input("Angle en degrés", value=60.0, min_value=1.0, max_value=179.0)
        points, attributs = losange_points_cote_angle(cote, angle)

    elif forme == "Losange (2 diagonales)":
        d1 = st.number_input("Diagonale 1 (mm)", value=1000, min_value=1)
        d2 = st.number_input("Diagonale 2 (mm)", value=600, min_value=1)
        points, attributs = losange_points_diagonales(d1, d2)

    elif forme == "Trapèze isocèle":
        base1 = st.number_input("Grande base (mm)", value=1000, min_value=1)
        base2 = st.number_input("Petite base (mm)", value=600, min_value=1)
        hauteur = st.number_input("Hauteur (mm)", value=400, min_value=1)
        points, attributs = trapeze_points(base1, base2, hauteur)

    elif forme == "Trapèze rectangle":
        hauteur1 = st.number_input("Hauteur 1 (mm)", value=1000, min_value=1)
        hauteur2 = st.number_input("Hauteur 2 (mm)", value=700, min_value=1)
        base = st.number_input("Base (mm)", value=400, min_value=1)
        points, attributs = trapeze_rectangle_points(hauteur1, hauteur2, base)

    elif forme == "Parallélogramme":
        base = st.number_input("Longueur de la base (mm)", value=1000, min_value=1)
        cote = st.number_input("Longueur du côté adjacent (mm)", value=600, min_value=1)
        angle = st.number_input("Angle entre base et côté (°)", value=60.0, min_value=1.0, max_value=179.0)
        points, attributs = parallelogramme_points(base, cote, angle)

    elif forme == "Quadrilatère avec côtés opposés parallèles (AB ‖ CD)":
        ab = st.number_input("Longueur AB", value=1000, min_value=1)
        bc = st.number_input("Longueur BC", value=600, min_value=1)
        cd = st.number_input("Longueur CD", value=1000, min_value=1)
        da = st.number_input("Longueur DA", value=600, min_value=1)
        angle_a = st.number_input("Angle A (en degrés)", value=60.0, min_value=0.0, max_value=180.0)
        angle_b = st.number_input("Angle B (en degrés)", value=60.0, min_value=0.0, max_value=180.0)

        points, ferme, ecart, attributs = construire_quadrilatere_ab_parallele_cd(ab, bc, cd, da, angle_a, angle_b)

        if ferme:
            st.success("✅ La figure se ferme correctement.")
        else:
            st.error(f"❌ La figure ne se ferme pas (écart de {ecart:.2f} unités).")

    elif forme == "Quadrilatère général":
        ab = st.number_input("Longueur AB", value=10.0, min_value=0.1)
        bc = st.number_input("Longueur BC", value=6.0, min_value=0.1)
        cd = st.number_input("Longueur CD", value=10.0, min_value=0.1)
        da = st.number_input("Longueur DA", value=6.0, min_value=0.1)
        angle_a = st.number_input("Angle A (en degrés)", value=60.0, min_value=0.0, max_value=180.0)
        angle_b = st.number_input("Angle B (en degrés)", value=60.0, min_value=0.0, max_value=180.0)

        points, ferme, ecart, attributs = construire_quadrilatere_general(ab, bc, cd, da, angle_a, angle_b)

        if ferme:
            st.success("✅ La figure se ferme correctement.")
        else:
            st.error(f"❌ La figure ne se ferme pas (écart de {ecart:.2f} unités).")

    elif forme == "Charger un DXF":
        uploaded_file = st.file_uploader("Chargez un fichier DXF", type=["dxf"])
        if uploaded_file is not None:
            try:
                import io
                dxf_stream = io.BytesIO(uploaded_file.read())
                doc = ezdxf.read(stream=dxf_stream)  # ✅ bonne fonction
                msp = doc.modelspace()
                entities = []

                for e in msp:
                    if e.dxftype() in ["LWPOLYLINE", "POLYLINE"]:
                        try:
                            # LWPOLYLINE
                            points = [(v[0], v[1]) for v in e.get_points()]
                        except AttributeError:
                            # POLYLINE (3D)
                            points = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices()]
                        if e.closed or points[0] == points[-1]:
                            entities.append(points)
                    elif e.dxftype() == "LINE":
                        start = e.dxf.start
                        end = e.dxf.end
                        entities.append([start[:2], end[:2]])

                all_points = [pt for entity in entities for pt in entity]
                if len(all_points) >= 3:
                    points = all_points
                    attributs = {"Source DXF": "Oui"}
                else:
                    st.warning("Aucune forme fermée trouvée dans le fichier DXF.")
                    points = []

            except Exception as e:
                st.error(f"Erreur lors de la lecture du fichier DXF : {e}")
                points = []

    if points:
        rect = minimum_bounding_rectangle(points)
        fig = draw_shape_and_rectangle(points, rect)
        st.pyplot(fig)

        # Dimensions rectangle englobant
        rect_width = round(math.dist(rect[0], rect[1]), 2)
        rect_height = round(math.dist(rect[1], rect[2]), 2)

        st.success("📏 Dimensions du rectangle englobant :")
        st.markdown(f"**Largeur** : {rect_width} mm")
        st.markdown(f"**Hauteur** : {rect_height} mm")

        # Export PDF
        if st.button("📄 Exporter en PDF"):
            pdf_path = export_forme_pdf(
                points=points,
                rect=rect,
                ref=ref,
                observation=observation,
                attributs=attributs,
                titre="Forme",
                filename=(ref or "forme") + ".pdf"
            )
            with open(pdf_path, "rb") as f:
                st.download_button("Télécharger le PDF", f, file_name=(ref or "forme") + ".pdf")


        # Eport DXF
        if st.button("📐 Exporter en DXF"):
            dxf_path = export_quadrilatere_to_dxf(points, "quadrilatere_export.dxf", ref="", observation="")
            with open(dxf_path, "rb") as f:
                st.download_button(
                    label="📥 Télécharger le fichier DXF",
                    data=f,
                    file_name=(ref or "forme") + ".dxf",
                    mime="application/dxf"
                )
if __name__ == "__main__":
    main()



#python -m streamlit run Home.py