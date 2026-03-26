"""
train_enhanced.py
-----------------
Entrenamiento avanzado del agente RL con monitoreo en tiempo real.

Uso:
    python train_enhanced.py --steps 500000 --eval-freq 10000
    
    # Solo evaluar un modelo
    python train_enhanced.py --eval-only truco_agent_50k
    
    # Self-play (entrenar contra versiones anteriores)
    python train_enhanced.py --selfplay truco_agent_50k
"""

import os
import numpy as np
from pathlib import Path
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from truco_env import TrucoEnv


class TrucoTrainingCallback(BaseCallback):
    """Callback para monitorear entrenamiento en tiempo real."""
    
    def __init__(self, eval_freq=10_000, verbose=1):
        super().__init__(verbose)
        self.eval_freq = eval_freq
        self.manos_totales = 0
        self.victorias = 0
        self.paso_anterior = 0
        
    def _on_step(self):
        # Contar manos y victorias
        if hasattr(self.model.env, 'envs'):
            # Entorno vectorizado
            for env in self.model.env.envs:
                if hasattr(env, 'unwrapped'):
                    env_unwrapped = env.unwrapped
                    if hasattr(env_unwrapped, 'engine'):
                        if env_unwrapped.engine.hand_over:
                            self.manos_totales += 1
                            if env_unwrapped.engine.hand_winner == 0:
                                self.victorias += 1
        
        # Mostrar progreso cada eval_freq pasos
        if self.n_calls - self.paso_anterior >= self.eval_freq:
            self.paso_anterior = self.n_calls
            if self.manos_totales > 0:
                wr = self.victorias / self.manos_totales
                print(f"\n  📊 PROGRESO")
                print(f"     Timesteps:      {self.num_timesteps:>10,}")
                print(f"     Manos jugadas:  {self.manos_totales:>10}")
                print(f"     Victorias:      {self.victorias:>10}")
                print(f"     Win Rate:       {wr:>10.1%}")
                print()
        
        return True


def entrenar(timesteps=500_000, eval_freq=10_000, nombre_modelo="truco_agent"):
    """Entrenar un nuevo agente."""
    
    print("\n" + "="*70)
    print("   ENTRENAMIENTO DEL AGENTE RL - TRUCO URUGUAYO")
    print("="*70)
    print(f"   Timesteps total:        {timesteps:,}")
    print(f"   Evaluación cada:        {eval_freq:,} timesteps")
    print(f"   Modelo guardado como:   {nombre_modelo}.zip")
    print(f"   Oponente:               Aleatorio (estrategia aleatoria)")
    print("="*70)
    
    # Crear entorno
    print("\n   Creando entorno...")
    env = TrucoEnv(opponent="random")
    
    # Crear modelo PPO con buenos hiperparámetros
    print("   Inicializando modelo PPO...")
    model = PPO(
        "MlpPolicy",
        env,
        verbose=0,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        policy_kwargs={"net_arch": [256, 256]},
        device="cpu",  # Usar CPU (compatible con Windows)
        tensorboard_log="./logs"
    )
    
    callback = TrucoTrainingCallback(eval_freq=eval_freq, verbose=1)
    
    print("\n   Iniciando entrenamiento...\n")
    
    try:
        model.learn(
            total_timesteps=timesteps,
            callback=callback,
            progress_bar=True
        )
    except KeyboardInterrupt:
        print("\n\n    Entrenamiento interrumpido por usuario.")
    
    # Guardar modelo
    ruta_modelo = Path(nombre_modelo)
    model.save(str(ruta_modelo))
    print(f"\n  Modelo guardado: {ruta_modelo}.zip")
    
    return model


