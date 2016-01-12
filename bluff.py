from flask import Flask,send_from_directory
from random import shuffle
from flask import render_template,jsonify
from collections import OrderedDict

from flask import request
from flask_socketio import SocketIO,send,emit
from collections import OrderedDict
import random,json
from itertools import cycle

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio=SocketIO(app)

cards={"2c":"2_of_clubs.png","3c":"3_of_clubs.png","4c":"4_of_clubs.png","5c":"5_of_clubs.png","6c":"6_of_clubs.png","7c":"7_of_clubs.png","8c":"8_of_clubs.png","9c":"9_of_clubs.png","10c":"10_of_clubs.png","11c":"jack_of_clubs.png","12c":"queen_of_clubs.png","13c":"king_of_clubs.png","1c":"ace_of_clubs.png","2d":"2_of_diamonds.png","3d":"3_of_diamonds.png","4d":"4_of_diamonds.png","5d":"5_of_diamonds.png","6d":"6_of_diamonds.png","7d":"7_of_diamonds.png","8d":"8_of_diamonds.png","9d":"9_of_diamonds.png","10d":"10_of_diamonds.png","11d":"jack_of_diamonds.png","12d":"queen_of_diamonds.png","13d":"king_of_diamonds.png","1d":"ace_of_diamonds.png","2h":"2_of_hearts.png","3h":"3_of_hearts.png","4h":"4_of_hearts.png","5h":"5_of_hearts.png","6h":"6_of_hearts.png","7h":"7_of_hearts.png","8h":"8_of_hearts.png","9h":"9_of_hearts.png","10h":"10_of_hearts.png","11h":"jack_of_hearts.png","12h":"queen_of_hearts.png","13h":"king_of_hearts.png","1h":"ace_of_hearts.png","2s":"2_of_spades.png","3s":"3_of_spades.png","4s":"4_of_spades.png","5s":"5_of_spades.png","6s":"6_of_spades.png","7s":"7_of_spades.png","8s":"8_of_spades.png","9s":"9_of_spades.png","10s":"10_of_spades.png","11s":"jack_of_spades.png","12s":"queen_of_spades.png","13s":"king_of_spades.png","1s":"ace_of_spades.png"}
cardNum={'9h':9,'12c':12,'12d':12,'12h':12,'9c':9,'9d':9,'12s':12,'9s':9,'1s':1,'5s':5,'1c':1,'5h':5,'1h':1,'5c':5,'1d':1,'13c':13,'6c':6,'6d':6,'13d':13,'6h':6,'13h':13,'13s':13,'6s':6,'5d':5,'2s':2,'2d':2,'2c':2,'2h':2,'10h':10,'7d':7,'7c':7,'10c':10,'10d':10,'7h':7,'7s':7,'10s':10,'3s':3,'3h':3,'3c':3,'3d':3,'11d':11,'8h':8,'11c':11,'8c':8,'11h':11,'8d':8,'11s':11,'8s':8,'4s':4,'4h':4,'4d':4,'4c':4}

def shuffledDeck(cards):
    cards=OrderedDict(cards)
    keys=list(cards.keys())
    random.shuffle(keys)
    cardList=[(key,cards[key]) for key in keys]
    cards=OrderedDict(cardList)
    return cards

#Global variables
locked=False
cards=shuffledDeck(cards)
clients=[]
clientCount=0
clientDeck=OrderedDict()
clientTurn=cycle('')
currentTurn=""
lastPlayer=""
lastPlayerCardList={}
tempCardList=[]
newTurn=True
turnList=[]
currentCard=0
lastPlayerTruth=True

def cToNum(card):
    if cardNum[card]==1:
        return "Ace"
    if cardNum[card]==11:
        return "Jack"
    if cardNum[card]==12:
        return "Queen"
    if cardNum[card]==13:
        return "King"
    return cardNum[card]



##SocketIO
@socketio.on('newClient')
def handle_message(msg):
    global locked,clientCount,clients
    if(locked==False):
        print msg
        print "broadcasting message"
        emit('ClientConnected',msg+" joined<br />",broadcast=True,include_self=False)
        clients.append(msg)
        clientCount += 1
    elif(locked==True):
        pass

@socketio.on('gameStartClient')
def play(playerId):
    global clientDeck,locked,clients,clientTurn,currentCard,newTurn
    if(locked != True):   
        locked=True
        clientDeck=divideDeck()
        clientTurn=cycle(clients)
        emit("gameStart","1",broadcast=True)
        giveTurn()
    else:
        #resuming play
        if(playerId in clientDeck.keys()):
            emit("gameStart","1")
            emit('checkTurn',[currentTurn,newTurn])
            emit("playingFor",currentCard)
        else:
             emit("onError","Game has already started!")

def cmp(l1,l2):
    if ((len(l1) == len(l2)) and (all(i in l1 for i in l2))):
        return True
    else:
        return False

def validate(cards,currentCard):
    if(len(cards)==0):
        return False
    for card in cards:
        if(cToNum(card)!=currentCard):
            return False
    return True


