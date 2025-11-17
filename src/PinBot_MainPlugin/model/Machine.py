
class Machine:
    """机台类"""
    def __init__(self, name, type, description):
        self.__name = name
        self.__type = type
        self.__description = description
        self.__statu = True
        self.__cards = []

    def getName(self):
        return self.__name
    def getType(self):
        return self.__type
    def getDescription(self):
        return self.__description
    def getCards(self):
        return self.__cards
    def getStatu(self):
        return self.__statu

    def setName(self, name):
        self.__name = name
    def setDescription(self, description):
        self.__description = description
    def setType(self, type):
        self.__type = type

    def offMachine(self):
        self.__statu = False
    def onMachine(self):
        self.__statu = True

    def putCard(self, id):
        if(id not in self.__cards):
            self.__cards.append(id)
    def popCard(self, id):
        if(id in self.__cards):
            self.__cards.remove(id)
    def clearCards(self):
        self.__cards = []
    def getCardsNo(self, userid):
        num = 0
        for id in self.__cards:
            num += 1
            if id == userid:
                return num
        return -1
    def nextCard(self):
        first_card = self.__cards.pop(0)
        self.__cards.append(first_card)




def serialize_machine(machine):
    return {
        "name" : machine.getName(),
        "type" : machine.getType(),
        "description" : machine.getDescription(),
        "status" : machine.getStatu(),
    }

def deserialize_machine(data):
    machine = Machine(data["name"], data["type"], data["description"])
    machine.onMachine() if data["status"] else machine.offMachine()
    return machine

def search_machine(machines, name):
    for i in range(len(machines)):
        if machines[i].getName() == name:
            return i
    return -1