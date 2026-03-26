"""
play_with_trained_agent.py
--------------------------
Jugar contra un modelo RL entrenado.

Uso:
    python play_with_trained_agent.py --model truco_agent_50k
"""

import sys
import argparse
from stable_baselines3 import PPO
from Truco import Truco
from Main import show_state, show_help, pause, fmt_card, process_command, clear, header, line


class TrainedRLAgent:
    """Agente que usa un modelo PPO entrenado."""
    
    def __init__(self, model_path):
        try:
            self.model = PPO.load(model_path)
            print(f"   Modelo cargado: {model_path}")
        except FileNotFoundError:
            print(f"   Model no encontrado: {model_path}.zip")
            sys.exit(1)
        
        # Importar el entorno para obtener la función de codificación
        from truco_env import TrucoEnv
        self.dummy_env = TrucoEnv()
    
    def decide_action(self, truco: Truco):
        """
        Decide una acción usando el modelo entrenado.
        Retorna una acción válida según el modelo.
        """
        player = 0  # El agente siempre es J1
        
        # Codificar el estado del juego
        obs = self._encode_state(truco)
        
        # Predecir acción
        action_idx, _ = self.model.predict(obs, deterministic=True)
        
        # Convertir índice a acción
        return self._action_from_index(action_idx, truco, player)
    
    def _encode_state(self, truco: Truco):
        """Codificar el estado para el modelo."""
        import numpy as np
        
        # Usar el mismo encoding que en TrucoEnv
        hand = truco.hand_of(0)
        hand_one_hot = np.zeros(40)
        for idx in hand:
            hand_one_hot[idx] = 1
        
        played = np.zeros(40)
        for card in truco.played[0] + truco.played[1]:
            played[card.index if hasattr(card, 'index') else card] = 1
        
        features = np.concatenate([
            hand_one_hot,
            played,
            np.array([
                truco.turn == 0,
                truco.envido_state is not None,
                truco.truco_state is not None,
                truco.flower_state is not None,
                truco.score[0] / 30,
                truco.score[1] / 30,
                len(truco.rounds) / 3,
            ])
        ])
        
        return features.astype(np.float32)
    
    def _action_from_index(self, action_idx, truco, player=0):
        """Convertir índice de acción a acción válida."""
        acciones = [
            ('play_card', 0),
            ('play_card', 1),
            ('play_card', 2),
            ('call_envido', 'envido'),
            ('respond_envido', 'quiero'),
            ('respond_envido', 'no_quiero'),
            ('call_truco', 'truco'),
            ('respond_truco', 'quiero'),
            ('respond_truco', 'no_quiero'),
            ('call_flower', 'la_mia'),
            ('respond_flower', 'la_mia'),
        ]
        
        action = acciones[action_idx] if action_idx < len(acciones) else ('play_card', 0)
        
        # Validar que sea una acción legal
        hand = truco.hand_of(player)
        if action[0] == 'play_card':
            card_idx = action[1]
            if card_idx >= len(hand):
                card_idx = 0
            return ('play_card', card_idx)
        
        return action


def play_with_trained_agent(model_path="truco_agent"):
    """Juego contra agente entrenado."""
    
    clear()
    header("  TRUCO URUGUAYO vs AGENTE ENTRENADO")
    print(f"\n  📦 Modelo:  {model_path}")
    print(f"   J1:     RL Agent (entrenado)")
    print(f"   J2:     Tú (manual)")
    print(f"\n  Partida a {Truco.POINTS_TO_WIN} puntos.\n")
    
    input("  Presioná ENTER para comenzar...")
    
    agent = TrainedRLAgent(model_path)
    truco = Truco()
    
    while not truco.game_winner():
        play_hand(agent, truco)
        truco.mano_player = 1 - truco.mano_player
    
    clear()
    winner = truco.game_winner()
    header("🏆  FIN DE LA PARTIDA")
    print(f"\n    ¡{truco.player_name(winner - 1)} gana!")
    print(f"\n    {truco.score_str()}")
    line()


def play_hand(agent: TrainedRLAgent, truco: Truco):
    """Loop de una mano."""
    
    agent_obj = agent  # Guardar referencia al agente
    truco.deal()
    msg = ""
    
    if truco.flowers_declared:
        flores = [truco.player_name(p) for p in truco.flowers_declared]
        msg = f"  ¡Tiene(n) flor: {', '.join(flores)}!"
    
    while not truco.hand_over:
        show_state(truco, msg)
        msg = ""
        
        # Turno del agente
        if truco.turn == 0:
            print(f"\n    Agente entrenado está pensando...\n")
            pause()
            
            action = agent_obj.decide_action(truco)
            
            if action[0] == 'play_card':
                res = truco.play_card(0, action[1])
                if res['ok']:
                    msg = f"  Agente juega: {fmt_card(res['card'])}"
                    if res.get('baza_done'):
                        w = res.get('baza_winner', 'empate')
                        msg += f"\n  ⚔️  Baza: {w}"
            
            elif action[0] == 'call_envido':
                res = truco.call_envido(0, action[1])
                if res['ok']:
                    msg = res['msg']
                    truco.turn = 1
            
            elif action[0] == 'respond_envido':
                res = truco.respond_envido(0, action[1])
                if res['ok']:
                    msg = res['msg']
            
            elif action[0] == 'call_truco':
                res = truco.call_truco(0, action[1])
                if res['ok']:
                    msg = res['msg']
                    truco.turn = 1
            
            elif action[0] == 'respond_truco':
                res = truco.respond_truco(0, action[1])
                if res['ok']:
                    msg = res['msg']
            
            elif action[0] == 'call_flower':
                res = truco.call_flower(0, action[1])
                if res['ok']:
                    msg = res['msg']
                    if len(truco.flowers_declared) > 1:
                        truco.turn = 1
            
            elif action[0] == 'respond_flower':
                res = truco.respond_flower(0, action[1])
                if res['ok']:
                    msg = res['msg']
        
        # Turno del humano
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
                msg = f"  {res['msg']}"
                pause()
                continue
            
            msg = res.get('msg', '')
            
            if res.get('hand_over'):
                show_state(truco, msg)
                print(f"\n    {truco.score_str()}")
                pause()
                return
        
        if truco.hand_over:
            show_state(truco, msg)
            print(f"\n    {truco.score_str()}")
            pause()
            return
    
    show_state(truco, msg)
    print(f"\n    {truco.score_str()}")
    pause()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jugar contra agente RL entrenado")
    parser.add_argument("--model", type=str, default="truco_agent",
                       help="Ruta del modelo entrenado (sin .zip)")
    args = parser.parse_args()
    
    play_with_trained_agent(args.model)