@socketio.on('turnPlayed')
def playerHasPlayed(clientCards):
    global clientTurn,lastPlayer,lastPlayerCardList,tempCardList,clientDeck,currentTurn,newTurn,cards,turnList,currentCard,lastPlayerTruth
    print clientCards
    if(clientCards== "show"):
            if(newTurn==False):
                print "SHOW event by user:"+currentTurn
             #check if previous turn has matching actual and fake
             #if true
                #append previous client card(all client cards TempCard) to current client deck
                #give turn to previous client
             #else (previous player Lied)
                #append list
                #Give Turn to current player
                if(lastPlayerTruth):
                    print lastPlayer+" has won"
                    for c in tempCardList:
                        clientDeck[currentTurn][c]=cards[c]
                    emit('notify',lastPlayer+" is correct",broadcast=True)
                    turnList.append(currentTurn)
                    turnList.append(lastPlayer)
                else:
                    print currentTurn+" has won "
                    for c in tempCardList:
                        clientDeck[lastPlayer][c]=cards[c]
                    emit('notify',currentTurn+" is correct ",broadcast=True)
                    turnList.append(currentTurn)
                newTurn=True
                tempCardList=[]
                emit("cardEvent","",broadcast=True)
                giveTurn()
    else:
        if(not clientCards['actual']):
            emit("onError","Please select cards and and press actual or fake cards button, before playing turn")
            return

        print currentCard
        if(newTurn and not validate(clientCards['actual'],cToNum(clientCards['actual'][0]))):
            emit("onError","Please select card of single value only!")
            return;
        if(newTurn):
            currentCard=cToNum(clientCards['actual'][0])
            if(len(clientCards['actual'])!=len(clientCards['fake'])):
                emit("onError","Please select equal number of actual and fake cards!")
                return
            emit("playingFor",currentCard,broadcast=True)
        lastPlayer=currentTurn
        lastPlayerCardList=clientCards

        if(newTurn and validate(clientCards['fake'],cToNum(clientCards['fake'][0])) and currentCard==cToNum(clientCards['fake'][0])):
            lastPlayerTruth=True
            print "new turn last player true"
        elif(newTurn and not validate(clientCards['fake'],currentCard)):
            lastPlayerTruth=False
            print "new turn last player false"
        if(not newTurn and not validate(clientCards['actual'],currentCard)):
            lastPlayerTruth=False
            print "last player false"
        elif(not newTurn and validate(clientCards['actual'],currentCard )and currentCard==cToNum(clientCards['actual'][0])):
            lastPlayerTruth=True
            print "last player true"
        if(newTurn):
            tempCardList +=clientCards['fake']
            #Deleting cards from current client list
            for card in clientCards['fake']:
                print "deleting "+clientDeck[currentTurn][card]
                del clientDeck[currentTurn][card]
        else:
            tempCardList +=clientCards['actual']
            for card in clientCards['actual']:
                #Deleting cards from current client list
                print "deleting "+clientDeck[currentTurn][card]
                del clientDeck[currentTurn][card]
        newTurn=False
        emit("cardEvent","",broadcast=True)
        giveTurn()




    

##Socket IO

def giveTurn():
    global currentTurn,turnList,newTurn
    if(turnList):
        currentTurn=turnList.pop()
        emit('checkTurn',[currentTurn,newTurn],broadcast=True)
    else:
        currentTurn=clientTurn.next()
        emit('checkTurn',[currentTurn,newTurn],broadcast=True)


def divideDeck():
    print "No. of clients="+str(len(clients))
    print "Total cards given will be :"+str(52/len(clients))
    i=0
    q=52/len(clients)
    deck=OrderedDict()
    for c in clients:
        deck[c]=OrderedDict(cards.items()[i:q])
        i=q
        q=q+(52/len(clients))
    return deck












@app.route('/')
def init():
    return render_template("dashboard.html",client=clients)

@app.route('/users')
def getAllUsers():
    dct={}
    dct['1']=2;
    l=[]
    l.append("vishal")
    #print cookies
    return json.dumps(clients);

@app.route('/card/all')
def sendCard():
    return render_template("index.html",images=cards)

#images of particular user
@app.route('/card/<user>')
def sendCardByUser(user):
    global clientDeck
    return render_template("index.html",images=clientDeck[user],clientList=clients)

@app.route('/v1/card/<user>')
def sendcardsbyuser(user):
    global clientDeck
    return json.dumps(clientDeck[user])

#to Load images
@app.route('/images/<name>')
def sendCardNumber(name):
    return send_from_directory('images',name)

@app.route('/reset')
def reset():
    global locked,cards,clients,clientCount,clientDeck,clientTurn,currentTurn,lastPlayer,lastPlayerCardList,tempCardList,newTurn,turnList,currentCard,lastPlayerTruth
    locked=False
    cards=shuffledDeck(cards)
    clients=[]
    clientCount=0
    clientDeck=OrderedDict()
    clientTurn=cycle('')
    currentTurn=""
    lastPlayer=""
    lastPlayerCardList={}
    tempCardList=[]
    newTurn=True
    turnList=[]
    currentCard=0
    lastPlayerTruth=True
    return "<h1>Game resetted</h1>"









if __name__ == '__main__':
    socketio.run(app,'0.0.0.0',80)