def evaluar(nombre_modelo="truco_agent", n_manos=500):
    """Evaluar un modelo contra oponente aleatorio."""
    
    print("\n" + "="*70)
    print("  EVALUACIÓN DEL MODELO")
    print("="*70)
    print(f"  Modelo:        {nombre_modelo}")
    print(f"  Manos:         {n_manos}")
    print(f"  Oponente:      Aleatorio")
    print("="*70)
    
    try:
        model = PPO.load(nombre_modelo)
    except FileNotFoundError:
        print(f"  No se encontró el modelo: {nombre_modelo}.zip")
        return
    
    env = TrucoEnv(opponent="random")
    
    victorias = 0
    empates = 0
    derrotas = 0
    puntos_ganados = 0
    puntos_perdidos = 0

    print(f"\n  Evaluando {n_manos} manos...\n")
    
    for mano_num in range(n_manos):
        obs, _ = env.reset()
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        
        # Resultado
        score_j0 = env.engine.score[0]
        score_j1 = env.engine.score[1]
        
        if score_j0 > score_j1:
            victorias += 1
            puntos_ganados += score_j0 - score_j1
        elif score_j0 < score_j1:
            derrotas += 1
            puntos_perdidos += score_j1 - score_j0
        else:
            empates += 1
        
        # Mostrar cada 100 manos
        if (mano_num + 1) % 100 == 0:
            wr_actual = victorias / (mano_num + 1)
            print(f"    Mano {mano_num + 1:>4}/{n_manos}  |  "
                  f"W: {victorias:>3}  L: {derrotas:>3}  D: {empates:>3}  |  "
                  f"Win Rate: {wr_actual:.1%}")
    
    wr_final = victorias / n_manos
    
    print("\n" + "="*70)
    print(f"  RESULTADOS FINALES")
    print("="*70)
    print(f"  Victorias:     {victorias:>4}  ({victorias/n_manos:.1%})")
    print(f"  Derrotas:      {derrotas:>4}  ({derrotas/n_manos:.1%})")
    print(f"  Empates:       {empates:>4}  ({empates/n_manos:.1%})")
    print(f"  Puntos netos:  {puntos_ganados - puntos_perdidos:>+4}")
    print("="*70)
    print(f"\n  Win Rate vs Aleatorio: {wr_final:.1%}")
    print(f"     (Un agente aleatorio = 50%)")
    print(f"     (Bien entrenado: 65-75%+)")
    print()


def selfplay(nombre_base="truco_agent", timesteps=100_000, n_eval=200):
    """Entrenar mediante self-play: nueva versión vs anterior."""
    
    print("\n" + "="*70)
    print("  SELF-PLAY: Entrenar contra versión anterior")
    print("="*70)
    
    # Cargar modelo anterior como oponente
    try:
        model_anterior = PPO.load(nombre_base)
    except FileNotFoundError:
        print(f"  No se encontró: {nombre_base}.zip")
        return
    
    print(f"  Oponente:      {nombre_base}")
    print(f"  Timesteps:     {timesteps:,}")
    print(f"  Evaluación:    {n_eval} manos")
    print("="*70)
    
    # Entrenar contra el modelo anterior
    env = TrucoEnv(opponent=model_anterior)
    model = PPO.load(nombre_base, env=env)
    
    print(f"\n  Entrenando {timesteps:,} timesteps vs versión anterior...\n")
    
    callback = TrucoTrainingCallback(eval_freq=timesteps//10, verbose=1)
    model.learn(total_timesteps=timesteps, callback=callback, progress_bar=True)
    
    # Evaluar contra modelo anterior
    print(f"\n  Evaluando nuevo modelo vs anterior...")
    env_eval = TrucoEnv(opponent=model_anterior)
    
    victorias = 0
    for _ in range(n_eval):
        obs, _ = env_eval.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, term, trunc, _ = env_eval.step(action)
            done = term or trunc
        if env_eval.engine.hand_winner == 0:
            victorias += 1
    
    wr = victorias / n_eval
    
    print(f"  Win rate del nuevo modelo: {wr:.1%}")
    
    if wr > 0.52:  # Mejoró al menos 2%
        model.save(nombre_base)
        print(f"  Nuevo modelo guardado (mejoró)")
    else:
        print(f"   Modelo no mejoró, se mantiene anterior")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description=" Entrenamiento avanzado RL para Truco Uruguayo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  
  1. Entrenar nuevo modelo:
     python train_enhanced.py --steps 500000
  
  2. Evaluar modelo existente:
     python train_enhanced.py --eval-only truco_agent_50k
  
  3. Self-play (entrenar contra versión anterior):
     python train_enhanced.py --selfplay truco_agent_50k
        """
    )
    
    parser.add_argument("--steps",      type=int,   default=500_000, 
                        help="Timesteps de entrenamiento (default: 500k)")
    parser.add_argument("--eval-freq",  type=int,   default=20_000,
                        help="Mostrar progreso cada N timesteps")
    parser.add_argument("--nombre",     type=str,   default="truco_agent",
                        help="Nombre del archivo del modelo")
    parser.add_argument("--eval-only",  type=str,   metavar="MODELO",
                        help="Solo evaluar un modelo existente")
    parser.add_argument("--n-eval",     type=int,   default=500,
                        help="Manos a evaluar (default: 500)")
    parser.add_argument("--selfplay",   type=str,   metavar="MODELO",
                        help="Self-play contra modelo especificado")
    
    args = parser.parse_args()
    
    if args.eval_only:
        evaluar(args.eval_only, args.n_eval)
    elif args.selfplay:
        selfplay(args.selfplay, args.steps, args.n_eval)
    else:
        entrenar(args.steps, args.eval_freq, args.nombre)
        print("\n   Ahora evaluando modelo...\n")
        evaluar(args.nombre, args.n_eval)
