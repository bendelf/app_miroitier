import streamlit as st
import math
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
import os
import ezdxf

def minimum_bounding_rectangle(points):
    poly = Polygon(points)
    if not poly.is_valid:
        poly = poly.buffer(0)
    min_rect = poly.minimum_rotated_rectangle
    return list(min_rect.exterior.coords)[:-1]

def rectangle_cintre_points(largeur, hg, hd, fleche, n_points=20):
    """Construit les points d’un rectangle avec un cintre en haut (arc simulé par segments)."""
    x0, y0 = 0, hg
    x1, y1 = largeur, hd

    # Base
    p1 = (0, 0)
    p2 = (largeur, 0)

    # Côtés verticaux
    p3 = (largeur, hd)
    p0 = (0, hg)

    # Génération de l’arc simulé (flèche au milieu)
    arc_points = []
    for i in range(n_points + 1):
        t = i / n_points
        x = x0 + t * (x1 - x0)
        # Interpolation linéaire + ajout de flèche au milieu
        y = y0 + t * (y1 - y0)
        h = 4 * fleche * t * (1 - t)  # Parabole
        arc_points.append((x, y + h))

    return [p1, p2, p3] + arc_points[::-1] + [p0]

def draw_shape_and_rectangle(shape_pts, rect_pts):
    fig, ax = plt.subplots()

    shape_poly = Polygon(shape_pts)
    x, y = shape_poly.exterior.xy
    ax.fill(x, y, alpha=0.5, label="Forme")

    rect_poly = Polygon(rect_pts)
    x_rect, y_rect = rect_poly.exterior.xy
    ax.plot(x_rect, y_rect, 'r--', label="Rectangle englobant")

    # Dimensions sur le dessin
    p0, p1, p2, p3 = rect_pts
    mid_top = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    mid_right = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

    width = round(math.dist(p0, p1), 2)
    height = round(math.dist(p1, p2), 2)

    ax.text(*mid_top, f"{width}", color='red', fontsize=12, ha='center', va='bottom', backgroundcolor='white')
    ax.text(*mid_right, f"{height}", color='red', fontsize=12, ha='left', va='center', rotation=90, backgroundcolor='white')

    ax.axis('equal')
    ax.legend()
    return fig

def export_pdf(points, rect, filename="rectangle_englobant.pdf"):
    fig, ax = plt.subplots()
    shape_poly = Polygon(points)
    x, y = shape_poly.exterior.xy
    ax.fill(x, y, alpha=0.5)

    rect_poly = Polygon(rect)
    x_rect, y_rect = rect_poly.exterior.xy
    ax.plot(x_rect, y_rect, 'r--')

    ax.axis('equal')
    plt.axis('off')

    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(tmpfile.name, bbox_inches='tight')
    plt.close(fig)

    pdf_path = os.path.join(tempfile.gettempdir(), filename)
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width_pdf, height_pdf = letter

    c.drawString(100, height_pdf - 50, "Rectangle englobant de la forme")
    rect_width = round(math.dist(rect[0], rect[1]), 2)
    rect_height = round(math.dist(rect[1], rect[2]), 2)
    c.drawString(100, height_pdf - 70, f"Largeur : {rect_width}")
    c.drawString(100, height_pdf - 90, f"Hauteur : {rect_height}")

    c.drawImage(tmpfile.name, 100, 300, width=400, preserveAspectRatio=True)
    c.save()

    os.unlink(tmpfile.name)
    return pdf_path

def export_quadrilatere_to_dxf(points, filename="quadrilatere.dxf"):
    """
    Exporte les points d'un quadrilatère vers un fichier DXF.
    Les points doivent être dans l'ordre [A, B, C, D].
    """
    doc = ezdxf.new()
    msp = doc.modelspace()

    # Fermer la boucle : A→B→C→D→A
    ordered_points = points + [points[0]]
    for i in range(len(ordered_points) - 1):
        msp.add_line(ordered_points[i], ordered_points[i + 1])

    # Créer un fichier temporaire et retourner le chemin
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    doc.saveas(temp_path)
    return temp_path

def main():
    st.title("🔺 Dessin forme cintrée")

    forme = st.selectbox("Choisissez une forme :", [
        "Rectangle avec cintre supérieur"
    ])

    if forme == "Rectangle avec cintre supérieur":
        largeur = st.number_input("Largeur de la base", value=1000, min_value=1)
        hg = st.number_input("Hauteur gauche", value=600, min_value=0)
        hd = st.number_input("Hauteur droite", value=1000, min_value=0)
        fleche = st.number_input("Flèche du cintre", value=50, min_value=0)
        points = rectangle_cintre_points(largeur, hg, hd, fleche)

        rect = minimum_bounding_rectangle(points)

        rect_width = round(math.dist(rect[0], rect[1]), 2)
        rect_height = round(math.dist(rect[1], rect[2]), 2)

        st.success("📏 Dimensions du rectangle englobant :")
        st.markdown(f"**Largeur** : {rect_width} mm")
        st.markdown(f"**Hauteur** : {rect_height} mm")

        fig = draw_shape_and_rectangle(points, rect)
        st.pyplot(fig)

        if st.button("📄 Exporter en PDF"):
            pdf_path = export_pdf(points, rect)
            with open(pdf_path, "rb") as f:
                st.download_button("Télécharger le PDF", f, file_name="rectangle_englobant.pdf")

        # Eport DXF
        if st.button("📐 Exporter en DXF"):
            dxf_path = export_quadrilatere_to_dxf(points, "quadrilatere_export.dxf")
            with open(dxf_path, "rb") as f:
                st.download_button(
                    label="📥 Télécharger le fichier DXF",
                    data=f,
                    file_name="quadrilatere.dxf",
                    mime="application/dxf"
                )

if __name__ == "__main__":
    main()
