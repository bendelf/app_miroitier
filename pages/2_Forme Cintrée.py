import streamlit as st
import math
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, LineString, Point
import numpy as np
import tempfile
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import ezdxf

st.set_page_config(layout="centered")

st.title("🔺 Trapèze avec cintre — flèche perpendiculaire à CD")
st.info("🔁 Calcule la flèche réelle (projetée perpendiculairement à CD).  "
"  🎯 Affiche cette valeur exacte de flèche (selon la géométrie oblique du segment CD).  "
"  🧮 Dessine la forme cintrée avec cette flèche calculée correctement.")


# Zone de saisie de texte (une seule ligne)
ref = st.text_input("Entrez une référence")

# Zone de texte multiligne
observation = st.text_area("Entrez une observation")


# --- Entrées utilisateur ---
largeur = st.number_input("Largeur de la base AB (mm)", value=1000, min_value=1)
hg = st.number_input("Hauteur côté gauche (AD) (mm)", value=600, min_value=0)
hd = st.number_input("Hauteur côté droit (BC) (mm)", value=800, min_value=0)

mode_fleche = st.radio("Définir la flèche :", ["Saisie directe", "Calcul depuis la base"])

if mode_fleche == "Saisie directe":
    fleche = st.number_input("Flèche (mm)", value=50.0, min_value=0.0)
else:
    h_base = st.number_input("Hauteur verticale depuis le milieu de AB (mm)", value=700.0, min_value=0.0)

# --- Calcul des points de base ---
A = (0, 0)
B = (largeur, 0)
D = (0, hg)
C = (largeur, hd)
milieu_AB = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)

# --- Calcul de la flèche réelle si "Calcul depuis la base" ---
if mode_fleche == "Calcul depuis la base":
    P = (milieu_AB[0], milieu_AB[1] + h_base)  # point à projeter
    line_CD = LineString([D, C])
    proj = line_CD.interpolate(line_CD.project(Point(P)))
    fleche = int(Point(P).distance(proj))
    st.info(f"📐 Flèche réelle calculée perpendiculairement à CD : **{fleche:.2f} mm**")

# --- Génération des points de l’arc parabolique ---
def generate_arc(D, C, fleche, n_points=50):
    arc_points = []
    for t in np.linspace(0, 1, n_points):
        x = D[0] + t * (C[0] - D[0])
        y = D[1] + t * (C[1] - D[1])
        h = 4 * fleche * t * (1 - t)  # parabole
        dx, dy = C[0] - D[0], C[1] - D[1]
        norm = math.hypot(dx, dy)
        nx, ny = -dy / norm, dx / norm
        arc_points.append((x + nx * h, y + ny * h))
    return arc_points

arc = generate_arc(D, C, fleche)

# --- Création de la forme complète ---
points = [A, B, C] + arc[::-1] + [D]

# --- Calcul rectangle englobant ---
def minimum_bounding_rectangle(points):
    poly = Polygon(points)
    if not poly.is_valid:
        poly = poly.buffer(0)
    min_rect = poly.minimum_rotated_rectangle
    return list(min_rect.exterior.coords)[:-1]

rect = minimum_bounding_rectangle(points)

