import requests
import math
import numpy as np
import matplotlib.gridspec as gridspec
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
import streamlit as st
from mplsoccer.pitch import Pitch
from mplsoccer import arrowhead_marker


# === FUNCIONES DE DIBUJO DEL CAMPO ===
def draw_pitch_mplsoccer(ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    pitch = Pitch(pitch_color='grass', line_color='white', stripe=True)
    pitch.draw(ax=ax)
    return ax

# === FUNCIONES DE EVENTOS ===
def mostrar_pases(df, player_name, equipo_seleccionado):
    if player_name == "TOTAL":
        return df[(df['type.name'] == 'Pass') & 
                  (df['pass.end_location'].notnull()) & 
                  (df['team.name'] == equipo_seleccionado)]
    else:
        return df[(df['type.name'] == 'Pass') & 
                  (df['player.name'] == player_name) & 
                  (df['pass.end_location'].notnull()) &
                  (df['team.name'] == equipo_seleccionado)]

def mostrar_tiros(df, player_name, equipo_seleccionado):
    if player_name == "TOTAL":
        return df[(df['type.name'] == 'Shot') & 
                  (df['team.name'] == equipo_seleccionado)]
    else:
        return df[(df['type.name'] == 'Shot') & 
                  (df['player.name'] == player_name) & 
                  (df['team.name'] == equipo_seleccionado)]

def mostrar_recuperaciones(df, player_name, equipo_seleccionado):
    if player_name == "TOTAL":
        return df[(df['type.name'] == 'Ball Recovery') & 
                  (df['team.name'] == equipo_seleccionado)]
    else:
        return df[(df['type.name'] == 'Ball Recovery') & 
                  (df['player.name'] == player_name) & 
                  (df['team.name'] == equipo_seleccionado)]

def mostrar_perdidas(df, player_name, equipo_seleccionado):
    # Se consideran las pérdidas de balón como pases con resultado distinto a 'Complete'
    if player_name == "TOTAL":
        return df[(df['type.name'] == 'Pass') &
                  (df['pass.end_location'].notnull()) &
                  (df['pass.outcome.name'].notnull()) &
                  (df['pass.outcome.name'] != 'Complete') &
                  (df['team.name'] == equipo_seleccionado)]
    else:
        return df[(df['type.name'] == 'Pass') &
                  (df['player.name'] == player_name) &
                  (df['pass.end_location'].notnull()) &
                  (df['pass.outcome.name'].notnull()) &
                  (df['pass.outcome.name'] != 'Complete') &
                  (df['team.name'] == equipo_seleccionado)]

def mostrar_faltas_cometidas(df, player_name, equipo_seleccionado):
    if player_name == "TOTAL":
        return df[(df['type.name'] == 'Foul Committed') & 
                  (df['team.name'] == equipo_seleccionado)]
    else:
        return df[(df['type.name'] == 'Foul Committed') & 
                  (df['player.name'] == player_name) & 
                  (df['team.name'] == equipo_seleccionado)]

def mostrar_faltas_recibidas(df, player_name, equipo_seleccionado):
    if player_name == "TOTAL":
        return df[(df['type.name'] == 'Foul Won') & 
                  (df['team.name'] == equipo_seleccionado)]
    else:
        return df[(df['type.name'] == 'Foul Won') & 
                  (df['player.name'] == player_name) & 
                  (df['team.name'] == equipo_seleccionado)]

def dibujar_eventos(ax, eventos, tipo):
    for _, row in eventos.iterrows():
        x_start, y_start = row['location']
        if tipo == "Pass":
            x_end, y_end = row['pass.end_location'][:2]
            outcome = row.get('pass.outcome.name')
            color = 'royalblue' if pd.isna(outcome) or outcome == 'Complete' else 'red'
            ax.annotate('', xy=(x_end, y_end), xytext=(x_start, y_start),
                        arrowprops=dict(arrowstyle='->', color=color, lw=2))
        elif tipo == "Shot":
            x_end, y_end = row['shot.end_location'][:2]
            outcome = row.get('shot.outcome.name')
            color = 'green' if pd.isna(outcome) or outcome == 'Goal' else 'orange'
            # Usamos arrowhead_marker como marcador para el tiro
            ax.scatter(x_end, y_end, color=color, s=100, marker=arrowhead_marker, zorder=5)
        elif tipo == "Ball Recovery":
            x_end, y_end = row['location']
            ax.scatter(x_end, y_end, color='green', s=150, marker='X', zorder=5)
        elif tipo == "Ball Loss":
            x_end, y_end = row['pass.end_location'][:2]
            ax.annotate('', xy=(x_end, y_end), xytext=(x_start, y_start),
                        arrowprops=dict(arrowstyle='->', color='black', lw=2, linestyle='dashed'))

# === TODOS LOS JUGADORES ===
def obtener_jugadores(lineup):
    jugadores = []
    for player in lineup:
        jugadores.append((player.get('jersey_number', '?'),
                          player.get('player_name'),
                          [pos.get('position') for pos in player.get("positions", [])]))
    return jugadores

# === Buscar equipo y posición ===
def buscar_info_jugador(jugador, lineup_local, lineup_visitante, home_team_name, away_team_name):
    for player in lineup_local:
        if player['player_name'] == jugador:
            for pos in player.get("positions", []):
                if pos.get("start_reason") == "Starting XI":
                    return home_team_name, pos.get('position'), player.get('jersey_number')
    for player in lineup_visitante:
        if player['player_name'] == jugador:
            for pos in player.get("positions", []):
                if pos.get("start_reason") == "Starting XI":
                    return away_team_name, pos.get('position'), player.get('jersey_number')
    return 'Desconocido', 'Sin posición', '?'

# === INTERFAZ STREAMLIT ===
st.set_page_config(layout="wide")

# === Cargar archivos ===
events_folder_api_url = "https://api.github.com/repos/statsbomb/open-data/contents/data/events"
events_response = requests.get(events_folder_api_url)

if events_response.status_code == 200:
    events_files = sorted([
        file["name"] for file in events_response.json()
        if file["name"].endswith(".json")
    ])
else:
    st.error("No se pudieron cargar los archivos de eventos.")
    st.stop()

# Paginación
files_per_page = 10
total_pages = math.ceil(len(events_files) / files_per_page)
selected_page = st.number_input("Página de partidos", min_value=1, max_value=total_pages, value=1, step=1)

# Mostrar solo los archivos de la página actual
start_idx = (selected_page - 1) * files_per_page
end_idx = start_idx + files_per_page
files_on_page = events_files[start_idx:end_idx]

# Función para obtener el título del partido
@st.cache_data(show_spinner=False)
def obtener_titulo_partido(filename):
    base_raw_url = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
    try:
        # Obtener nombres de equipos desde la alineación
        lineups_url = f"{base_raw_url}/lineups/{filename}"
        lineups_data = requests.get(lineups_url).json()
        home_team = lineups_data[0]['team_name']
        away_team = lineups_data[1]['team_name']

        # Obtener datos de eventos para calcular el marcador
        events_url = f"{base_raw_url}/events/{filename}"
        events_data = requests.get(events_url).json()
        goles_local = len([
            e for e in events_data 
            if e.get('type', {}).get('name') == 'Shot' 
            and e.get('team', {}).get('name') == home_team 
            and e.get('shot', {}).get('outcome', {}).get('name') == 'Goal'
        ])
        goles_away = len([
            e for e in events_data 
            if e.get('type', {}).get('name') == 'Shot' 
            and e.get('team', {}).get('name') == away_team 
            and e.get('shot', {}).get('outcome', {}).get('name') == 'Goal'
        ])

        return f"{home_team} {goles_local} - {goles_away} {away_team}"
    except Exception as e:
        return f"Partido desconocido ({filename})"

# Selectbox para seleccionar partido
selected_game = st.selectbox("Selecciona un partido", files_on_page, format_func=obtener_titulo_partido)

# Construcción de URLs
base_raw_url = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
events_url = f"{base_raw_url}/events/{selected_game}"
lineups_url = f"{base_raw_url}/lineups/{selected_game}"

# Carga de datos
try:
    events_data = requests.get(events_url).json()
    lineups_data = requests.get(lineups_url).json()

    df_data = pd.json_normalize(events_data)

    home_lineup = lineups_data[0]['lineup']
    away_lineup = lineups_data[1]['lineup']

    home_team_name = lineups_data[0]['team_name']
    away_team_name = lineups_data[1]['team_name']
except Exception as e:
    st.error("Ocurrió un error al cargar los datos del partido.")
    st.stop()

# Obtener todos los jugadores (no solo titulares)
jugadores_local = obtener_jugadores(home_lineup)
jugadores_visitante = obtener_jugadores(away_lineup)

# === Calcular marcador ===
goles_local = len(df_data[(df_data['type.name'] == 'Shot') & 
                          (df_data['team.name'] == home_team_name) & 
                          (df_data['shot.outcome.name'] == 'Goal')])

goles_visitante = len(df_data[(df_data['type.name'] == 'Shot') & 
                               (df_data['team.name'] == away_team_name) & 
                               (df_data['shot.outcome.name'] == 'Goal')])

# Mostrar el título con los nombres de los equipos y el marcador
st.title(f"{home_team_name} {goles_local} - {goles_visitante} {away_team_name}")

def obtener_suplentes(lineup):
    # Precompute a mapping from substitution-off minute to the player being substituted out.
    subs_off = {}
    for player in lineup:
        positions = player.get("positions", [])
        for p in positions:
            # If the player's position ended because of a substitution off, record the minute.
            if p.get("end_reason", "").startswith("Substitution - Off"):
                minute = p.get("to")
                if minute:
                    # Use the player's name as the one being replaced.
                    nombre = player.get('player_nickname', '') or player.get('player_name', '')
                    subs_off[minute] = (player.get('jersey_number', '?'), nombre)

    suplentes = []
    for player in lineup:
        positions = player.get("positions", [])
        # Consider the player as a substitute only if no role is "Starting XI"
        if any(p.get("start_reason") == "Starting XI" for p in positions):
            continue
        dorsal = player.get('jersey_number', '?')
        nombre = player.get('player_nickname', '') or player.get('player_name', '')
        # Buscar la entrada con "Substitution - On (Tactical)" para obtener el minuto
        sub_minutes = [p.get("from") for p in positions if p.get("start_reason") == "Substitution - On (Tactical)"]
        minuto = sub_minutes[0] if sub_minutes else '-'
        # Buscar a quién sustituyó usando el minuto de entrada
        por_quien = subs_off.get(minuto, ('-', '-'))[1] if minuto in subs_off else '-'
        suplentes.append((dorsal, nombre, minuto, por_quien))
    return suplentes

position_map_home = {
    'Goalkeeper': (5, 40),  # Gk
    'Right Back': (18, 12),  # RB
    'Right Center Back': (18, 28),  # RCB
    'Center Back': (18, 40),  # CB
    'Left Center Back': (18, 52),  # LCB
    'Left Back': (18, 68),  # LB
    'Right Wing Back': (25, 12),  # RWB
    'Left Wing Back': (25, 68),  # LWB
    'Right Defensive Midfield': (35, 28),  # RDM
    'Center Defensive Midfield': (30, 40),  # CDM
    'Left Defensive Midfield': (35, 55),  # LDM
    'Right Midfield': (45, 15),  # RM
    'Right Center Midfield': (45, 30),  # RCM
    'Center Midfield': (45, 40),  # CM
    'Left Center Midfield': (45, 52),  # LCM
    'Left Midfield': (45, 65),  # LM
    'Right Wing': (55, 15),  # RW
    'Right Attacking Midfield': (55, 30),  # RAM
    'Center Attacking Midfield': (55, 40),  # CAM
    'Left Attacking Midfield': (55, 55),  # LAM
    'Left Wing': (55, 65),  # LW
    'Right Center Forward': (55, 30),  # RCF
    'Striker': (55, 40),  # ST
    'Center Forward': (55, 40),  # ST
    'Left Center Forward': (55, 55),  # LCF
    'Secondary Striker': (55, 50)  # SS
}


position_map_away = {
    'Goalkeeper': (115, 40),  # Gk
    'Right Back': (102, 15),  # RB
    'Right Center Back': (102, 25),  # RCB
    'Center Back': (102, 40),  # CB
    'Left Center Back': (102, 55),  # LCB
    'Left Back': (102, 65),  # LB
    'Right Wing Back': (95, 15),  # RWB
    'Left Wing Back': (95, 65),  # LWB
    'Right Defensive Midfield': (80, 30),  # RDM
    'Center Defensive Midfield': (85, 40),  # CDM
    'Left Defensive Midfield': (80, 50),  # LDM
    'Right Midfield': (70, 15),  # RM
    'Right Center Midfield': (70, 30),  # RCM
    'Center Midfield': (70, 40),  # CM
    'Left Center Midfield': (70, 50),  # LCM
    'Left Midfield': (70, 60),  # LM
    'Right Wing': (60, 15),  # RW
    'Right Attacking Midfield': (60, 30),  # RAM
    'Center Attacking Midfield': (60, 40),  # CAM
    'Left Attacking Midfield': (60, 50),  # LAM
    'Left Wing': (60, 60),  # LW
    'Right Center Forward': (65, 30),  # RCF
    'Striker': (65, 40),  # ST
    'Center Forward': (65, 40),  # ST
    'Left Center Forward': (65, 50),  # LCF
    'Secondary Striker': (65, 45)  # SS
}


def dibujar_titulares_en_campo_horizontal_ax(ax, home_lineup, away_lineup):
    draw_pitch_mplsoccer(ax)
    # Dibujar titulares Equipo Local (azul)
    for player in home_lineup:
        positions = player.get("positions", [])
        titulares = [p for p in positions if p.get("start_reason") == "Starting XI"]
        if not titulares:
            continue
        dorsal = player.get('jersey_number', '?')
        nombre = player.get('player_nickname', '') or player.get('player_name', '')
        pos_name = titulares[0].get('position', 'Desconocido')
        coord = position_map_home.get(pos_name, (60, 40))
        # Dibuja el dorsal centrado en el círculo
        ax.text(coord[0], coord[1], str(dorsal),
                fontsize=8, ha='center', va='center',
                bbox=dict(facecolor='lightblue', edgecolor='blue', boxstyle='circle'))
        # Dibuja el nombre justo debajo del dorsal (desplazado hacia abajo)
        ax.text(coord[0], coord[1] + 4, nombre,
                fontsize=8, ha='center', va='bottom', color='blue')
    # Dibujar titulares Equipo Visitante (rojo)
    for player in away_lineup:
        positions = player.get("positions", [])
        titulares = [p for p in positions if p.get("start_reason") == "Starting XI"]
        if not titulares:
            continue
        dorsal = player.get('jersey_number', '?')
        nombre = player.get('player_nickname', '') or player.get('player_name', '')
        pos_name = titulares[0].get('position', 'Desconocido')
        coord = position_map_away.get(pos_name, (60, 40))
        ax.text(coord[0], coord[1], str(dorsal),
                fontsize=8, ha='center', va='center',
                bbox=dict(facecolor='lightcoral', edgecolor='red', boxstyle='circle'))
        ax.text(coord[0], coord[1] + 4, nombre,
                fontsize=8, ha='center', va='bottom', color='red')

fig_pitch, ax_pitch = plt.subplots(figsize=(12, 8))
draw_pitch_mplsoccer(ax_pitch)
dibujar_titulares_en_campo_horizontal_ax(ax_pitch, home_lineup, away_lineup)

# Mostrar en Streamlit
st.write("### Alineación")
st.pyplot(fig_pitch)

# Obtener los suplentes para cada equipo
suplentes_local = obtener_suplentes(home_lineup)  
suplentes_away = obtener_suplentes(away_lineup)

# Convertir a DataFrame para usar st.table
columns = ["Nº", "Jugador", "Min", "Por quién"]
df_suplentes_local = pd.DataFrame(suplentes_local, columns=columns) if suplentes_local else pd.DataFrame(columns=columns)
df_suplentes_away = pd.DataFrame(suplentes_away, columns=columns) if suplentes_away else pd.DataFrame(columns=columns)

# Crear dos columnas para las tablas de suplentes
col1, col2 = st.columns(2)

# Mostrar las tablas dentro de las columnas
with col1:
    st.write(f"### Suplentes {home_team_name}")
    if not df_suplentes_local.empty:
        st.table(df_suplentes_local)
    else:
        st.write("Sin suplentes")

with col2:
    st.write(f"### Suplentes {away_team_name}")
    if not df_suplentes_away.empty:
        st.table(df_suplentes_away)
    else:
        st.write("Sin suplentes")

# Selección de equipo
equipo_seleccionado = st.selectbox("Selecciona un equipo", [home_team_name, away_team_name])

# Obtener los jugadores según el equipo seleccionado
if equipo_seleccionado == home_team_name:
    jugadores = [name for _, name, _ in jugadores_local]
else:
    jugadores = [name for _, name, _ in jugadores_visitante]

# Selección de jugador
jugador_seleccionado = st.selectbox("Selecciona un jugador", ["TOTAL"] + jugadores)

# Buscar equipo y posición del jugador
equipo, posicion, dorsal = buscar_info_jugador(jugador_seleccionado, home_lineup, away_lineup, home_team_name, away_team_name)


# === FUNCIONES PARA CONTAR EVENTOS ===
def contar_pases_acertados_errados(df, jugador):
    if jugador == "TOTAL":
        pases_jugador = df[(df['type.name'] == 'Pass') & (df['pass.end_location'].notnull()) & (df['team.name'] == equipo_seleccionado)]
    else:
        pases_jugador = mostrar_pases(df, jugador, equipo_seleccionado)
    
    # Dividir los eventos en primera y segunda parte
    primera_parte = pases_jugador[pases_jugador['minute'] <= 45]
    segunda_parte = pases_jugador[pases_jugador['minute'] > 45]
    
    # Pases completados
    pases_acertados_primera = primera_parte[primera_parte['pass.outcome.name'].isna() | (primera_parte['pass.outcome.name'] == 'Complete')]
    pases_errados_primera = primera_parte[~primera_parte['pass.outcome.name'].isna() & (primera_parte['pass.outcome.name'] != 'Complete')]
    
    pases_acertados_segunda = segunda_parte[segunda_parte['pass.outcome.name'].isna() | (segunda_parte['pass.outcome.name'] == 'Complete')]
    pases_errados_segunda = segunda_parte[~segunda_parte['pass.outcome.name'].isna() & (segunda_parte['pass.outcome.name'] != 'Complete')]
    
    # Totales
    pases_acertados_totales = len(pases_acertados_primera) + len(pases_acertados_segunda)
    pases_errados_totales = len(pases_errados_primera) + len(pases_errados_segunda)

    return (len(pases_acertados_primera), len(pases_errados_primera), 
            len(pases_acertados_segunda), len(pases_errados_segunda),
            pases_acertados_totales, pases_errados_totales)

def contar_tiros(df, jugador):
    if jugador == "TOTAL":
        tiros_jugador = df[(df['type.name'] == 'Shot') & (df['team.name'] == equipo_seleccionado)]
    else:
        tiros_jugador = mostrar_tiros(df, jugador, equipo_seleccionado)

    tiros_a_puerta = tiros_jugador[tiros_jugador['shot.outcome.name'] == 'Goal']
    tiros_a_puerta = pd.concat([tiros_a_puerta, tiros_jugador[tiros_jugador['shot.outcome.name'] == 'Saved']])
    
    tiros_fuera = tiros_jugador[tiros_jugador['shot.outcome.name'] == 'Off Target']
    
    total_tiros = len(tiros_jugador)
    total_puerta = len(tiros_a_puerta)
    total_fuera = len(tiros_fuera)
    
    return total_tiros, total_puerta, total_fuera

# Mostrar la tabla de pases en formato horizontal con porcentajes
def mostrar_tabla_pases(df, jugador):
    pases_primera, errados_primera, pases_segunda, errados_segunda, pases_totales, errados_totales = contar_pases_acertados_errados(df, jugador)
    
    # Filtrar pases cortos y largos
    pases_jugador = mostrar_pases(df, jugador, equipo_seleccionado)
    pases_cortos = pases_jugador[pases_jugador['pass.length'] <= 30]
    pases_largos = pases_jugador[pases_jugador['pass.length'] > 30]

    # Contar pases cortos y largos acertados y errados
    cortos_acertados = len(pases_cortos[pases_cortos['pass.outcome.name'].isna() | (pases_cortos['pass.outcome.name'] == 'Complete')])
    cortos_errados = len(pases_cortos[~pases_cortos['pass.outcome.name'].isna() & (pases_cortos['pass.outcome.name'] != 'Complete')])
    largos_acertados = len(pases_largos[pases_largos['pass.outcome.name'].isna() | (pases_largos['pass.outcome.name'] == 'Complete')])
    largos_errados = len(pases_largos[~pases_largos['pass.outcome.name'].isna() & (pases_largos['pass.outcome.name'] != 'Complete')])

    # Calcular totales y porcentajes
    total_pases_primera = pases_primera + errados_primera
    total_pases_segunda = pases_segunda + errados_segunda
    total_pases_totales = pases_totales + errados_totales
    total_cortos = cortos_acertados + cortos_errados
    total_largos = largos_acertados + largos_errados

    # Evitar división por cero
    porcentaje = lambda x, total: f"{x} ({(x / total * 100):.1f}%)" if total > 0 else f"{x} (0%)"

    # Crear un dataframe con los resultados
    data = {
        '': ['Total', '1ra Parte', '2da Parte'],
        'Pases Acertados': [
            porcentaje(pases_totales, total_pases_totales),
            porcentaje(pases_primera, total_pases_primera),
            porcentaje(pases_segunda, total_pases_segunda)
        ],
        'Pases Errados': [
            porcentaje(errados_totales, total_pases_totales),
            porcentaje(errados_primera, total_pases_primera),
            porcentaje(errados_segunda, total_pases_segunda)
        ],
        'Cortos Acertados': [
            porcentaje(cortos_acertados, total_cortos),
            porcentaje(len(pases_cortos[(pases_cortos['minute'] <= 45) & (pases_cortos['pass.outcome.name'].isna() | (pases_cortos['pass.outcome.name'] == 'Complete'))]), len(pases_cortos[pases_cortos['minute'] <= 45])),
            porcentaje(len(pases_cortos[(pases_cortos['minute'] > 45) & (pases_cortos['pass.outcome.name'].isna() | (pases_cortos['pass.outcome.name'] == 'Complete'))]), len(pases_cortos[pases_cortos['minute'] > 45]))
        ],
        'Cortos Errados': [
            porcentaje(cortos_errados, total_cortos),
            porcentaje(len(pases_cortos[(pases_cortos['minute'] <= 45) & (~pases_cortos['pass.outcome.name'].isna() & (pases_cortos['pass.outcome.name'] != 'Complete'))]), len(pases_cortos[pases_cortos['minute'] <= 45])),
            porcentaje(len(pases_cortos[(pases_cortos['minute'] > 45) & (~pases_cortos['pass.outcome.name'].isna() & (pases_cortos['pass.outcome.name'] != 'Complete'))]), len(pases_cortos[pases_cortos['minute'] > 45]))
        ],
        'Largos Acertados': [
            porcentaje(largos_acertados, total_largos),
            porcentaje(len(pases_largos[(pases_largos['minute'] <= 45) & (pases_largos['pass.outcome.name'].isna() | (pases_largos['pass.outcome.name'] == 'Complete'))]), len(pases_largos[pases_largos['minute'] <= 45])),
            porcentaje(len(pases_largos[(pases_largos['minute'] > 45) & (pases_largos['pass.outcome.name'].isna() | (pases_largos['pass.outcome.name'] == 'Complete'))]), len(pases_largos[pases_largos['minute'] > 45]))
        ],
        'Largos Errados': [
            porcentaje(largos_errados, total_largos),
            porcentaje(len(pases_largos[(pases_largos['minute'] <= 45) & (~pases_largos['pass.outcome.name'].isna() & (pases_largos['pass.outcome.name'] != 'Complete'))]), len(pases_largos[pases_largos['minute'] <= 45])),
            porcentaje(len(pases_largos[(pases_largos['minute'] > 45) & (~pases_largos['pass.outcome.name'].isna() & (pases_largos['pass.outcome.name'] != 'Complete'))]), len(pases_largos[pases_largos['minute'] > 45]))
        ]
    }
    
    return pd.DataFrame(data)

def mostrar_tabla_tiros(df, jugador):
    total_tiros, total_puerta, total_fuera = contar_tiros(df, jugador)

    tiros_jugador = mostrar_tiros(df, jugador, equipo_seleccionado)
    tiros_primera = tiros_jugador[tiros_jugador['minute'] <= 45]
    tiros_segunda = tiros_jugador[tiros_jugador['minute'] > 45]

    puerta_primera = len(tiros_primera[tiros_primera['shot.outcome.name'].isin(['Goal', 'Saved'])])
    fuera_primera = len(tiros_primera[tiros_primera['shot.outcome.name'] == 'Off Target'])

    puerta_segunda = len(tiros_segunda[tiros_segunda['shot.outcome.name'].isin(['Goal', 'Saved'])])
    fuera_segunda = len(tiros_segunda[tiros_segunda['shot.outcome.name'] == 'Off Target'])

    data = {
        '': ['Total', '1ra Parte', '2da Parte'],
        'Tiros a puerta': [total_puerta, puerta_primera, puerta_segunda],
        'Tiros fuera': [total_fuera, fuera_primera, fuera_segunda],
    }

    return pd.DataFrame(data)

def mostrar_tabla_recuperaciones(df, jugador):
    # Obtener los eventos de recuperaciones
    recov_jugador = mostrar_recuperaciones(df, jugador, equipo_seleccionado)
    
    # Dividir por partes
    recov_total = recov_jugador
    recov_primera = recov_jugador[recov_jugador['minute'] <= 45]
    recov_segunda = recov_jugador[recov_jugador['minute'] > 45]
    
    # Definir función para determinar campo propio vs contrario
    if equipo_seleccionado == home_team_name:
        is_prop = lambda loc: loc[0] < 60
        is_contra = lambda loc: loc[0] >= 60
    else:
        is_prop = lambda loc: loc[0] > 60
        is_contra = lambda loc: loc[0] <= 60

    # Función auxiliar para filtrar según condición en la localización
    def filtrar_por_campo(df_events, cond):
        return df_events[df_events['location'].apply(lambda loc: cond(loc))]

    # Totales
    total_prop = len(filtrar_por_campo(recov_total, is_prop))
    total_contra = len(filtrar_por_campo(recov_total, is_contra))
    
    # Primera parte
    primera_prop = len(filtrar_por_campo(recov_primera, is_prop))
    primera_contra = len(filtrar_por_campo(recov_primera, is_contra))
    
    # Segunda parte
    segunda_prop = len(filtrar_por_campo(recov_segunda, is_prop))
    segunda_contra = len(filtrar_por_campo(recov_segunda, is_contra))

    # Crear la tabla (DataFrame)
    data = {
        '': ['Total', '1ra Parte', '2da Parte'],
        'Campo Propio': [total_prop, primera_prop, segunda_prop],
        'Campo Contrario': [total_contra, primera_contra, segunda_contra]
    }
    return pd.DataFrame(data)

def mostrar_tabla_falta_cometidas(df, jugador):
    # Obtener los eventos de faltas cometidas
    falta_jugador = mostrar_faltas_cometidas(df, jugador, equipo_seleccionado)
    
    # Dividir por partes
    falta_total = falta_jugador
    falta_primera = falta_jugador[falta_jugador['minute'] <= 45]
    falta_segunda = falta_jugador[falta_jugador['minute'] > 45]

    # Totales
    total_faltas = len(falta_total)
    
    # Primera parte
    primera_faltas = len(falta_primera)
    
    # Segunda parte
    segunda_faltas = len(falta_segunda)

    # Crear la tabla (DataFrame)
    data = {
        '': ['Total', '1ra Parte', '2da Parte'],
        'Faltas Cometidas': [total_faltas, primera_faltas, segunda_faltas]
    }
    return pd.DataFrame(data)

def mostrar_tabla_falta_recibidas(df, jugador):
    # Obtener los eventos de faltas recibidas
    falta_jugador = mostrar_faltas_recibidas(df, jugador, equipo_seleccionado)
    
    # Dividir por partes
    falta_total = falta_jugador
    falta_primera = falta_jugador[falta_jugador['minute'] <= 45]
    falta_segunda = falta_jugador[falta_jugador['minute'] > 45]

    # Totales
    total_faltas = len(falta_total)
    
    # Primera parte
    primera_faltas = len(falta_primera)
    
    # Segunda parte
    segunda_faltas = len(falta_segunda)

    # Crear la tabla (DataFrame)
    data = {
        '': ['Total', '1ra Parte', '2da Parte'],
        'Faltas Recibidas': [total_faltas, primera_faltas, segunda_faltas]
    }
    return pd.DataFrame(data)

# Mostrar la tabla de pases y tiros
st.write("### Pases Realizados")
tabla_pases = mostrar_tabla_pases(df_data, jugador_seleccionado)
st.dataframe(tabla_pases)

st.write("### Tiros Realizados")
tabla_tiros = mostrar_tabla_tiros(df_data, jugador_seleccionado)
st.dataframe(tabla_tiros)

st.write("### Recuperaciones de Balón")
tabla_recup = mostrar_tabla_recuperaciones(df_data, jugador_seleccionado)
st.dataframe(tabla_recup)

st.write("### Faltas Cometidas")
tabla_faltas = mostrar_tabla_falta_cometidas(df_data, jugador_seleccionado)
st.dataframe(tabla_faltas)

st.write("### Faltas Recibidas")
tabla_faltas_recibidas = mostrar_tabla_falta_recibidas(df_data, jugador_seleccionado)
st.dataframe(tabla_faltas_recibidas)


evento_tipo = st.selectbox("Selecciona el tipo de evento a visualizar", ["Pases", "Tiros", "Recuperaciones", "Perdidas"])

# Visualización de eventos
fig, ax = plt.subplots(figsize=(12, 8))
draw_pitch_mplsoccer(ax)

# Dibujar posición inicial
if equipo == home_team_name:
    pos_coords = position_map_home.get(posicion)
else:
    pos_coords = position_map_away.get(posicion)

# Filtrar los eventos según el tipo
if evento_tipo == "Pases":
    eventos = mostrar_pases(df_data, jugador_seleccionado, equipo_seleccionado)
elif evento_tipo == "Tiros":
    eventos = mostrar_tiros(df_data, jugador_seleccionado, equipo_seleccionado)
elif evento_tipo == "Recuperaciones":
    eventos = mostrar_recuperaciones(df_data, jugador_seleccionado, equipo_seleccionado)
elif evento_tipo == "Perdidas":
    eventos = mostrar_perdidas(df_data, jugador_seleccionado, equipo_seleccionado)

# Dibujar eventos
dibujar_eventos(ax, eventos, evento_tipo)
st.pyplot(fig)
