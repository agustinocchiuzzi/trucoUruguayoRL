"""
truco_engine.py
---------------
Motor del Truco Uruguayo 1v1 con flujo de juego correcto.
 
Flujo de una mano:
  - Se reparten 3 cartas a cada jugador y se voltea la muestra.
  - Antes de tirar la primera carta (primera ronda), cualquier jugador
    en su turno puede cantar: ENVIDO, REAL ENVIDO, TRUCO o FLOR.
  - Si hay flor en cualquiera de los dos jugadores, el envido queda anulado.
  - Una vez cantado, el rival debe responder antes de que el juego continúe.
  - Después de la primera carta de la primera ronda, solo se puede cantar TRUCO.
  - La mano se juega en hasta 3 bazas. Gana quien gane 2.
 
Estados posibles en cada turno (ACTION_SPACE):
  PLAY_0, PLAY_1, PLAY_2   → jugar carta 0, 1 o 2
  CALL_ENVIDO              → cantar envido (2 pts)
  CALL_REAL_ENVIDO         → cantar real envido (3 pts)
  CALL_TRUCO               → cantar truco
  CALL_RETRUCO             → cantar retruco
  CALL_VALE_CUATRO         → cantar vale cuatro
  CALL_FLOWER              → cantar flor (la mía)
  RESPOND_QUIERO           → quiero (acepta el canto pendiente)
  RESPOND_NO_QUIERO        → no quiero (rechaza el canto pendiente)
 
El motor expone:
  - legal_actions()  → lista de acciones válidas en el estado actual
  - step(action)     → ejecuta la acción, retorna (obs, reward, done, info)
  - reset()          → nueva mano
  - observation()    → vector numérico del estado (para el agente RL)
"""
 
import random
import numpy as np
from Card import Card
from Game import Game
 
# ── Constantes de acción ──────────────────────────────────────
PLAY_0           = 0
PLAY_1           = 1
PLAY_2           = 2
CALL_ENVIDO      = 3
CALL_REAL_ENVIDO = 4
CALL_TRUCO       = 5
CALL_RETRUCO     = 6
CALL_VALE_CUATRO = 7
CALL_FLOWER      = 8
RESPOND_QUIERO   = 9
RESPOND_NO_QUIERO= 10
 
N_ACTIONS = 11
 
ACTION_NAMES = {
    PLAY_0: "Jugar carta 0",
    PLAY_1: "Jugar carta 1",
    PLAY_2: "Jugar carta 2",
    CALL_ENVIDO: "Envido",
    CALL_REAL_ENVIDO: "Real Envido",
    CALL_TRUCO: "Truco",
    CALL_RETRUCO: "Retruco",
    CALL_VALE_CUATRO: "Vale Cuatro",
    CALL_FLOWER: "La mía flor",
    RESPOND_QUIERO: "Quiero",
    RESPOND_NO_QUIERO: "No Quiero",
}
 
