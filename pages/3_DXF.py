import streamlit as st
import ezdxf
import numpy as np
import tempfile
import plotly.graph_objects as go

def get_layers(doc):
    msp = doc.modelspace()
    return sorted(set(entity.dxf.layer for entity in msp))

def plot_dxf_interactive(doc, selected_layers):
    msp = doc.modelspace()
    fig = go.Figure()

    for entity in msp:
        if entity.dxf.layer not in selected_layers:
            continue

        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            fig.add_trace(go.Scatter(
                x=[start.x, end.x], y=[start.y, end.y],
                mode='lines',
                line=dict(color='blue'),
                name='LINE',
                showlegend=False
            ))
        elif entity.dxftype() == "CIRCLE":
            center = entity.dxf.center
            radius = entity.dxf.radius
            theta = np.linspace(0, 2*np.pi, 100)
            x = center.x + radius * np.cos(theta)
            y = center.y + radius * np.sin(theta)
            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode='lines',
                line=dict(color='green'),
                name='CIRCLE',
                showlegend=False
            ))
        elif entity.dxftype() == "ARC":
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = np.radians(entity.dxf.start_angle)
            end_angle = np.radians(entity.dxf.end_angle)
            theta = np.linspace(start_angle, end_angle, 100)
            x = center.x + radius * np.cos(theta)
            y = center.y + radius * np.sin(theta)
            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode='lines',
                line=dict(color='red'),
                name='ARC',
                showlegend=False
            ))
        elif entity.dxftype() in ["LWPOLYLINE", "POLYLINE"]:
            try:
                points = entity.get_points()
                points = [p[0:2] for p in points]
            except AttributeError:
                points = [(v.dxf.x, v.dxf.y) for v in entity.vertices()]
            x, y = zip(*points)
            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode='lines',
                line=dict(color='magenta'),
                name='POLYLINE',
                showlegend=False
            ))
        elif entity.dxftype() == "TEXT":
            insert = entity.dxf.insert
            content = entity.dxf.text
            fig.add_trace(go.Scatter(
                x=[insert.x],
                y=[insert.y],
                mode="text",
                text=[content],
                textposition="top right",
                textfont=dict(size=12, color="black"),
                showlegend=False
            ))
        elif entity.dxftype() == "MTEXT":
            insert = entity.dxf.insert
            content = entity.text
            fig.add_trace(go.Scatter(
                x=[insert.x],
                y=[insert.y],
                mode="text",
                text=[content],
                textposition="top right",
                textfont=dict(size=12, color="black"),
                showlegend=False
            ))

    fig.update_layout(
        title="DXF interactif (zoom/pan)",
        xaxis=dict(scaleanchor="y"),
        yaxis=dict(scaleanchor="x"),
        dragmode="pan",
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return fig

def main():
    st.title("📐 Visionneuse DXF interactive (zoom & pan)")

    uploaded_file = st.file_uploader("Chargez un fichier DXF", type=["dxf"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        try:
            doc = ezdxf.readfile(tmp_path)
            layers = get_layers(doc)

            st.markdown("### Calques à afficher")
            selected_layers = st.multiselect("Sélectionnez les calques à afficher :", layers, default=layers)

            if selected_layers:
                fig = plot_dxf_interactive(doc, selected_layers)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Aucun calque sélectionné.")

        except Exception as e:
            st.error(f"Erreur : {e}")

if __name__ == "__main__":
    main()
