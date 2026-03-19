
from Card import Card
 
class Game:
 
    def orderHand(self, hand, sample):
        # order the cards from the lowest to the higher value in truco
        orderedCards = []
        orderedCards.append(hand[0])
        for i in range(1, 3):
            x = 0
            while x < len(orderedCards) and hand[i].value(sample) > orderedCards[x].value(sample):
                x += 1
            orderedCards.insert(x, hand[i])
        return orderedCards
 
    def isFlower(self, hand, sample):
        cond1 = hand[0].isPiece(sample) and hand[1].isPiece(sample) and hand[2].isPiece(sample)
        cond2 = (
            (hand[0].isPiece(sample) and hand[1].isPiece(sample)) or
            (hand[1].isPiece(sample) and hand[2].isPiece(sample)) or
            (hand[0].isPiece(sample) and hand[2].isPiece(sample))
        )
        cond3 = (
            (hand[0].isPiece(sample) and hand[1].palo == hand[2].palo) or
            (hand[1].isPiece(sample) and hand[2].palo == hand[0].palo) or
            (hand[2].isPiece(sample) and hand[1].palo == hand[0].palo)
        )
        cond4 = hand[0].palo == hand[1].palo == hand[2].palo
        return cond1 or cond2 or cond3 or cond4
 
    def calculateEnvido(self, hand, sample):
        if self.isFlower(hand, sample):
            return -1
        orderedCards = []
        orderedCards.append(hand[0])
        for i in range(1, 3):
            x = 0
            while x < len(orderedCards) and hand[i].envidoValue(sample) > orderedCards[x].envidoValue(sample):
                x += 1
            orderedCards.insert(x, hand[i])
        if orderedCards[2].isPiece(sample):
            envido = orderedCards[2].envidoValue(sample) + orderedCards[1].envidoValue(sample)
        elif orderedCards[0].palo == orderedCards[1].palo:
            envido = orderedCards[0].envidoValue(sample) + orderedCards[1].envidoValue(sample) + 20
        elif orderedCards[0].palo == orderedCards[2].palo:
            envido = orderedCards[0].envidoValue(sample) + orderedCards[2].envidoValue(sample) + 20
        elif orderedCards[1].palo == orderedCards[2].palo:
            envido = orderedCards[1].envidoValue(sample) + orderedCards[2].envidoValue(sample) + 20
        else:
            envido = orderedCards[2].envidoValue(sample)
        return envido
 
    def calculateFlower(self, hand, sample):
        pieces = [c for c in hand if c.isPiece(sample)]
        non_pieces = [c for c in hand if not c.isPiece(sample)]
        if len(pieces) == 3:
            vals = sorted([c.envidoValue(sample) for c in pieces], reverse=True)
            return vals[0] + (vals[1] % 10) + (vals[2] % 10)
        if len(pieces) == 2:
            vals = sorted([c.envidoValue(sample) for c in pieces], reverse=True)
            other_val = non_pieces[0].envidoValue(sample) if non_pieces else 0
            return vals[0] + (vals[1] % 10) + other_val
        if len(pieces) == 1:
            piece_val = pieces[0].envidoValue(sample)
            others = sorted([c.envidoValue(sample) for c in non_pieces], reverse=True)
            return piece_val + sum(others)
        vals = sorted([c.envidoValue(sample) for c in hand], reverse=True)
        return vals[0] + vals[1] + vals[2] + 20
 
    def resolveRound(self, card1, card2, sample):
        v1 = card1.value(sample)
        v2 = card2.value(sample)
        if v1 > v2:
            return 1
        elif v2 > v1:
            return 2
        else:
            return 0
 
    def resolveHand(self, rounds):
        # resolve if the hands has a winner or not yet (if not returns 0 then)
        r = rounds
 
        if len(r) == 0:
            return 0
        if len(r) >= 2 and r[0] != 0 and r[0] == r[1]:
            return r[0]
        if len(r) >= 2 and r[0] == 0 and r[1] != 0:
            return r[1]
        if len(r) >= 2 and r[0] != 0 and r[1] == 0:
            return r[0]
        if len(r) == 2 and r[0] != 0 and r[1] != 0 and r[0] != r[1]:
            return 0
        if len(r) == 3:
            if r[2] != 0:
                return r[2]
            return 1
        return 0