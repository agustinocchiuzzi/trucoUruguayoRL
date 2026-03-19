"""
Truco Uruguayo — Interfaz de consola vs RL Agent
Ejecutar: python main.py

Jugador 1: Agente de RL (automático)
Jugador 2: Humano (tú)
"""
 
import os
import random
from Truco import Truco

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')
 
def line(c='─', n=58):
    print(c * n)
 
def header(txt):
    line('═')
    print(f"  {txt}")
    line('═')

def pause():
    input("\n  [ ENTER para continuar ]")
 
PALOS_ES = {"sword": "Espada", "coarse": "Basto", "gold": "Oro", "cup": "Copa"}
 
def fmt_card(card):
    return f"{card.number} de {PALOS_ES.get(card.palo, card.palo)}"

# ─────────────────────────────────────────────
# AGENTE DE RL (SIMPLE/ALEATORIO POR AHORA)
# ─────────────────────────────────────────────

class RLAgent:
    """
    Agente básico de RL que juega como Jugador 1.
    Por ahora toma decisiones aleatorias entre acciones válidas.
    Después se puede entrenar con PPO, A2C, etc.
    """
    def decide_action(self, truco: Truco):
        """
        Retorna una acción válida según el estado del juego.
        Acciones posibles:
        - ('play_card', index): jugar carta
        - ('call_truco', tipo)
        - ('respond_truco', response)
        - ('call_envido', tipo)
        - ('respond_envido', response)
        - ('call_flower', tipo)
        - ('respond_flower', response)
        - ('pass',): pasar
        """
        player = 0  # Agente siempre es jugador 1 (index 0)
        
        # Si hay envido/truco sin responder, responder es prioritario
        if self._should_respond_truco(truco, player):
            return self._respond_to_truco(truco, player)
        
        if self._should_respond_envido(truco, player):
            return self._respond_to_envido(truco, player)
        
        if self._should_respond_flower(truco, player):
            return self._respond_to_flower(truco, player)
        
        # Si es mi turno y no hay respuestas pendientes, puedo jugar o cantar
        if truco.turn == player and not truco.hand_over:
            # Por ahora: 50% jugar, 50% cantar (si hay opciones)
            if random.random() < 0.5 and len(truco.hand_of(player)) > 0:
                # Jugar una carta aleatoria válida
                valid_cards = self._get_valid_card_indices(truco, player)
                if valid_cards:
                    return ('play_card', random.choice(valid_cards))
            
            # Intentar cantar algo
            if not truco.rounds:  # Antes de jugar cartas
                # Cantar envido (solo si yo no tengo flor Y el rival no tiene flor)
                if random.random() < 0.4 and not truco.envido_resolved:
                    env = truco.envido_of(player)
                    rival = truco.rival_of(player)
                    rival_env = truco.envido_of(rival)
                    if env != -1 and rival_env != -1:  # Ni yo ni el rival tenemos flor
                        return ('call_envido', 'envido')
                
                # Cantar flor (solo si tengo flor)
                if random.random() < 0.2 and player in truco.flowers_declared:
                    return ('call_flower', 'la_mia')
            
            # Jugar si no hizo nada anterior
            valid_cards = self._get_valid_card_indices(truco, player)
            if valid_cards:
                return ('play_card', random.choice(valid_cards))
        
        return ('pass',)
    
    def _should_respond_truco(self, truco, player):
        return (
            truco.truco_state in ('truco', 'retruco', 'vale_cuatro') and
            truco.truco_caller != player and
            not truco.truco_resolved
        )
    
    def _should_respond_envido(self, truco, player):
        return (
            truco.envido_state in ('envido', 'real_envido', 'falta_envido') and
            truco.envido_caller != player and
            not truco.envido_resolved
        )
    
    def _should_respond_flower(self, truco, player):
        return (
            truco.flower_state in ('la_mia', 'con_flor_envido', 'contra_flor', 'contra_flor_al_resto') and
            truco.flower_caller != player and
            not truco.flower_resolved and
            len(truco.flowers_declared) > 1
        )
    
    def _respond_to_truco(self, truco, player):
        """Decide cómo responder al truco."""
        # Solo puedo levantar si tengo la palabra
        puede_levantar = (truco.truco_word_holder == player)
        
        # Decisión: 60% quiero, 30% no quiero, 10% subir (solo si puede)
        rnd = random.random()
        
        if rnd < 0.60:
            return ('respond_truco', 'quiero')
        elif rnd < 0.90:
            return ('respond_truco', 'no_quiero')
        else:
            # Subir el truco (solo si tiene la palabra)
            if puede_levantar:
                if truco.truco_state == 'truco':
                    return ('respond_truco', 'retruco')
                elif truco.truco_state == 'retruco':
                    return ('respond_truco', 'vale_cuatro')
                else:
                    # Ya es vale_cuatro, no se puede subir más
                    return ('respond_truco', 'quiero')
            else:
                # No tengo la palabra, debo responder al canto actual
                return ('respond_truco', 'quiero')
    
    def _respond_to_envido(self, truco, player):
        """Decide cómo responder al envido."""
        env = truco.envido_of(player)
        
        # Si tiene flor, no quiero (anula envido)
        if env == -1:
            return ('respond_envido', 'no_quiero')
        
        # Decidir: responder, subir o rechazar
        # 60% quiero, 20% no quiero, 20% subir
        rnd = random.random()
        
        if rnd < 0.60:
            return ('respond_envido', 'quiero')
        elif rnd < 0.80:
            return ('respond_envido', 'no_quiero')
        else:
            # Subir el envido (30% envido, 70% real_envido)
            if truco.envido_state == 'envido':
                if random.random() < 0.7:
                    return ('respond_envido', 'real_envido')
                else:
                    return ('respond_envido', 'falta_envido')
            elif truco.envido_state == 'real_envido':
                return ('respond_envido', 'falta_envido')
            else:
                # Ya es falta_envido, no se puede subir más
                return ('respond_envido', 'quiero')
    
    def _respond_to_flower(self, truco, player):
        """Decide cómo responder a la flor."""
        # Decisión simple: 70% la mía, 30% otra
        if random.random() < 0.7:
            return ('respond_flower', 'la_mia')
        else:
            return ('respond_flower', 'con_flor_envido')
    
    def _get_valid_card_indices(self, truco, player):
        """Retorna índices de cartas válidas para jugar."""
        hand = truco.hand_of(player)
        
        # Si hay respuestas pendientes, no se puede jugar
        if truco._waiting_for_truco_response(player):
            return []
        if truco._waiting_for_flower_response(player):
            return []
        if truco.envido_state and truco.envido_caller != player and not truco.envido_resolved:
            return []
        
        # Retorna todos los índices disponibles
        return list(range(len(hand)))

