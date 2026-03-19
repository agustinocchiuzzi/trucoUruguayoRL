class Card:
 
    def __init__(self, number, palo):
        self.palo = palo
        self.number = number
 
    def value(self, sample):
        if (self.number == 2 and self.palo == sample.palo) or (self.number == 12 and self.palo == sample.palo and sample.number == 2):
            return 100
        elif (self.number == 4 and self.palo == sample.palo) or (self.number == 12 and self.palo == sample.palo and sample.number == 4):
            return 99
        elif (self.number == 5 and self.palo == sample.palo) or (self.number == 12 and self.palo == sample.palo and sample.number == 5):
            return 98
        elif (self.number == 11 and self.palo == sample.palo) or (self.number == 12 and self.palo == sample.palo and sample.number == 11):
            return 97
        elif (self.number == 10 and self.palo == sample.palo) or (self.number == 12 and self.palo == sample.palo and sample.number == 10):
            return 96
        elif (self.number == 1 and self.palo == "sword"):
            return 95
        elif (self.number == 1 and self.palo == "coarse"):
            return 94
        elif (self.number == 7 and self.palo == "sword"):
            return 93
        elif (self.number == 7 and self.palo == "gold"):
            return 93
        elif (self.number == 3):
            return 92
        elif (self.number == 2):
            return 91
        elif (self.number == 1):
            return 90
        elif (self.number == 12):
            return 89
        elif (self.number == 11):
            return 88
        elif (self.number == 10):
            return 87
        elif (self.number == 7):
            return 86
        elif (self.number == 6):
            return 85
        elif (self.number == 5):
            return 84
        else:
            return 83
 
    def envidoValue(self, sample):
        if self.palo == sample.palo:
            if self.number == 10 or self.number == 11 or (self.number == 12 and sample.number in [10,11]):
                return 27
            elif self.number == 5 or ( self.number == 12 and sample.number == 2):
                return 28
            elif self.number == 4 or (self.number == 12 and sample.number == 4):
                return 29
            elif self.number == 2 or (self.number == 12 and sample.number == 2):
                return 30
            elif self.number == 12:
                return 0
            else:
                return self.number
        else:
            if self.number == 10 or self.number == 11 or self.number == 12:
                return 0
            else:
                return self.number
 
    def isPiece(self, sample):
        return (
            (self.number in [2, 4, 5, 10, 11] and self.palo == sample.palo) or
            (self.number == 12 and self.palo == sample.palo and sample.number in [2, 4, 5, 10, 11])
        )
 
    def flowerValue(self, sample):
        if self.isPiece(sample):
            return self.envidoValue(sample)
        return 0
 
    def __repr__(self):
        palos_es = {"sword": "Espada", "coarse": "Basto", "gold": "Oro", "cup": "Copa"}
        return f"{self.number} de {palos_es.get(self.palo, self.palo)}"