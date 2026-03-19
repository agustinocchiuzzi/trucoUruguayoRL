from Game import Game
import random
from Card import Card
 
class Truco:
 
    POINTS_TO_WIN = 30
 
    def __init__(self):
        palos = ["sword", "coarse", "gold", "cup"]
        numbers = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
        self.maze = [(number, palo) for palo in palos for number in numbers]
        self.game = Game()
        self.score = [0, 0]
        self._reset_hand_state()
 
    def _reset_hand_state(self):
        self.hand1   = []
        self.hand2   = []
        self.sample  = None
 
        self.played  = [[], []]
        self.rounds  = []
 
        self.turn    = 1
        self.mano_player = 0
 
        self.truco_state      = None    # None, 'truco', 'retruco', 'vale_cuatro', 'querido'
        self.truco_caller     = None    # quién cantó (0 o 1)
        self.truco_points     = 1       # puntos en juego por truco
        self.truco_resolved   = False
        self.truco_word_holder = None   # quién tiene la "palabra" para levantar apuesta después de "quiero"
 
        # Estado del envido
        self.envido_state     = None    # None, 'envido', 'real_envido', 'falta_envido', 'querido', 'no_querido'
        self.envido_caller    = None
        self.envido_points    = 0       # puntos acumulados en la escalada
        self.envido_resolved  = False
 
        # Estado de la flor
        self.flower_state     = None    # None, 'la_mia', 'con_flor_envido', 'contra_flor', 'contra_flor_al_resto'
        self.flower_caller    = None
        self.flower_resolved  = False
        self.flowers_declared = []      # [0] si j1, [1] si j2, ambos si los dos
 
        # Mano terminada
        self.hand_over        = False
        self.hand_winner      = None    # 1 o 2
 
    # ─────────────────────────────────────────────
    # REPARTO
    # ─────────────────────────────────────────────
 
    def generateRandomHandsAndSample(self):
        random.shuffle(self.maze)
        randCards = random.sample(self.maze, 7)
        hand1  = [Card(randCards[i][0], randCards[i][1]) for i in range(3)]
        hand2  = [Card(randCards[i][0], randCards[i][1]) for i in range(3, 6)]
        sample = Card(randCards[6][0], randCards[6][1])
        return hand1, hand2, sample
 
    def deal(self):
        self._reset_hand_state()
        self.hand1, self.hand2, self.sample = self.generateRandomHandsAndSample()
        self.turn = 1 - self.mano_player
 
        self._detect_flowers()
 
    def _detect_flowers(self):
        h1 = self.game.isFlower(self.hand1, self.sample)
        h2 = self.game.isFlower(self.hand2, self.sample)
        if h1:
            self.flowers_declared.append(0)
        if h2:
            self.flowers_declared.append(1)
 
    # ─────────────────────────────────────────────
    # UTILIDADES
    # ─────────────────────────────────────────────
 
    def hand_of(self, player):
        """Retorna la mano actual del jugador (0 o 1)."""
        return self.hand1 if player == 0 else self.hand2
 
    def rival_of(self, player):
        return 1 - player
 
    def player_name(self, idx):
        return f"Jugador {idx + 1}"
 
    def current_hand(self):
        return self.hand1 if self.turn == 0 else self.hand2
 
    def cards_in_hand(self, player):
        return self.hand_of(player)
 
    def envido_of(self, player):
        return self.game.calculateEnvido(self.hand_of(player), self.sample)
 
    def flower_value_of(self, player):
        return self.game.calculateFlower(self.hand_of(player), self.sample)
 
    # ─────────────────────────────────────────────
    # JUGAR CARTA
    # ─────────────────────────────────────────────
 
    def play_card(self, player, card_index):
        """
        El jugador juega la carta en card_index.
        Retorna dict con resultado.
        """
        if player != self.turn:
            return {'ok': False, 'msg': f"No es tu turno. Turno de {self.player_name(self.turn)}."}
 
        hand = self.hand_of(player)
        if card_index < 0 or card_index >= len(hand):
            return {'ok': False, 'msg': f"Índice inválido. Tenés {len(hand)} cartas."}
 
        # Verificar que no haya un canto de truco o flor pendiente de respuesta
        if self._waiting_for_truco_response(player):
            return {'ok': False, 'msg': "Debés responder al truco antes de jugar."}
        if self._waiting_for_flower_response(player):
            return {'ok': False, 'msg': "Debés responder a la flor antes de jugar."}
 
        card = hand.pop(card_index)
        self.played[player].append(card)
 
        result = {'ok': True, 'card': card, 'player': player, 'baza_done': False}
 
        # Si ambos jugaron en esta ronda
        if len(self.played[0]) == len(self.played[1]):
            c1 = self.played[0][-1]
            c2 = self.played[1][-1]
            baza = self.game.resolveRound(c1, c2, self.sample)
            self.rounds.append(baza)
            result['baza_done']   = True
            result['baza_result'] = baza   # 1, 2 o 0
 
            # Quién empieza la siguiente baza
            if baza == 1:
                self.turn = 0
                result['baza_winner'] = self.player_name(0)
            elif baza == 2:
                self.turn = 1
                result['baza_winner'] = self.player_name(1)
            else:
                result['baza_winner'] = 'empate'
                # En empate sigue el mismo que empezó esa baza (el primero)
                # Ahora self.turn es del segundo, así que invertimos
                self.turn = self.rival_of(self.turn)
 
            # Verificar si la mano terminó
            winner = self.game.resolveHand(self.rounds)
            if winner != 0 or len(self.rounds) == 3:
                self._close_hand(winner if winner != 0 else self._mano_winner())
                result['hand_over']   = True
                result['hand_winner'] = self.hand_winner
        else:
            # Pasa el turno al otro
            self.turn = self.rival_of(player)
 
        return result
 
    def _mano_winner(self):
        """En caso de triple empate gana el mano (quien empieza)."""
        return self.mano_player + 1  # convertir a 1-based
 
    def _close_hand(self, winner):
        """Cierra la mano, asigna puntos de truco y actualiza estado."""
        self.hand_over   = True
        self.hand_winner = winner  # 1 o 2
        idx = winner - 1
        if not self.truco_resolved:
            self.score[idx] += self.truco_points
            self.truco_resolved = True
 
    # ─────────────────────────────────────────────
    # TRUCO
    # ─────────────────────────────────────────────
 
    def _waiting_for_truco_response(self, player):
        """True si hay un canto de truco pendiente que el jugador debe responder."""
        return (
            self.truco_state in ('truco', 'retruco', 'vale_cuatro') and
            self.truco_caller != player and
            not self.truco_resolved
        )
 
    def can_call_truco(self, player):
        if self.hand_over or self.truco_resolved:
            return False, "El truco ya terminó."
        if self.truco_caller == player:
            return False, "No podés subir tu propio canto."
        escalada = {None: 'truco', 'truco': 'retruco', 'retruco': 'vale_cuatro', 'querido': None}
        if self.truco_state == 'vale_cuatro':
            return False, "No se puede subir más el truco."
        return True, escalada.get(self.truco_state, 'truco')
 
    def call_truco(self, player, tipo):
        """
        tipo: 'truco', 'retruco', 'vale_cuatro'
        Puntos: truco=1, retruco=3 (suma 2 al querido), vale_cuatro=4 (suma 1 al retruco querido)
        """
        ok, next_call = self.can_call_truco(player)
        if not ok:
            return {'ok': False, 'msg': next_call}
 
        orden = [None, 'truco', 'retruco', 'vale_cuatro']
        current_idx = orden.index(self.truco_state)
        tipo_idx    = orden.index(tipo)
 
        if tipo_idx != current_idx + 1:
            return {'ok': False, 'msg': f"El siguiente canto debe ser '{orden[current_idx + 1]}'."}
 
        self.truco_state  = tipo
        self.truco_caller = player
        puntos = {'truco': 1, 'retruco': 3, 'vale_cuatro': 4}
        self.truco_points = puntos[tipo]
        return {'ok': True, 'msg': f"{self.player_name(player)} canta: {tipo.upper()}"}

 
    def respond_truco(self, player, response):
        """
        response: 'quiero', 'no_quiero', 'retruco', 'vale_cuatro'
        Cuando dices "quiero", obtienes la palabra para poder levantar la apuesta.
        """
        if self.truco_caller == player:
            return {'ok': False, 'msg': "No podés responder tu propio canto."}
        if self.truco_state is None:
            return {'ok': False, 'msg': "No hay truco cantado."}
 
        # Subir la apuesta (solo quien tiene la palabra puede hacerlo)
        if response in ('retruco', 'vale_cuatro'):
            if self.truco_word_holder != player:
                return {'ok': False, 'msg': "No tenés la palabra para levantar la apuesta."}
            return self.call_truco(player, response)
 
        if response == 'quiero':
            # Quien dice quiero obtiene la palabra y eleva el truco a 2 puntos
            self.truco_state = 'querido'
            self.truco_word_holder = player
            # Elevar el truco a 2 puntos cuando es querido
            self.truco_points = 2
            return {'ok': True, 'msg': f"{self.player_name(player)} quiere el truco. En juego: {self.truco_points} pts"}
 
        if response == 'no_quiero':
            self.truco_resolved = True
            # El que cantó gana los puntos del canto (menos 1 si no fue el primer truco)
            puntos_ganados_tabla = {'truco': 1, 'retruco': 2, 'vale_cuatro': 3}
            pts_ganados = puntos_ganados_tabla.get(self.truco_state, 1)
            self.score[self.truco_caller] += pts_ganados
            self.hand_over   = True
            self.hand_winner = self.truco_caller + 1
            return {
                'ok':     True,
                'msg':    f"{self.player_name(player)} no quiere. {self.player_name(self.truco_caller)} suma {pts_ganados} pts.",
                'hand_over': True
            }
 
        return {'ok': False, 'msg': f"Respuesta inválida: {response}"}
 
    # ─────────────────────────────────────────────
    # ENVIDO
    # ─────────────────────────────────────────────
 
    def _waiting_for_envido_response(self, player):
        """True si hay un canto de envido pendiente que el jugador debe responder."""
        return (
            self.envido_state in ('envido', 'real_envido', 'falta_envido') and
            self.envido_caller != player and
            not self.envido_resolved
        )
 
    def _waiting_for_flower_response(self, player):
        return (
            self.flower_state in ('la_mia', 'con_flor_envido', 'contra_flor') and
            self.flower_caller != player and
            not self.flower_resolved and
            len(self.flowers_declared) > 1  # solo si ambos tienen flor
        )
 
    def can_call_envido(self, player):
        if self.envido_resolved:
            return False, "El envido ya terminó."
        if len(self.rounds) > 0:
            return False, "El envido solo se puede cantar antes de la segunda baza."
        env = self.envido_of(player)
        if env == -1:
            return False, "Tenés flor, no podés cantar envido."
        # Verificar si el rival tiene flor
        rival = self.rival_of(player)
        if self.envido_of(rival) == -1:
            return False, f"{self.player_name(rival)} tiene flor, no se puede cantar envido."
        if self.envido_caller == player:
            return False, "No podés subir tu propio canto."
        return True, ""
 
    def call_envido(self, player, tipo):
        """tipo: 'envido', 'real_envido', 'falta_envido'"""
        ok, msg = self.can_call_envido(player)
        if not ok:
            return {'ok': False, 'msg': msg}
 
        orden = [None, 'envido', 'real_envido', 'falta_envido']
        current_idx = orden.index(self.envido_state)
        tipo_idx    = orden.index(tipo)
 
        if tipo_idx <= current_idx and self.envido_state is not None:
            return {'ok': False, 'msg': f"No podés bajar la apuesta del envido."}
 
        # Acumular puntos según tabla oficial
        puntos_acumulados = {
            (None,          'envido'):        2,
            (None,          'real_envido'):   3,
            (None,          'falta_envido'):  0,  # se calcula al resolver
            ('envido',      'envido'):        4,
            ('envido',      'real_envido'):   5,
            ('envido',      'falta_envido'):  0,
            ('real_envido', 'falta_envido'):  0,
        }
        self.envido_points = puntos_acumulados.get((self.envido_state, tipo), self.envido_points)
        self.envido_state  = tipo
        self.envido_caller = player
 
        return {'ok': True, 'msg': f"{self.player_name(player)} canta: {tipo.replace('_', ' ').upper()}"}
 
    def respond_envido(self, player, response):
        """response: 'quiero', 'no_quiero', 'envido', 'real_envido', 'falta_envido'"""
        if self.envido_caller == player:
            return {'ok': False, 'msg': "No podés responder tu propio canto."}
        if self.envido_state is None:
            return {'ok': False, 'msg': "No hay envido cantado."}
        if self.envido_resolved:
            return {'ok': False, 'msg': "El envido ya fue resuelto."}
        
        # Si tienes flor, el envido se anula (no suma nada)
        if self.envido_of(player) == -1:
            self.envido_resolved = True
            return {
                'ok': True,
                'msg': f"{self.player_name(player)} tiene flor. El envido se anula."
            }
 
        if response in ('envido', 'real_envido', 'falta_envido'):
            return self.call_envido(player, response)
 
        if response == 'quiero':
            self.envido_resolved = True
            return self._resolve_envido()
 
        if response == 'no_quiero':
            self.envido_resolved = True
            # El que cantó gana 1 punto (o la suma de los queridos anteriores)
            pts = max(1, self.envido_points - 1) if self.envido_points > 0 else 1
            self.score[self.envido_caller] += pts
            return {
                'ok':  True,
                'msg': f"{self.player_name(player)} no quiere. {self.player_name(self.envido_caller)} suma {pts} pts."
            }
 
        return {'ok': False, 'msg': f"Respuesta inválida: {response}"}
 
    def _resolve_envido(self):
        """Compara envidos y asigna puntos."""
        e1 = self.envido_of(0)
        e2 = self.envido_of(1)
 
        if self.envido_state == 'falta_envido':
            # Gana los puntos que le faltan al equipo que va primero para llegar a 40
            winner_idx = 0 if e1 >= e2 else 1
            pts = self.POINTS_TO_WIN - self.score[winner_idx]
        else:
            pts        = self.envido_points
            winner_idx = 0 if e1 >= e2 else 1
 
        self.score[winner_idx] += pts
        loser_idx = 1 - winner_idx
 
        return {
            'ok':      True,
            'msg':     (f"Envido querido! {self.player_name(0)}: {e1} pts | "
                        f"{self.player_name(1)}: {e2} pts\n"
                        f"  → {self.player_name(winner_idx)} gana {pts} pts de envido."),
            'winner':  winner_idx,
            'pts':     pts,
            'e1':      e1,
            'e2':      e2
        }
 
    # ─────────────────────────────────────────────
    # FLOR
    # ─────────────────────────────────────────────
 
    def call_flower(self, player, tipo):
        """
        tipo: 'la_mia', 'con_flor_envido', 'contra_flor', 'contra_flor_al_resto'
        Solo válido si el jugador tiene flor.
        Solo se puede cantar 'la_mia' en esta versión.
        """
        if player not in self.flowers_declared:
            return {'ok': False, 'msg': "No tenés flor."}
        if self.flower_resolved:
            return {'ok': False, 'msg': "La flor ya fue resuelta."}
        if len(self.rounds) > 0:
            return {'ok': False, 'msg': "La flor debe cantarse antes de jugar la primera carta."}
        
        # Solo se permite cantar 'la_mia' en esta versión
        if tipo != 'la_mia':
            return {'ok': False, 'msg': "Solo se puede decir 'La Mía es Flor' cuando hay flor."}

        self.flower_state  = tipo
        self.flower_caller = player
 
        # Si solo un equipo tiene flor, se le dan 3 pts directamente al final
        if len(self.flowers_declared) == 1:
            if tipo == 'la_mia':
                return {'ok': True, 'msg': f"{self.player_name(player)} canta: ¡LA MÍA FLOR! (3 pts al final de la mano)"}
            else:
                return {'ok': False, 'msg': "Solo podés cantar 'la_mia' si el rival no tiene flor."}
 
        # Ambos tienen flor
        puntos = {'la_mia': 3, 'con_flor_envido': 5, 'contra_flor': 0, 'contra_flor_al_resto': 0}
        return {'ok': True, 'msg': f"{self.player_name(player)} canta: {tipo.replace('_', ' ').upper()}"}
 
    def respond_flower(self, player, response):
        """response: 'la_mia', 'con_flor_envido', 'contra_flor', 'contra_flor_al_resto'"""
        if self.flower_caller == player:
            return {'ok': False, 'msg': "No podés responder tu propio canto de flor."}
 
        self.flower_resolved = True
        self.flower_state    = response
 
        f1 = self.flower_value_of(0)
        f2 = self.flower_value_of(1)
        winner_idx = 0 if f1 >= f2 else 1
 
        if response == 'con_flor_envido':
            pts = 5
        elif response == 'contra_flor':
            pts = 0  # gana la flor más alta, sin puntos extra fijos
            # La contra_flor otorga la flor del rival al ganador
            pts = f1 + f2  # simplificado: suma de ambas flores
        elif response == 'contra_flor_al_resto':
            pts = self.POINTS_TO_WIN - self.score[winner_idx]
        else:
            pts = 3
 
        self.score[winner_idx] += pts
        return {
            'ok':  True,
            'msg': (f"Flor resuelta! {self.player_name(0)}: {f1} | {self.player_name(1)}: {f2}\n"
                    f"  → {self.player_name(winner_idx)} gana {pts} pts de flor."),
            'winner': winner_idx,
            'pts': pts
        }
 
    def resolve_single_flower(self):
        """Si solo un jugador tiene flor, al final de la mano suma 3 pts."""
        if len(self.flowers_declared) == 1 and not self.flower_resolved:
            idx = self.flowers_declared[0]
            self.score[idx] += 3
            self.flower_resolved = True
            return {'ok': True, 'msg': f"{self.player_name(idx)} suma 3 pts por flor."}
        return {'ok': False, 'msg': ""}
 
    # ─────────────────────────────────────────────
    # PARTIDA
    # ─────────────────────────────────────────────
 
    def game_winner(self):
        """Retorna 1, 2 o None si no hay ganador aún."""
        if self.score[0] >= self.POINTS_TO_WIN:
            return 1
        if self.score[1] >= self.POINTS_TO_WIN:
            return 2
        return None
 
    def score_str(self):
        return f"Jugador 1: {self.score[0]} pts  |  Jugador 2: {self.score[1]} pts"
 
    def next_hand(self):
        """Prepara la siguiente mano alternando quién es mano."""
        self.mano_player = 1 - self.mano_player
        self.deal()





