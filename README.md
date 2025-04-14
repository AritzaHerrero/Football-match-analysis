# Football Match Analysis

Este proyecto es una aplicación interactiva desarrollada con **Streamlit** para analizar partidos de fútbol utilizando datos abiertos de **StatsBomb**. La aplicación permite visualizar eventos como pases, tiros, recuperaciones, pérdidas de balón, faltas cometidas y recibidas, así como alineaciones y suplentes de los equipos.

## Funcionalidades

1. **Visualización del campo de juego**:
   - Se utiliza la librería `mplsoccer` para dibujar el campo de fútbol y representar eventos sobre él.

2. **Carga de datos**:
   - Los datos de eventos y alineaciones se obtienen directamente desde el repositorio de datos abiertos de StatsBomb.

3. **Análisis de eventos**:
   - **Pases**: Visualización de pases acertados y errados, diferenciados por primera y segunda parte.
   - **Tiros**: Análisis de tiros a puerta, fuera y goles.
   - **Recuperaciones**: Recuperaciones de balón en campo propio y contrario.
   - **Pérdidas**: Pérdidas de balón clasificadas como pases no completados.
   - **Faltas**: Faltas cometidas y recibidas.

4. **Alineaciones y suplentes**:
   - Visualización de los jugadores titulares en el campo.
   - Listado de suplentes con información sobre el minuto de entrada y a quién sustituyeron.

5. **Interfaz interactiva**:
   - Selección de partidos, equipos y jugadores para personalizar el análisis.
   - Visualización de eventos específicos en el campo.

## Requisitos

- Python 3.8 o superior.
- Librerías necesarias:
  - `streamlit`
  - `mplsoccer`
  - `matplotlib`
  - `pandas`
  - `numpy`
  - `requests`

## Como ejecutar la aplicación
streamlit run main.py

## Estructura del código

### Dibujo del campo:
- draw_pitch_mplsoccer(ax): Dibuja el campo de fútbol utilizando mplsoccer.

### Eventos:
- mostrar_pases(df, player_name, equipo_seleccionado): Filtra los pases realizados por un jugador o equipo.
- mostrar_tiros(df, player_name, equipo_seleccionado): Filtra los tiros realizados.
- mostrar_recuperaciones(df, player_name, equipo_seleccionado): Filtra las recuperaciones de balón.
- mostrar_perdidas(df, player_name, equipo_seleccionado): Filtra las pérdidas de balón.
- mostrar_faltas_cometidas(df, player_name, equipo_seleccionado): Filtra las faltas cometidas.
- mostrar_faltas_recibidas(df, player_name, equipo_seleccionado): Filtra las faltas recibidas.

### Alineaciones:
- obtener_jugadores(lineup): Obtiene la lista de jugadores de una alineación.
- dibujar_titulares_en_campo_horizontal_ax(ax, home_lineup, away_lineup): Dibuja los jugadores titulares en el campo.

### Tablas de análisis:
- mostrar_tabla_pases(df, jugador): Genera una tabla con estadísticas de pases.
- mostrar_tabla_tiros(df, jugador): Genera una tabla con estadísticas de tiros.
- mostrar_tabla_recuperaciones(df, jugador): Genera una tabla con estadísticas de recuperaciones.
- mostrar_tabla_falta_cometidas(df, jugador): Genera una tabla con estadísticas de faltas cometidas.
- mostrar_tabla_falta_recibidas(df, jugador): Genera una tabla con estadísticas de faltas recibidas.