# ─────────────────────────────────────────────
# INTERFAZ DE USUARIO
# ─────────────────────────────────────────────

def show_state(truco: Truco, msg=""):
    clear()
    header(f"TRUCO URUGUAYO vs RL Agent")

    m = truco
    print(f"\n  📊  {m.score_str()}  (meta: {Truco.POINTS_TO_WIN} pts)")
    print(f"    Mano: {m.player_name(m.mano_player)}")
    print(f"    Muestra: {fmt_card(m.sample)}  (palo: {PALOS_ES.get(m.sample.palo)})")
    
    if m.rounds:
        baza_txt = []
        for i, r in enumerate(m.rounds):
            if r == 1:
                baza_txt.append(f"Baza {i+1}: J1")
            elif r == 2:
                baza_txt.append(f"Baza {i+1}: J2")
            else:
                baza_txt.append(f"Baza {i+1}: empate")
        print(f"  ⚔️   {' | '.join(baza_txt)}")
    
    # Estado envido / truco / flor
    if m.envido_state:
        state_txt = m.envido_state.replace('_', ' ')
        print(f"    Envido: {state_txt}  ({m.envido_points} pts en juego)")
        if m.envido_caller is not None:
            print(f"             Cantado por: {m.player_name(m.envido_caller)}")
    
    if m.truco_state:
        print(f"    Truco: {m.truco_state}  ({m.truco_points} pts en juego)")
        if m.truco_caller is not None:
            print(f"           Cantado por: {m.player_name(m.truco_caller)}")
    
    if m.flower_state:
        state_txt = m.flower_state.replace('_', ' ')
        print(f"    Flor: {state_txt}")
        if m.flower_caller is not None:
            print(f"          Cantado por: {m.player_name(m.flower_caller)}")

    line()
    
    # Cartas en mesa
    j1_played = m.played[0][-1] if m.played[0] and len(m.played[0]) > len(m.played[1]) or \
        (m.played[0] and m.played[1] and len(m.played[0]) == len(m.played[1])) else None
    j2_played = m.played[1][-1] if m.played[1] and len(m.played[1]) > 0 and \
        (len(m.played[0]) == len(m.played[1])) else None
    
    if j1_played or j2_played:
        print(f"\n  Mesa:")
        if j1_played:
            print(f"    J1 (RL Agent) jugó: {fmt_card(j1_played)}")
        if j2_played:
            print(f"    J2 (Tú) jugó: {fmt_card(j2_played)}")
    
    # Manos
    print(f"\n  🤖  Jugador 1 (RL Agent):")
    print(f"    [{len(m.hand1)}] cartas")
    
    print(f"\n  🧑  Jugador 2 (Tú):")
    for i, c in enumerate(m.hand2):
        print(f"    [{i}] {fmt_card(c)}")
    if not m.hand2:
        print("    (sin cartas)")
    
    # Flores declaradas
    if m.flowers_declared:
        flores = [m.player_name(p) for p in m.flowers_declared]
        print(f"\n  🌸  Tiene(n) flor: {', '.join(flores)}")
    
    line()
    
    # Mostrar si tienes que responder algo
    if m.turn == 1:  # Turno del humano (J2)
        if m._waiting_for_truco_response(1):
            print(f"\n  ⚠️   TIENES QUE RESPONDER AL TRUCO cantado por {m.player_name(m.truco_caller)}")
        elif m.envido_state and m.envido_caller != 1 and not m.envido_resolved:
            print(f"\n  ⚠️   TIENES QUE RESPONDER AL ENVIDO cantado por {m.player_name(m.envido_caller)}")
        elif m._waiting_for_flower_response(1):
            print(f"\n  ⚠️   TIENES QUE RESPONDER A LA FLOR cantada por {m.player_name(m.flower_caller)}")
    
    if msg:
        print(f"\n  {msg}\n")
        line()

