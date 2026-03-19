from Game import Game
from Card import Card
from Truco import Truco

if __name__ == "__main__":
    truco = Truco()
    mano1, mano2, sample =truco.generateRandomHandsAndSample()
    print(f"mano jugador 1: {mano1}")
    print(f"mano jugador 2: {mano2}")
    print(f"muestra: {sample}")

    flower = [Card(7,"sword"),Card(4,"cup"),Card(11,"sword")]
    sampFlower = Card(10,"sword")

    game = Game()
    order1 = game.orderHand(mano1, sample)
    order2 = game.orderHand(mano2, sample)
    print(f"mano ordenada de j1: {order1}")
    print(f"mano ordenada de j2: {order2}")
    print(f"envido 1: {game.calculateEnvido(flower,sampFlower)}")
