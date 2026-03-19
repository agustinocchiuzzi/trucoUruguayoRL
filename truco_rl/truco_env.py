"""
truco_env.py
------------
Entorno Gymnasium para entrenar un agente de RL en Truco Uruguayo 1v1.
 
Uso básico:
    env = TrucoEnv()
    obs, info = env.reset()
    done = False
    while not done:
        action = env.action_space.sample()          # agente aleatorio
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
 
Para entrenar con stable-baselines3:
    from stable_baselines3 import PPO
    from truco_env import TrucoEnv
 
    env = TrucoEnv()
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=500_000)
 
NOTAS SOBRE EL DISEÑO:
  - El agente siempre juega como J0.
  - J1 es un oponente interno (por defecto: aleatorio entre acciones legales).
  - Podés reemplazar el oponente con otro agente entrenado (self-play).
  - Las acciones ilegales están enmascaradas: si el agente elige una acción
    ilegal, el entorno la ignora y elige aleatoriamente entre las legales.
  - La recompensa es acumulada al final de la mano (sparse reward).
"""
 
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from truco_engine import TrucoEngine, N_ACTIONS, ACTION_NAMES
 
 
class TrucoEnv(gym.Env):
    """
    Entorno Gymnasium 1v1 de Truco Uruguayo.
 
    observation_space: Box(135,) — vector de estado visible para el agente
    action_space:      Discrete(11) — acciones posibles (ver truco_engine.py)
 
    El agente es siempre J0. J1 es un oponente configurable.
    """
 
    metadata = {"render_modes": ["human"]}
 
    def __init__(self, opponent="random", render_mode=None):
        super().__init__()
        self.engine      = TrucoEngine()
        self.opponent    = opponent   # "random" o un modelo con .predict()
        self.render_mode = render_mode
 
        # Espacios
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(135,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(N_ACTIONS)
 
        # Estadísticas de entrenamiento
        self.episode_rewards = []
        self.wins  = 0
        self.games = 0
 
    # ─────────────────────────────────────────────
    # RESET
    # ─────────────────────────────────────────────
 
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        obs = self.engine.reset()
 
        # Si el primer turno es del oponente (J1), lo ejecutamos
        obs = self._maybe_opponent_moves(obs)
 
        info = {
            "score":       list(self.engine.score),
            "has_flower":  self.engine.has_flower,
            "legal_actions": self.engine.legal_actions(),
        }
        return obs, info
 
    # ─────────────────────────────────────────────
    # STEP
    # ─────────────────────────────────────────────
 
    def step(self, action):
        """
        Ejecuta la acción del agente (J0).
        Si la acción es ilegal, se elige aleatoriamente entre las legales.
        """
        # Mano ya terminada — no debería ocurrir, pero lo manejamos
        if self.engine.done:
            obs = self.engine.observation(perspective=0)
            return obs, 0.0, True, False, {
                "score": list(self.engine.score), "legal_actions": []
            }
 
        legal = self.engine.legal_actions()
 
        # Sin acciones legales disponibles — terminar episodio
        if not legal:
            obs = self.engine.observation(perspective=0)
            return obs, 0.0, True, False, {
                "score": list(self.engine.score), "legal_actions": []
            }
 
        # Enmascarar acción ilegal
        if int(action) not in legal:
            action = int(np.random.choice(legal))
 
        obs, rewards, done, info = self.engine.step(int(action))
        agent_reward = float(rewards[0])
        terminated   = False
        truncated    = False
 
        if done:
            terminated = True
        else:
            # Ejecutar turnos del oponente (J1) hasta que sea turno de J0
            obs = self._maybe_opponent_moves(obs)
            if self.engine.done:
                terminated   = True
                agent_reward += float(self.engine.last_rewards[0])
 
        if terminated:
            self.episode_rewards.append(agent_reward)
            self.games += 1
            if self.engine.hand_winner == 0:
                self.wins += 1
            info["win_rate"] = self.wins / self.games
 
        info["score"]         = list(self.engine.score)
        info["legal_actions"] = self.engine.legal_actions()
 
        return obs, agent_reward, terminated, truncated, info
 
    # ─────────────────────────────────────────────
    # OPONENTE
    # ─────────────────────────────────────────────
 
    def _maybe_opponent_moves(self, obs):
        """
        Ejecuta turnos del oponente (J1) hasta que sea el turno del agente (J0)
        o hasta que la mano termine.
        """
        while not self.engine.done and self.engine.turn == 1:
            legal = self.engine.legal_actions()
            if not legal:
                break
            action = self._opponent_action(obs, legal)
            obs, _, _, _ = self.engine.step(action)
        return obs
 
    def _opponent_action(self, obs, legal_actions):
        """Elige la acción del oponente según la política configurada."""
        if self.opponent == "random":
            return int(np.random.choice(legal_actions))
 
        # Oponente con modelo entrenado (self-play)
        if hasattr(self.opponent, "predict"):
            obs_j1 = self.engine.observation(perspective=1)
            action, _ = self.opponent.predict(obs_j1, deterministic=True)
            if int(action) in legal_actions:
                return int(action)
            return int(np.random.choice(legal_actions))
 
        return int(np.random.choice(legal_actions))
 
    # ─────────────────────────────────────────────
    # RENDER
    # ─────────────────────────────────────────────
 
    def render(self):
        if self.render_mode == "human":
            self.engine.render(perspective=0)
 
    # ─────────────────────────────────────────────
    # ACTION MASK (para algoritmos que la soportan)
    # ─────────────────────────────────────────────
 
    def action_masks(self):
        """
        Retorna un array booleano de shape (N_ACTIONS,) indicando
        qué acciones son legales. Útil para MaskablePPO de sb3-contrib.
        """
        mask  = np.zeros(N_ACTIONS, dtype=bool)
        legal = self.engine.legal_actions()
        for a in legal:
            mask[a] = True
        return mask
 