def show_help(truco: Truco):
    """Muestra los comandos disponibles para el Jugador 2."""
    m = truco
    player = 1  # Siempre es el humano (J2)
    
    print(f"\n  🎮  Turno de: {m.player_name(player)} (Tú)\n")
    print("  Comandos:")
    print("  [0] [1] [2]          → Jugar carta")
    
    # Flor (solo antes de la primera carta)
    if player in m.flowers_declared and not m.flower_resolved and not m.rounds:
        if m.flower_state is None:
            print("  [f]                  → Cantar 'La mía flor'")
            if len(m.flowers_declared) > 1:
                print("  [fe]                 → Con flor envido")
                print("  [fc]                 → Contra flor")
                print("  [fcr]                → Contra flor al resto")
        elif m.flower_caller != player and len(m.flowers_declared) > 1:
            print("  [f]                  → Responder 'La mía'")
            print("  [fe]                 → Con flor envido")
            print("  [fc]                 → Contra flor")
            print("  [fcr]                → Contra flor al resto")
    
    # Envido
    if not m.envido_resolved and not m.rounds:
        if m.envido_state and m.envido_caller != player:
            # Debo responder
            print("  [e]                  → Subir a Envido")
            print("  [re]                 → Subir a Real Envido")
            print("  [fae]                → Subir a Falta Envido")
            print("  [eq]                 → Quiero (envido)")
            print("  [enq]                → No Quiero (envido)")
        else:
            # Puedo cantar
            if m.envido_of(player) != -1:  # no tiene flor
                if m.envido_state is None:
                    print("  [e]                  → Cantar Envido")
                    print("  [re]                 → Cantar Real Envido")
                    print("  [fae]                → Cantar Falta Envido")
    
    # Truco
    if not m.truco_resolved and not m.hand_over:
        if m.truco_state and m.truco_caller != player:
            # Debo responder
            siguiente = {'truco': '[r] Retruco', 'retruco': '[v] Vale Cuatro'}.get(m.truco_state, '')
            if siguiente:
                print(f"  {siguiente}")
            print("  [tq]                 → Quiero (truco)")
            print("  [tnq]                → No Quiero (truco)")
        elif m.truco_state is None:
            # Puedo cantar
            print("  [t]                  → Cantar Truco")
    
    print("  [pts]                → Ver tus puntos de envido")
    print("  [?]                  → Ver ayuda")
    line()