# ── Estado del canto pendiente ────────────────────────────────
NO_PENDING      = 0
PENDING_ENVIDO  = 1
PENDING_REAL    = 2
PENDING_TRUCO   = 3
PENDING_RETRUCO = 4
PENDING_V4      = 5
PENDING_FLOWER  = 6
 
 
class TrucoEngine:
    """
    Motor 1v1 del Truco Uruguayo.
    Jugador 0 = el pie (empieza en la primera baza).
    Jugador 1 = el mano (reparte, empieza en buenas/malas).
    """
 
    POINTS_TO_WIN = 40
    PALOS   = ["sword", "coarse", "gold", "cup"]
    NUMBERS = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
 
    def __init__(self):
        self.game    = Game()
        self.score   = [0, 0]
        self.mano_player = 1   # quién reparte (se alterna cada mano)
        self._full_deck = [(n, p) for p in self.PALOS for n in self.NUMBERS]
        self.reset()
 
    # ─────────────────────────────────────────────
    # RESET / DEAL
    # ─────────────────────────────────────────────
 
    def reset(self):
        """Inicia una nueva mano. Retorna la observación inicial."""
        deck = random.sample(self._full_deck, 7)
        self.hand = [
            [Card(deck[i][0], deck[i][1]) for i in range(3)],   # jugador 0
            [Card(deck[i][0], deck[i][1]) for i in range(3, 6)], # jugador 1
        ]
        self.sample = Card(deck[6][0], deck[6][1])
 
        # Cartas jugadas por ronda: played[player] = lista de cartas
        self.played = [[], []]
 
        # Resultados de bazas: 0=empate, 1=j0 gana, 2=j1 gana
        self.rounds = []
 
        # Turno: el pie (1 - mano_player) empieza
        self.turn = 1 - self.mano_player
 
        # ── Estado de cantos ──
        # Canto pendiente de respuesta
        self.pending        = NO_PENDING
        self.pending_caller = None   # quién cantó
 
        # Envido
        self.envido_state   = None   # None, 'envido', 'real_envido'
        self.envido_pts     = 0      # puntos en juego
        self.envido_done    = False
 
        # Truco
        self.truco_state    = None   # None, 'truco', 'retruco', 'vale_cuatro'
        self.truco_pts      = 1      # puntos en juego
        self.truco_done     = False
 
        # Flor
        self.has_flower = [
            self.game.isFlower(self.hand[0], self.sample),
            self.game.isFlower(self.hand[1], self.sample),
        ]
        self.flower_done    = False
        self.flower_winner  = None   # 0 o 1
 
        # Si hay flor, el envido queda anulado
        self.envido_blocked = any(self.has_flower)
 
        # Primera ronda jugada (flag para bloquear envido/flor después)
        self.first_card_played = False
 
        # Fin de mano
        self.done           = False
        self.hand_winner    = None   # 0 o 1
        self.last_rewards   = [0.0, 0.0]
 
        return self.observation()
 
    # ─────────────────────────────────────────────
    # ACCIONES LEGALES
    # ─────────────────────────────────────────────
 
    def legal_actions(self):
        """Retorna lista de acciones válidas para el jugador actual."""
        if self.done:
            return []
 
        actions = []
        p = self.turn
 
        # ── Si hay canto pendiente de respuesta ──
        if self.pending != NO_PENDING:
            # Solo puede responder el rival del que cantó
            if self.pending_caller == p:
                # Quien cantó solo puede esperar — no debería ocurrir en flujo normal
                return []
 
            actions.append(RESPOND_QUIERO)
            actions.append(RESPOND_NO_QUIERO)
 
            # Puede revirar si corresponde
            if self.pending == PENDING_ENVIDO and not self.envido_blocked:
                actions.append(CALL_REAL_ENVIDO)
            if self.pending == PENDING_TRUCO:
                actions.append(CALL_RETRUCO)
            if self.pending == PENDING_RETRUCO:
                actions.append(CALL_VALE_CUATRO)
 
            return actions
 
        # ── Turno normal ──
        # Jugar cartas disponibles
        for i in range(len(self.hand[p])):
            actions.append(PLAY_0 + i)
 
        # Cantos solo antes de tirar la primera carta de la mano
        # (first_card_played se activa cuando CUALQUIER jugador tira su primera carta)
        pre_primera = not self.first_card_played
 
        # Envido: antes de primera carta, no bloqueado, no resuelto
        if pre_primera and not self.envido_blocked and not self.envido_done:
            if self.envido_state is None:
                actions.append(CALL_ENVIDO)
                actions.append(CALL_REAL_ENVIDO)
            elif self.envido_state == 'envido':
                actions.append(CALL_REAL_ENVIDO)
 
        # Truco: en cualquier momento, no resuelto
        if not self.truco_done:
            if self.truco_state is None:
                actions.append(CALL_TRUCO)
            # Retruco/vale cuatro solo si el rival cantó el anterior
            elif self.truco_state == 'truco' and self.pending_caller != p:
                actions.append(CALL_RETRUCO)
            elif self.truco_state == 'retruco' and self.pending_caller != p:
                actions.append(CALL_VALE_CUATRO)
 
        # Flor: antes de primera carta, si tiene, no resuelta
        if pre_primera and self.has_flower[p] and not self.flower_done:
            actions.append(CALL_FLOWER)
 
        return list(set(actions))  # sin duplicados
 
    # ─────────────────────────────────────────────
    # STEP
    # ─────────────────────────────────────────────
 
    def step(self, action):
        """
        Ejecuta la acción del jugador actual.
        Retorna: (observation, rewards, done, info)
          - rewards: [reward_j0, reward_j1] — recompensa inmediata
          - done: True si la mano terminó
          - info: dict con detalles
        """
        assert not self.done, "La mano ya terminó. Llamá reset()."
        assert action in self.legal_actions(), \
            f"Acción ilegal: {ACTION_NAMES.get(action, action)}. Legales: {[ACTION_NAMES[a] for a in self.legal_actions()]}"
 
        p    = self.turn
        info = {'action': ACTION_NAMES.get(action, action), 'player': p}
        rewards = [0.0, 0.0]
 
        # ── JUGAR CARTA ──────────────────────────────────────
        if action in (PLAY_0, PLAY_1, PLAY_2):
            idx  = action  # 0, 1 o 2 coinciden con índice
            card = self.hand[p].pop(idx)
            self.played[p].append(card)
            self.first_card_played = True
            info['card'] = card
 
            # Después de tirar, bloquear envido y flor
            self.envido_blocked = True
 
            # Si ambos jugaron en esta ronda
            if len(self.played[0]) == len(self.played[1]):
                c0   = self.played[0][-1]
                c1   = self.played[1][-1]
                baza = self.game.resolveRound(c0, c1, self.sample)
                self.rounds.append(baza)
                info['baza'] = baza
 
                # Quién empieza la siguiente
                if baza == 1:
                    self.turn = 0
                elif baza == 2:
                    self.turn = 1
                # empate: sigue el mismo que empezó esta baza
 
                # ¿Terminó la mano?
                winner = self.game.resolveHand(self.rounds)
                if winner != 0 or len(self.rounds) == 3:
                    w = winner if winner != 0 else (self.mano_player + 1)
                    self._close_hand(w - 1, rewards, info)
            else:
                # Pasa turno
                self.turn = 1 - p
 
        # ── RESPONDER QUIERO / NO QUIERO ─────────────────────
        elif action == RESPOND_QUIERO:
            rewards, info = self._handle_quiero(p, rewards, info)
 
        elif action == RESPOND_NO_QUIERO:
            rewards, info = self._handle_no_quiero(p, rewards, info)
 
        # ── CANTOS ───────────────────────────────────────────
        elif action == CALL_ENVIDO:
            self.envido_state   = 'envido'
            self.envido_pts     = 2
            self.pending        = PENDING_ENVIDO
            self.pending_caller = p
            self.turn           = 1 - p
            info['msg'] = f"J{p} canta ENVIDO (2 pts en juego)"
 
        elif action == CALL_REAL_ENVIDO:
            prev = self.envido_pts
            self.envido_state   = 'real_envido'
            self.envido_pts     = prev + 3 if self.envido_state else 3
            self.pending        = PENDING_REAL
            self.pending_caller = p
            self.turn           = 1 - p
            info['msg'] = f"J{p} canta REAL ENVIDO ({self.envido_pts} pts en juego)"
 
        elif action == CALL_TRUCO:
            self.truco_state    = 'truco'
            self.truco_pts      = 2
            self.pending        = PENDING_TRUCO
            self.pending_caller = p
            self.turn           = 1 - p
            info['msg'] = f"J{p} canta TRUCO (2 pts en juego)"
 
        elif action == CALL_RETRUCO:
            self.truco_state    = 'retruco'
            self.truco_pts      = 3
            self.pending        = PENDING_RETRUCO
            self.pending_caller = p
            self.turn           = 1 - p
            info['msg'] = f"J{p} canta RETRUCO (3 pts en juego)"
 
        elif action == CALL_VALE_CUATRO:
            self.truco_state    = 'vale_cuatro'
            self.truco_pts      = 4
            self.pending        = PENDING_V4
            self.pending_caller = p
            self.turn           = 1 - p
            info['msg'] = f"J{p} canta VALE CUATRO (4 pts en juego)"
 
        elif action == CALL_FLOWER:
            self.pending        = PENDING_FLOWER
            self.pending_caller = p
            self.turn           = 1 - p
            info['msg'] = f"J{p} canta LA MÍA FLOR"
 
        self.last_rewards = rewards
        obs = self.observation()
        return obs, rewards, self.done, info
 
    # ─────────────────────────────────────────────
    # HANDLERS DE RESPUESTA
    # ─────────────────────────────────────────────
 
    def _handle_quiero(self, p, rewards, info):
        """Procesa RESPOND_QUIERO según el canto pendiente."""
        return self._quiero_dispatch(p, rewards, info)
 
    def _quiero_dispatch(self, p, rewards, info):
        """Despacha el quiero al canto correcto según self.pending."""
        pend = self.pending  # leer ANTES de limpiar
 
        if pend in (PENDING_ENVIDO, PENDING_REAL):
            self.pending      = NO_PENDING
            self.envido_done  = True
            e0 = self.game.calculateEnvido(self.hand[0] + self.played[0], self.sample)
            e1 = self.game.calculateEnvido(self.hand[1] + self.played[1], self.sample)
            # Manejar -1 (flor) — no debería ocurrir si envido_blocked funciona bien
            if e0 < 0: e0 = 0
            if e1 < 0: e1 = 0
            winner = 0 if e0 >= e1 else 1
            pts = self.envido_pts
            self.score[winner] += pts
            rewards[winner]    += pts
            rewards[1-winner]  -= pts
            info['envido'] = {'winner': winner, 'e0': e0, 'e1': e1, 'pts': pts}
            info['msg']    = f"Envido querido. J{winner} gana {pts} pts (J0:{e0} J1:{e1})"
            # Turno: sigue el que respondió
            self.turn = p
 
        elif pend in (PENDING_TRUCO, PENDING_RETRUCO, PENDING_V4):
            self.pending = NO_PENDING
            # No se resuelve aún — se resuelve cuando termine la mano
            info['msg'] = f"Truco querido. En juego: {self.truco_pts} pts"
            self.turn   = p
 
        elif pend == PENDING_FLOWER:
            self.pending     = NO_PENDING
            self.flower_done = True
            # Si solo uno tiene flor → 3 pts al que cantó
            if not self.has_flower[p]:
                winner = self.pending_caller
                pts    = 3
                self.score[winner] += pts
                rewards[winner]    += pts
                rewards[1-winner]  -= pts
                info['msg'] = f"Flor aceptada. J{winner} suma {pts} pts"
            else:
                # Ambos tienen flor → compara valor
                f0 = self.game.calculateFlower(self.hand[0] + self.played[0], self.sample)
                f1 = self.game.calculateFlower(self.hand[1] + self.played[1], self.sample)
                winner = 0 if f0 >= f1 else 1
                pts    = 3
                self.score[winner] += pts
                rewards[winner]    += pts
                rewards[1-winner]  -= pts
                info['msg'] = f"Flor querida. J{winner} gana {pts} pts (J0:{f0} J1:{f1})"
            self.flower_winner = winner
            self.turn = p
 
        return rewards, info
 
    def _handle_no_quiero(self, p, rewards, info):
        """Procesa RESPOND_NO_QUIERO."""
        pend   = self.pending
        caller = self.pending_caller
        self.pending = NO_PENDING
 
        if pend in (PENDING_ENVIDO, PENDING_REAL):
            self.envido_done = True
            pts = 1  # no querido siempre vale 1 pt para quien cantó
            self.score[caller]  += pts
            rewards[caller]     += pts
            rewards[1 - caller] -= pts
            info['msg'] = f"Envido no querido. J{caller} suma {pts} pt"
            self.turn   = p
 
        elif pend in (PENDING_TRUCO, PENDING_RETRUCO, PENDING_V4):
            # Gana quien cantó, con los puntos del nivel anterior
            pts_no_quiero = {
                PENDING_TRUCO:   1,
                PENDING_RETRUCO: 2,
                PENDING_V4:      3,
            }
            pts = pts_no_quiero[pend]
            self.score[caller]  += pts
            rewards[caller]     += pts
            rewards[1 - caller] -= pts
            self.truco_done = True
            info['msg']     = f"Truco no querido. J{caller} suma {pts} pts"
            # La mano termina
            self._close_hand(caller, rewards, info)
 
        elif pend == PENDING_FLOWER:
            # El que no tiene flor no puede decir no quiero — esto no debería pasar
            # Si ambos tienen flor y uno dice no quiero a contra flor → 3 pts al caller
            pts = 3
            self.score[caller]  += pts
            rewards[caller]     += pts
            self.flower_done     = True
            self.flower_winner   = caller
            info['msg'] = f"Flor no querida. J{caller} suma {pts} pts"
            self.turn   = p
 
        return rewards, info
 
    # ─────────────────────────────────────────────
    # CERRAR MANO
    # ─────────────────────────────────────────────
 
    def _close_hand(self, winner_idx, rewards, info):
        """Cierra la mano, asigna puntos de truco y marca done."""
        self.done        = True
        self.hand_winner = winner_idx
 
        if not self.truco_done:
            pts = self.truco_pts
            self.score[winner_idx]   += pts
            rewards[winner_idx]      += pts
            rewards[1 - winner_idx]  -= pts
            self.truco_done = True
 
        # Flor solitaria al final si no fue resuelta
        if not self.flower_done and any(self.has_flower):
            flower_player = next(i for i, f in enumerate(self.has_flower) if f)
            self.score[flower_player] += 3
            rewards[flower_player]    += 3
            self.flower_done    = True
            self.flower_winner  = flower_player
 
        info['hand_winner'] = winner_idx
        info['score']       = list(self.score)
 
    # ─────────────────────────────────────────────
    # OBSERVACIÓN (para el agente RL)
    # ─────────────────────────────────────────────
 
    def observation(self, perspective=None):
        """
        Construye el vector de observación desde la perspectiva
        del jugador actual (o del especificado).
 
        El vector tiene 115 valores float32:
          [0:40]   mis cartas en mano (one-hot sobre las 40 cartas del mazo)
          [40:80]  cartas jugadas por mí (one-hot)
          [80:120] cartas jugadas por el rival (one-hot) — lo que es visible
          Nota: las cartas del rival en mano NO se incluyen (información oculta)
          [120]    muestra (índice normalizado 0-1)
          [121]    puntaje propio normalizado (/ 40)
          [122]    puntaje rival normalizado (/ 40)
          [123]    es mi turno (1/0)
          [124]    pending canto (0-6, normalizado)
          [125]    yo canté el pending (1/0)
          [126]    envido_pts normalizado (/ 10)
          [127]    truco_pts normalizado (/ 4)
          [128]    tengo flor (1/0)
          [129]    rival tiene flor (1/0)
          [130]    envido bloqueado (1/0)
          [131]    first_card_played (1/0)
          [132]    baza 1 resultado (0=empate,0.5=yo gano,1=rival gana) — desde mi perspectiva
          [133]    baza 2 resultado
          [134]    baza 3 resultado
 
        Total: 135 valores
        """
        p = perspective if perspective is not None else self.turn
 
        # Índice de cada carta en el mazo
        card_idx = {(n, pa): i for i, (n, pa) in enumerate(
            [(n, pa) for pa in self.PALOS for n in self.NUMBERS]
        )}
 
        def one_hot_cards(cards):
            vec = np.zeros(40, dtype=np.float32)
            for c in cards:
                idx = card_idx.get((c.number, c.palo), -1)
                if idx >= 0:
                    vec[idx] = 1.0
            return vec
 
        obs = np.zeros(135, dtype=np.float32)
 
        # Mis cartas en mano
        obs[0:40]   = one_hot_cards(self.hand[p])
        # Mis cartas jugadas
        obs[40:80]  = one_hot_cards(self.played[p])
        # Cartas jugadas por el rival (visible)
        obs[80:120] = one_hot_cards(self.played[1 - p])
 
        # Muestra
        obs[120] = card_idx.get((self.sample.number, self.sample.palo), 0) / 39.0
 
        # Puntajes
        obs[121] = self.score[p] / self.POINTS_TO_WIN
        obs[122] = self.score[1 - p] / self.POINTS_TO_WIN
 
        # Turno
        obs[123] = 1.0 if self.turn == p else 0.0
 
        # Canto pendiente
        obs[124] = self.pending / 6.0
        obs[125] = 1.0 if self.pending_caller == p else 0.0
 
        # Puntos en juego
        obs[126] = self.envido_pts / 10.0
        obs[127] = self.truco_pts / 4.0
 
        # Flor
        obs[128] = 1.0 if self.has_flower[p] else 0.0
        obs[129] = 1.0 if self.has_flower[1 - p] else 0.0
        obs[130] = 1.0 if self.envido_blocked else 0.0
        obs[131] = 1.0 if self.first_card_played else 0.0
 
        # Bazas (desde perspectiva del jugador p)
        # p=0: baza 1 = 0.5 si gana j0 (result==1), 1 si gana j1 (result==2)
        for i, r in enumerate(self.rounds[:3]):
            if r == 0:
                obs[132 + i] = 0.5   # empate
            elif (r == 1 and p == 0) or (r == 2 and p == 1):
                obs[132 + i] = 1.0   # yo gané
            else:
                obs[132 + i] = 0.0   # rival ganó
 
        return obs
 
    # ─────────────────────────────────────────────
    # UTILIDADES
    # ─────────────────────────────────────────────
 
    def game_over(self):
        """Retorna el índice del ganador de la partida (0 o 1), o None."""
        if self.score[0] >= self.POINTS_TO_WIN:
            return 0
        if self.score[1] >= self.POINTS_TO_WIN:
            return 1
        return None
 
    def new_hand(self):
        """Alterna el mano y reinicia para la siguiente mano."""
        self.mano_player = 1 - self.mano_player
        return self.reset()
 
    def score_str(self):
        return f"J0: {self.score[0]} pts  |  J1: {self.score[1]} pts"
 
    def render(self, perspective=0):
        """Muestra el estado actual en consola (debug)."""
        palos_es = {"sword": "Espada", "coarse": "Basto", "gold": "Oro", "cup": "Copa"}
        print(f"\n{'─'*50}")
        print(f"  Muestra: {self.sample.number} de {palos_es[self.sample.palo]}")
        print(f"  {self.score_str()}")
        print(f"  Mano: J{self.mano_player}  |  Turno: J{self.turn}")
        if self.rounds:
            print(f"  Bazas: {self.rounds}")
        if self.pending != NO_PENDING:
            print(f"  Pendiente: {self.pending} (cantó J{self.pending_caller})")
        for pl in [0, 1]:
            cartas = [f"{c.number}/{palos_es[c.palo][:2]}" for c in self.hand[pl]]
            jugadas = [f"{c.number}/{palos_es[c.palo][:2]}" for c in self.played[pl]]
            flor = " 🌸" if self.has_flower[pl] else ""
            print(f"  J{pl}: mano={cartas}  jugadas={jugadas}{flor}")
        print(f"  Legales J{self.turn}: {[ACTION_NAMES[a] for a in self.legal_actions()]}")
        print(f"{'─'*50}")