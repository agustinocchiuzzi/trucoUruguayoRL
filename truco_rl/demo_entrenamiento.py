"""
demo_entrenamiento.py
---------------------
Demostración rápida del entrenamiento RL.
Entrena un modelo pequeño en ~2 minutos para que veas cómo funciona.

Uso:
    python demo_entrenamiento.py
"""

from stable_baselines3 import PPO
from truco_env import TrucoEnv
import time


def demo():
    print("\n" + "="*70)
    print("  🤖 DEMOSTRACIÓN RÁPIDA DE ENTRENAMIENTO RL")
    print("="*70)
    print("""
  En esta demostración vas a:
  1. Ver cómo se entrena un modelo
  2. Evaluar su progreso
  3. Jugar contra él
  
  ⏱️  Tiempo total: ~2-3 minutos
  """)
    print("="*70)
    
    # ─────────────────────────────────────────────
    # PASO 1: Crear entorno
    # ─────────────────────────────────────────────
    
    print("\n  📦 PASO 1: Creando entorno...")
    time.sleep(1)
    
    env = TrucoEnv(opponent="random")
    print("     ✅ Entorno creado")
    print(f"     - Observation space: {env.observation_space}")
    print(f"     - Action space: {env.action_space}")
    
    # ─────────────────────────────────────────────
    # PASO 2: Crear modelo
    # ─────────────────────────────────────────────
    
    print("\n  🧠 PASO 2: Inicializando modelo PPO...")
    time.sleep(1)
    
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
        device="cpu"
    )
    
    print("     ✅ Modelo creado")
    print("""     Configuración:
     - Algoritmo: PPO (Proximal Policy Optimization)
     - Red neural: 2 capas de 256 neuronas
     - Learning rate: 0.0003
     - Batch size: 64
     - Gamma (descuento): 0.99
    """)
    
    # ─────────────────────────────────────────────
    # PASO 3: Obtener baseline (modelo sin entrenar)
    # ─────────────────────────────────────────────
    
    print("  📊 PASO 3: Evaluando modelo SIN entrenar...")
    time.sleep(1)
    
    env_eval = TrucoEnv(opponent="random")
    wins_before = 0
    n_test = 100
    
    print(f"     Jugando {n_test} manos...")
    
    for ep in range(n_test):
        obs, _ = env_eval.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, term, trunc, _ = env_eval.step(action)
            done = term or trunc
        
        if env_eval.engine.hand_winner == 0:
            wins_before += 1
        
        if (ep + 1) % 25 == 0:
            print(f"     [{ep + 1:>3}/{n_test}] {wins_before:>2} victorias hasta ahora")
    
    wr_before = wins_before / n_test
    print(f"\n     ✅ Win rate inicial: {wr_before:.1%} ({wins_before}/{n_test})")
    print(f"        (Sin entrenar, esperamos ~50%)")
    
    # ─────────────────────────────────────────────
    # PASO 4: Entrenar
    # ─────────────────────────────────────────────
    
    print("\n  ⏳ PASO 4: Entrenando por 10,000 timesteps...")
    time.sleep(1)
    
    start_time = time.time()
    model.learn(total_timesteps=10_000, progress_bar=True)
    train_time = time.time() - start_time
    
    print(f"\n     ✅ Entrenamiento completado en {train_time:.1f} segundos")
    
    # ─────────────────────────────────────────────
    # PASO 5: Evaluar modelo entrenado
    # ─────────────────────────────────────────────
    
    print("\n  📊 PASO 5: Evaluando modelo ENTRENADO...")
    time.sleep(1)
    
    wins_after = 0
    
    print(f"     Jugando {n_test} manos...")
    
    for ep in range(n_test):
        obs, _ = env_eval.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, term, trunc, _ = env_eval.step(action)
            done = term or trunc
        
        if env_eval.engine.hand_winner == 0:
            wins_after += 1
        
        if (ep + 1) % 25 == 0:
            print(f"     [{ep + 1:>3}/{n_test}] {wins_after:>2} victorias hasta ahora")
    
    wr_after = wins_after / n_test
    print(f"\n     ✅ Win rate final: {wr_after:.1%} ({wins_after}/{n_test})")
    
    # ─────────────────────────────────────────────
    # RESUMEN
    # ─────────────────────────────────────────────
    
    improvement = (wr_after - wr_before) * 100
    
    print("\n" + "="*70)
    print("  📈 RESUMEN")
    print("="*70)
    print(f"  Win rate ANTES:     {wr_before:.1%}  ({wins_before}/{n_test} manos)")
    print(f"  Win rate DESPUÉS:   {wr_after:.1%}  ({wins_after}/{n_test} manos)")
    print(f"  Mejora:             {improvement:+.1f}%")
    print(f"  Tiempo de entreno:  {train_time:.1f} segundos")
    print("="*70)
    
    if improvement > 0:
        print(f"\n  ✅ ¡El modelo APRENDIÓ! Mejoró un {improvement:.1f}%")
        print(f"     Con más tiempo de entrenamiento (100k-500k timesteps),")
        print(f"     alcanzaría un win rate de 65-75%+")
    else:
        print(f"\n  ℹ️  El modelo aún no mejora significativamente.")
        print(f"     Necesita más tiempo de entrenamiento.")
    
    # ─────────────────────────────────────────────
    # INSTRUCCIONES SIGUIENTES
    # ─────────────────────────────────────────────
    
    print("\n" + "="*70)
    print("  🚀 PRÓXIMOS PASOS")
    print("="*70)
    print("""
  1. Entrenar un modelo más grande:
     
     python train_enhanced.py --steps 50000 --nombre demo_model_50k
  
  2. Ver el progreso en tiempo real (actualización cada 10k timesteps)
  
  3. Después del entrenamiento, evaluar:
     
     python train_enhanced.py --eval-only demo_model_50k --n-eval 500
  
  4. Jugar contra el modelo:
     
     python play_with_trained_agent.py --model demo_model_50k
  
  Para más detalles, lee: GUIA_ENTRENAMIENTO_RL.md
  """)
    print("="*70)
    
    # Guardar modelo demo
    model.save("demo_model_untrained")
    print(f"\n  💾 Modelo guardado como: demo_model_untrained.zip")


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Demostración interrumpida por usuario.")
    except Exception as e:
        print(f"\n  ❌ Error: {e}")
        print("""
  Asegúrate de:
  1. Estar en la carpeta correcta: truco_rl/
  2. Tener las dependencias instaladas: pip install stable-baselines3
  3. Ejecutar: python demo_entrenamiento.py
        """)