def process_command(cmd: str, truco: Truco):
    """Procesa un comando del Jugador 2 (humano)."""
    player = 1  # Siempre es el humano
    
    # ── Jugar carta ──
    if cmd in ('0', '1', '2'):
        res = truco.play_card(player, int(cmd))
        if not res['ok']:
            return res
        msg = f"✅ Jugaste: {fmt_card(res['card'])}"
        if res.get('baza_done'):
            w = res.get('baza_winner', 'empate')
            msg += f"\n  ⚔️  Baza: {w}"
        if res.get('hand_over'):
            winner = truco.player_name(truco.hand_winner - 1)
            pts = truco.truco_points
            msg += f"\n  🏆  {winner} gana la mano (+{pts} pts)"
        return {'ok': True, 'msg': msg, 'hand_over': res.get('hand_over', False)}
    
    # ── Flor ──
    if cmd == 'f':
        # Cantar "La Mía es Flor"
        if truco.flower_state is None:
            res = truco.call_flower(player, 'la_mia')
            if res['ok']:
                # Solo cambiar turno si ambos tienen flor
                if len(truco.flowers_declared) > 1:
                    truco.turn = 0  # RL debe responder
                # Si solo tú tienes flor, turno sigue siendo tuyo
            return res
        else:
            # Responder a la flor del rival
            flower_caller_antes = truco.flower_caller
            res = truco.respond_flower(player, 'la_mia')
            if res['ok'] and truco.flower_resolved:
                # Flor se resolvió, turno al que la cantó para jugar carta
                truco.turn = flower_caller_antes
            return res
    
    # Rechazar otros tipos de flor (no permitidos en esta versión)
    if cmd in ('fe', 'fc', 'fcr'):
        return {'ok': False, 'msg': "Solo se puede cantar/responder 'La Mía es Flor' (comando: f)"}

    
    # ── Envido ──
    if cmd == 'e':
        if truco.envido_state is None:
            # Cantar envido: pasa turno al RL
            res = truco.call_envido(player, 'envido')
            if res['ok']:
                truco.turn = 0  # Turno automático al RL para responder
            return res
        else:
            # Responder envido: el RL sigue respondiendo
            return truco.respond_envido(player, 'envido')
    if cmd == 're':
        if truco.envido_state is None:
            # Cantar real envido: pasa turno al RL
            res = truco.call_envido(player, 'real_envido')
            if res['ok']:
                truco.turn = 0  # Turno automático al RL para responder
            return res
        else:
            # Responder al envido cantado: subir a real
            return truco.respond_envido(player, 'real_envido')
    if cmd == 'fae':
        if truco.envido_state is None:
            # Cantar falta envido: pasa turno al RL
            res = truco.call_envido(player, 'falta_envido')
            if res['ok']:
                truco.turn = 0  # Turno automático al RL para responder
            return res
        else:
            # Responder al envido cantado: subir a falta
            return truco.respond_envido(player, 'falta_envido')
    if cmd == 'eq':
        envido_caller_antes = truco.envido_caller
        res = truco.respond_envido(player, 'quiero')
        if res['ok'] and truco.envido_resolved:
            # Envido se resolvió, turno al que lo cantó para jugar carta
            truco.turn = envido_caller_antes
        return res
    if cmd == 'enq':
        envido_caller_antes = truco.envido_caller
        res = truco.respond_envido(player, 'no_quiero')
        if res['ok'] and truco.envido_resolved:
            # Envido se resolvió, turno al que lo cantó para jugar carta
            truco.turn = envido_caller_antes
        return res
    
    # ── Truco ──
    if cmd == 't':
        # Cantar truco: pasa turno al RL para responder
        res = truco.call_truco(player, 'truco')
        if res['ok']:
            truco.turn = 0  # Turno automático al RL
        return res
    if cmd == 'r':
        # Intentar subir el truco a retruco
        res = truco.respond_truco(player, 'retruco')
        if res['ok']:
            # Subida exitosa, turno al RL para responder
            truco.turn = 0
        return res
    if cmd == 'v':
        # Intentar subir el truco a vale cuatro
        res = truco.respond_truco(player, 'vale_cuatro')
        if res['ok']:
            # Subida exitosa, turno al RL para responder
            truco.turn = 0
        return res
    if cmd == 'tq':
        truco_caller_antes = truco.truco_caller
        res = truco.respond_truco(player, 'quiero')
        if res['ok'] and truco.truco_resolved:
            # Truco se resolvió, turno al que lo cantó para jugar carta
            truco.turn = truco_caller_antes
        return res
    if cmd == 'tnq':
        truco_caller_antes = truco.truco_caller
        res = truco.respond_truco(player, 'no_quiero')
        if res['ok'] and truco.truco_resolved:
            # Truco se resolvió, turno al que lo cantó para jugar carta
            truco.turn = truco_caller_antes
        return res
    
    # ── Info ──
    if cmd == 'pts':
        e = truco.envido_of(player)
        if e == -1:
            return {'ok': True, 'msg': f"Tenés flor (el envido no aplica)."}
        return {'ok': True, 'msg': f"Tus puntos de envido: {e}"}
    
    if cmd == '?':
        return {'ok': True, 'msg': '', 'show_help': True}
    
    return {'ok': False, 'msg': f"Comando desconocido: '{cmd}'. Escribí [?] para ver ayuda."}