# --- Affichage graphique ---
def draw_shape_and_rectangle(shape_pts, rect_pts, fleche_pt=None):
    fig, ax = plt.subplots()

    poly = Polygon(shape_pts)
    x, y = poly.exterior.xy
    ax.fill(x, y, alpha=0.5, label="Forme")

    rx, ry = zip(*rect_pts + [rect_pts[0]])
    ax.plot(rx, ry, 'r--', label="Rectangle englobant")

    w = round(math.dist(rect_pts[0], rect_pts[1]), 2)
    h = round(math.dist(rect_pts[1], rect_pts[2]), 2)
    mid_top = ((rect_pts[0][0] + rect_pts[1][0]) / 2, (rect_pts[0][1] + rect_pts[1][1]) / 2)
    mid_right = ((rect_pts[1][0] + rect_pts[2][0]) / 2, (rect_pts[1][1] + rect_pts[2][1]) / 2)
    ax.text(*mid_top, f"{w} mm", ha="center", va="bottom", fontsize=10, color="red", backgroundcolor="white")
    ax.text(*mid_right, f"{h} mm", ha="left", va="center", fontsize=10, color="red", backgroundcolor="white")

    if fleche_pt:
        p1, p2 = fleche_pt
        # Si p1 et p2 sont des tuples (cas de saisie directe), on les transforme en Point
        if not isinstance(p1, Point): p1 = Point(p1)
        if not isinstance(p2, Point): p2 = Point(p2)

        ax.plot([p1.x, p2.x], [p1.y, p2.y], 'k:', lw=1.5)
        fx = (p1.x + p2.x) / 2
        fy = (p1.y + p2.y) / 2
        f_val = int(p1.distance(p2))
        ax.text(fx, fy, f"Flèche {f_val} mm", fontsize=9, ha='left', va='center', backgroundcolor='white')

    ax.set_aspect('equal')
    ax.axis('off')
    ax.legend()
    return fig

fleche_segment = None
if mode_fleche == "Calcul depuis la base":
    fleche_segment = [P, proj]

fig = draw_shape_and_rectangle(points, rect, fleche_segment)
st.pyplot(fig)

# --- Export PDF ---
def export_pdf(points, rect, fleche_segment=None, filename="forme_cintré.pdf"):
    # 1. Redessiner la figure complète (comme dans Streamlit)
    fig = draw_shape_and_rectangle(points, rect, fleche_segment)

    # 2. Sauvegarder en image temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png', mode="wb") as tmpfile:
        fig.savefig(tmpfile.name, bbox_inches='tight', dpi=200)
        image_path = tmpfile.name  # on garde le chemin
    plt.close(fig)

    # 3. Création du PDF avec en-tête + image
    pdf_path = os.path.join(tempfile.gettempdir(), filename)
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width_pdf, height_pdf = letter

    y = height_pdf - 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Fiche technique - Forme cintrée")
    y -= 20

    c.setFont("Helvetica", 10)
    if ref:
        c.drawString(40, y, f"Référence : {ref}")
        y -= 15
    if observation:
        c.drawString(40, y, f"Observation : {observation}")
        y -= 15
    c.drawString(40, y, f"Base :  {largeur} mm")
    y -= 15
    c.drawString(40, y, f"Côté gauche :  {hg} mm")
    y -= 15
    c.drawString(40, y, f"Côté droit :  {hd} mm")
    y -= 15

    rect_width = round(math.dist(rect[0], rect[1]), 2)
    rect_height = round(math.dist(rect[1], rect[2]), 2)
    c.drawString(40, y, f"Largeur rectangle englobant : {rect_width} mm")
    y -= 15
    c.drawString(40, y, f"Hauteur rectangle englobant : {rect_height} mm")
    y -= 15

    c.drawString(40, y, f"Flèche (réelle ou saisie) : {round(fleche, 2)} mm")
    y -= 25

    # 4. Insertion de l'image
    image_width = 450
    image_height = 300
    c.drawImage(image_path, 80, 100, width=image_width, height=image_height, preserveAspectRatio=True)

    c.save()
    os.unlink(image_path)
    return pdf_path

if st.button("📄 Exporter en PDF"):
    pdf_path = export_pdf(points, rect, fleche_segment)
    with open(pdf_path, "rb") as f:
        st.download_button("Télécharger le PDF", f, file_name=(ref or "forme") + ".pdf")


# --- Export DXF ---
def export_dxf(points, filename="forme.dxf"):
    doc = ezdxf.new()
    msp = doc.modelspace()
    closed_points = points + [points[0]]
    for i in range(len(closed_points) - 1):
        msp.add_line(closed_points[i], closed_points[i + 1])
    path = os.path.join(tempfile.gettempdir(), filename)
    doc.saveas(path)
    return path

if st.button("📐 Exporter en DXF"):
    dxf_path = export_dxf(points, ref + ".dxf")
    with open(dxf_path, "rb") as f:
        st.download_button("📥 Télécharger le DXF", f, file_name=(ref or "forme") + ".dxf", mime="application/dxf")