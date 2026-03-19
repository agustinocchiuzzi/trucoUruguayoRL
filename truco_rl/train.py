"""
train.py
--------
Entrenamiento del agente de RL para Truco Uruguayo.
 
Ejecutar:
    python train.py
 
Requiere:
    pip install stable-baselines3 gymnasium
    (opcional para action masking): pip install sb3-contrib
"""
 
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback
from stable_baselines3.common.evaluation import evaluate_policy
from truco_env import TrucoEnv
 
 
# ─────────────────────────────────────────────
# CALLBACK: muestra win rate durante entreno
# ─────────────────────────────────────────────
 
class TrucoCallback(BaseCallback):
    """
    Muestra estadísticas de entrenamiento cada N pasos.
    """
 
    def __init__(self, check_freq=10_000, verbose=1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.wins  = 0
        self.games = 0
 
    def _on_step(self):
        # stable-baselines3 envuelve el env en Monitor, no podemos acceder
        # a env.wins directamente. Leemos reward y done de cada step:
        # reward > 0 al terminar significa que J0 ganó la mano.
        dones   = self.locals.get("dones",   [])
        rewards = self.locals.get("rewards", [])
        for done, reward in zip(dones, rewards):
            if done:
                self.games += 1
                if reward > 0:
                    self.wins += 1
 
        if self.n_calls % self.check_freq == 0 and self.games > 0:
            wr = self.wins / self.games
            if self.verbose:
                print(f"  [paso {self.num_timesteps:>8,}]  "
                      f"win rate: {wr:.1%}  |  "
                      f"manos jugadas: {self.games}")
        return True
 
 
# ─────────────────────────────────────────────
# ENTRENAMIENTO PRINCIPAL
# ─────────────────────────────────────────────
 
def train(total_timesteps=300_000, save_path="truco_ppo"):
 
    print("=" * 55)
    print("  ENTRENAMIENTO — Truco Uruguayo RL")
    print("=" * 55)
    print(f"  Timesteps:  {total_timesteps:,}")
    print(f"  Algoritmo:  PPO (Proximal Policy Optimization)")
    print(f"  Oponente:   Aleatorio")
    print(f"  Guardado en: {save_path}.zip")
    print("=" * 55)
 
    # Crear entorno
    env = TrucoEnv(opponent="random")
 
    # Crear modelo PPO
    # MlpPolicy = red neuronal densa (Multi-Layer Perceptron)
    # Adecuada para vectores de estado como el nuestro (135 valores)
    model = PPO(
        "MlpPolicy",
        env,
        verbose=0,
        learning_rate=3e-4,
        n_steps=2048,         # pasos por actualización
        batch_size=64,
        n_epochs=10,
        gamma=0.99,           # descuento de recompensas futuras
        gae_lambda=0.95,      # ventaja generalizada
        clip_range=0.2,
        ent_coef=0.01,        # coeficiente de entropía (fomenta exploración)
        policy_kwargs={
            "net_arch": [256, 256],   # 2 capas de 256 neuronas
        }
    )
 
    callback = TrucoCallback(check_freq=10_000)
 
    print("\n  Entrenando...\n")
    model.learn(total_timesteps=total_timesteps, callback=callback)
 
    # Guardar modelo
    model.save(save_path)
    print(f"\n  ✅ Modelo guardado en '{save_path}.zip'")
 
    return model
 
 
# ─────────────────────────────────────────────
# EVALUACIÓN
# ─────────────────────────────────────────────
 
def evaluate(model_path="truco_ppo", n_episodes=200):
    print(f"\n  Evaluando modelo '{model_path}'...")
 
    model = PPO.load(model_path)
    env   = TrucoEnv(opponent="random")
 
    wins = 0
    for ep in range(n_episodes):
        obs, _ = env.reset()
        done   = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        if env.engine.hand_winner == 0:
            wins += 1
 
    wr = wins / n_episodes
    print(f"  Win rate vs aleatorio: {wr:.1%}  ({wins}/{n_episodes} manos)")
    print(f"  (Un agente aleatorio tiene ~50%. Bien entrenado debería superar 60-70%)")
    return wr
 
 
# ─────────────────────────────────────────────
# SELF-PLAY (avanzado)
# ─────────────────────────────────────────────
 
def self_play_iteration(model_path="truco_ppo", timesteps=100_000):
    """
    Una iteración de self-play:
    - Carga el modelo actual como oponente
    - Entrena una nueva versión contra él
    - Guarda si mejora
    """
    from stable_baselines3 import PPO
 
    print("\n  === ITERACIÓN DE SELF-PLAY ===")
 
    # Cargar modelo anterior como oponente
    opponent_model = PPO.load(model_path)
 
    env_selfplay = TrucoEnv(opponent=opponent_model)
    new_model    = PPO.load(model_path, env=env_selfplay)
 
    new_model.learn(total_timesteps=timesteps)
 
    # Evaluar si el nuevo modelo es mejor que el anterior
    wins = 0
    eval_env = TrucoEnv(opponent=opponent_model)
    obs, _   = eval_env.reset()
    for _ in range(200):
        done = False
        obs, _ = eval_env.reset()
        while not done:
            action, _ = new_model.predict(obs, deterministic=True)
            obs, _, term, trunc, _ = eval_env.step(action)
            done = term or trunc
        if eval_env.engine.hand_winner == 0:
            wins += 1
 
    wr = wins / 200
    print(f"  Win rate del nuevo modelo vs anterior: {wr:.1%}")
 
    if wr > 0.52:  # mejora mínima del 2%
        new_model.save(model_path)
        print(f"  ✅ Nuevo modelo guardado (mejoró).")
    else:
        print(f"  ⚠️  Modelo no mejoró, se mantiene el anterior.")
 
    return wr
 
 
# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
 
if __name__ == "__main__":
    import argparse
 
    parser = argparse.ArgumentParser(description="Entrenamiento RL Truco Uruguayo")
    parser.add_argument("--steps",    type=int,   default=300_000, help="Timesteps de entrenamiento")
    parser.add_argument("--save",     type=str,   default="truco_ppo", help="Nombre del archivo a guardar")
    parser.add_argument("--eval",     action="store_true", help="Solo evaluar un modelo existente")
    parser.add_argument("--selfplay", action="store_true", help="Ejecutar iteración de self-play")
    args = parser.parse_args()
 
    if args.eval:
        evaluate(args.save)
    elif args.selfplay:
        self_play_iteration(args.save)
    else:
        model = train(total_timesteps=args.steps, save_path=args.save)
        evaluate(args.save)