# ─────────────────────────────────────────────
# LOOP PRINCIPAL
# ─────────────────────────────────────────────

def play_hand(truco: Truco):
    """Loop de una mano completa, alternando entre agente y humano."""
    agent = RLAgent()
    truco.deal()
    msg = ""
    
    # Anunciar flores al inicio
    if truco.flowers_declared:
        flores = [truco.player_name(p) for p in truco.flowers_declared]
        msg = f"🌸  ¡Tiene(n) flor: {', '.join(flores)}!"
    
    while not truco.hand_over:
        show_state(truco, msg)
        msg = ""
        
        # Turno del agente (Jugador 1)
        if truco.turn == 0:
            print(f"\n  🤖  RL Agent está pensando...\n")
            pause()
            
            action = agent.decide_action(truco)
            
            if action[0] == 'play_card':
                res = truco.play_card(0, action[1])
                if res['ok']:
                    msg = f"🤖  RL Agent juega: {fmt_card(res['card'])}"
                    if res.get('baza_done'):
                        w = res.get('baza_winner', 'empate')
                        msg += f"\n  ⚔️  Baza: {w}"
                    if res.get('hand_over'):
                        winner = truco.player_name(truco.hand_winner - 1)
                        pts = truco.truco_points
                        msg += f"\n  🏆  {winner} gana la mano (+{pts} pts)"
            
            elif action[0] == 'call_envido':
                res = truco.call_envido(0, action[1])
                if res['ok']:
                    msg = res['msg']
                    truco.turn = 1  # Turno automático al humano para responder
            
            elif action[0] == 'respond_envido':
                envido_caller_antes = truco.envido_caller
                res = truco.respond_envido(0, action[1])
                if res['ok']:
                    msg = res['msg']
                    if truco.envido_resolved:
                        # Envido resuelto, turno al que lo cantó para jugar carta
                        truco.turn = envido_caller_antes
                    else:
                        # El RL subió, turno al humano para responder nuevamente
                        truco.turn = 1
            
            elif action[0] == 'call_truco':
                res = truco.call_truco(0, action[1])
                if res['ok']:
                    msg = res['msg']
                    truco.turn = 1  # Turno automático al humano para responder
            
            elif action[0] == 'respond_truco':
                truco_caller_antes = truco.truco_caller
                res = truco.respond_truco(0, action[1])
                if res['ok']:
                    msg = res['msg']
                    if truco.truco_resolved:
                        # Truco resuelto, turno al que lo cantó para jugar carta
                        truco.turn = truco_caller_antes
                    else:
                        # El RL subió, turno al humano para responder nuevamente
                        truco.turn = 1
                    if res.get('hand_over'):
                        pass  # Mano terminada
            
            elif action[0] == 'call_flower':
                res = truco.call_flower(0, action[1])
                if res['ok']:
                    msg = res['msg']
                    # Si ambos tienen flor, turno al humano
                    if len(truco.flowers_declared) > 1:
                        truco.turn = 1  # Turno automático al humano
            
            elif action[0] == 'respond_flower':
                flower_caller_antes = truco.flower_caller
                res = truco.respond_flower(0, action[1])
                if res['ok']:
                    msg = res['msg']
                    if truco.flower_resolved:
                        # Flor resuelta, turno al que la cantó para jugar carta
                        truco.turn = flower_caller_antes
                    else:
                        # El RL subió, turno al humano para responder nuevamente
                        truco.turn = 1
        
        # Turno del humano (Jugador 2)
        else:
            show_help(truco)
            
            try:
                cmd = input("  > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\n  Juego interrumpido.")
                return
            
            res = process_command(cmd, truco)
            
            if res.get('show_help'):
                pause()
                continue
            
            if not res['ok']:
                msg = f"❌  {res['msg']}"
                pause()
                continue
            
            msg = res.get('msg', '')
            
            if res.get('hand_over'):
                # Resolver flor solitaria al final de la mano
                fl = truco.resolve_single_flower()
                if fl['ok']:
                    msg += f"\n  {fl['msg']}"
                show_state(truco, msg)
                print(f"\n  📊  {truco.score_str()}")
                pause()
                return
        
        # Si la mano terminó, salir del loop
        if truco.hand_over:
            fl = truco.resolve_single_flower()
            if fl['ok']:
                msg += f"\n  {fl['msg']}"
            show_state(truco, msg)
            print(f"\n  📊  {truco.score_str()}")
            pause()
            return
    
    show_state(truco, msg)
    print(f"\n  📊  {truco.score_str()}")
    pause()


def main():
    clear()
    header("🃏  TRUCO URUGUAYO vs RL AGENT")
    print(f"\n  Partida a {Truco.POINTS_TO_WIN} puntos.")
    print(f"  🤖  Jugador 1: RL Agent (automático)")
    print(f"  🧑  Jugador 2: Tú (manual)\n")
    input("  Presioná ENTER para comenzar...")
    
    truco = Truco()
    
    while not truco.game_winner():
        play_hand(truco)
        truco.mano_player = 1 - truco.mano_player  # alterna mano
    
    clear()
    winner = truco.game_winner()
    header("🏆  FIN DE LA PARTIDA")
    print(f"\n  🎉  ¡{truco.player_name(winner - 1)} gana la partida!")
    print(f"\n  📊  {truco.score_str()}")
    line()
    print("\n  ¡Gracias por jugar!")


if __name__ == '__main__':
    main()
