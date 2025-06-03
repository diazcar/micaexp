from plotly import graph_objects as go


def make_corr_matrix(graph_data, station_name=None):
    # if station_name rename column station to station_name
    if station_name and "station" in graph_data.columns:
        graph_data = graph_data.rename(columns={"station": station_name})
    # Calculate the correlation matrix
    corr_matrix = graph_data.corr()
   
    fig_corr = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale="PiYG",
            zmin=-1,
            zmax=1,
            colorbar=dict(title="Correlation"),
        )
    )
    fig_corr.update_layout(
        title="Matrice de corrélation",
        title_x=0.5,
        margin=dict(t=60, b=40, l=0, r=0),
        xaxis=dict(
            tickangle=45,
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,
            zeroline=False,
        ),
        yaxis=dict(
            autorange="reversed",
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,
            zeroline=False,
        ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig_corr
