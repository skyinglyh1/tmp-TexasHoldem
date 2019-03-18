"""
TexasHoldem Game
"""
from ontology.interop.Ontology.Contract import Migrate
from ontology.interop.System.Storage import GetContext, Get, Put
from ontology.interop.System.Runtime import CheckWitness, GetTime, Notify
from ontology.interop.Ontology.Runtime import GetCurrentBlockHash, Base58ToAddress
from ontology.builtins import concat, sha256


Admin = Base58ToAddress('address')
PLAYER_LAST_CHECK_IN_DAY = "P1"
GAME_SALT_KEY = "G1"
DaySeconds = 86400

PLAYER_REFERRAL_KEY = "P1"


def Main(operation, args):
    ######################### for Admin to invoke Begin #########################
    if operation == "startGame":
        assert (len(args) == 3)
        pokerHashList = args[0]
        playerList = args[1]
        gameId = args[2]
        return startGame(pokerHashList, playerList, gameId)
    if operation == "endGame":
        assert (len(args) == 2)
        gameId = args[0]
        salt = args[1]
        return endGame(gameId, salt)
    if operation == "migrateContract":
        assert (len(args) == 7)
        code = args[0]
        needStorage = args[1]
        name = args[2]
        version = args[3]
        author = args[4]
        email = args[5]
        description = args[6]
        return migrateContract(code, needStorage, name, version, author, email, description)
    if operation == "addReferral":
        assert (len(args) == 2)
        toBeReferred = args[0]
        referral = args[1]
        return addReferral(toBeReferred, referral)
    if operation == "addMultiReferral":
        assert (len(args) == 1)
        toBeReferredReferralList =args[0]
        return addMultiReferral(toBeReferredReferralList)
    ######################### for Admin to invoke End #########################

    ######################### for Player to invoke Begin #########################
    if operation == "checkIn":
        assert (len(args) == 1)
        player = args[0]
        return checkIn(player)
    if operation == "ifCheckIn":
        assert (len(args) == 1)
        account = args[0]
        return ifCheckIn(account)
    if operation == "projectReward":
        assert (len(args) == 2)
        player = args[0]
        projectId = args[1]
        return projectReward(player, projectId)
    if operation == "getSaltAfterEnd":
        assert (len(args) == 1)
        gameId = args[0]
        return getSaltAfterEnd(gameId)
    if operation == "checkPokerHash":
        assert (len(args) == 2)
        gameId = args[0]
        pokerNum = args[1]
        return checkPokerHash(gameId, pokerNum)
    if operation == "getReferral":
        assert (len(args) == 1)
        toBeReferred = args[0]
        return getReferral(toBeReferred)
    ######################### for Player to invoke End #########################
    return False


######################### for Admin to invoke Begin #########################
def startGame(pokerHashList, playerList, gameId):
    """
    admin send param to start game
    algorithm: pokeHash = abs(sha256(pokerNum) ^ sha256(salt))
    :param pokerHashList: [pokerHash1, pokerHash2, pokerHash3, ..., pokerHash52] send a list include 52 pokerHash
    :param playerList: [address1, address2, address3...] send all player address in this game
    :param gameId: game's id
    :return: bool
    """
    assert (CheckWitness(Admin))
    playerNum = len(playerList)
    pokerNum = len(pokerHashList)
    helperRandom = abs(GetCurrentBlockHash()) % pokerNum
    # deal poker to player
    playerPokerList = []

    tmp = 0
    while tmp < playerNum:
        # deal first poker
        playerHandPokerList = []
        poker = pokerHashList[helperRandom]
        pokerHashList.remove(helperRandom)
        playerHandPokerList.append(poker)
        pokerNum = Sub(pokerNum, 1)

        # deal second poker
        helperRandom = abs(sha256(concat(helperRandom, poker))) % pokerNum
        poker = pokerHashList[helperRandom]
        pokerHashList.remove(helperRandom)
        playerHandPokerList.append(poker)
        pokerNum = Sub(pokerNum, 1)

        helperRandom = abs(sha256(concat(helperRandom, poker))) % pokerNum
        tmp += 1
        playerPokerList.append(playerHandPokerList)

    # deal common poker
    commonPokerList = []
    commonPokerNum = 0
    while commonPokerNum < 5:
        poker = pokerHashList[helperRandom]
        pokerHashList.remove(helperRandom)
        commonPokerList.append(poker)
        pokerNum = Sub(pokerNum, 1)
        helperRandom = abs(sha256(concat(helperRandom, poker))) % pokerNum
        commonPokerNum += 1

    Notify(["startGame", pokerHashList, commonPokerList, playerPokerList, gameId])
    return True


def endGame(gameId, salt):
    """
    send game id and salt to
    :param gameId: game's id
    :param salt: salt number
    :return: bool
    """
    assert (CheckWitness(Admin))
    # set salt
    Put(GetContext(), concatKey(gameId, GAME_SALT_KEY), salt)
    Notify(["endGame", gameId, salt])
    return True


def migrateContract(code, needStorage, name, version, author, email, description):
    """
    admin can migrate contract
    :param code: new contract's avm code
    :param needStorage: if need storage default true
    :param name: contract's name
    :param version: contract's version
    :param author: contract's author
    :param email: contract's email
    :param description: contract's description
    :return: bool
    """
    assert (CheckWitness(Admin))
    res = Migrate(code, needStorage, name, version, author, email, description)
    assert (res)
    Notify(["Migrate Contract successfully"])
    return True


def addReferral(toBeReferred, referral):
    """
    admin can add referral
    :param toBeReferred: the player to be referred
    :param referral: the player can get referral reward
    :return: bool
    """
    assert (CheckWitness(Admin))
    RequireScriptHash(toBeReferred)
    RequireScriptHash(referral)
    assert (not getReferral(toBeReferred))
    assert (toBeReferred != referral)
    Put(GetContext(), concatKey(PLAYER_REFERRAL_KEY, toBeReferred), referral)
    Notify(["addReferral", toBeReferred, referral])
    return True


def addMultiReferral(toBeReferredReferralList):
    """
    admin can add referral
    :param toBeReferredReferralList: [[toBeReferred1, referral1], [toBeReferred2, referral2], ......]
    :return: bool
    """
    assert (CheckWitness(Admin))
    for toBeReferredReferral in toBeReferredReferralList:
        toBeReferred = toBeReferredReferral[0]
        referral = toBeReferredReferral[1]
        RequireScriptHash(toBeReferred)
        RequireScriptHash(referral)
        assert (not getReferral(toBeReferred))
        assert (toBeReferred != referral)
        Put(GetContext(), concatKey(PLAYER_REFERRAL_KEY, toBeReferred), referral)
    Notify(["addMultiReferral", toBeReferredReferralList])
    return True
######################### for Admin to invoke End #########################


######################### for Player to invoke Begin #########################
def checkIn(player):
    """
    check in function
    :param account: player's account addresss
    :return: bool
    """
    assert (CheckWitness(player))
    checkInDays = ifCheckIn(player)
    assert (checkInDays)
    Put(GetContext(), concatKey(PLAYER_LAST_CHECK_IN_DAY, player), checkInDays)

    Notify(["checkIn", player, checkInDays])
    return True


def ifCheckIn(player):
    """
    :param player: player's account address
    :return:  return == False => can NOT check in.
              return > now days => can check in.
    """
    lastTimeCheckIn = Get(GetContext(), concatKey(PLAYER_LAST_CHECK_IN_DAY, player))
    now = Add(GetTime(), Mul(8, 3600))  # to UTC8
    days = Div(now, DaySeconds)
    if not lastTimeCheckIn:
        return days
    if days > lastTimeCheckIn:
        return days
    else:
        return False


def projectReward(player, projectId):
    """
    :param player: player's account address
    :param projectId: project's id
    :return: bool
    """
    assert (CheckWitness(player))
    Notify(["getReward", player, projectId])
    return True


def getSaltAfterEnd(gameId):
    """
    can only get game's salt after end
    :param gameId: game's id
    :return: salt number
    """
    salt = Get(GetContext(), concatKey(gameId, GAME_SALT_KEY))
    return salt


def checkPokerHash(gameId, pokerNum):
    """
    can only check hash after end
    :param gameId: game's id
    :param pokeNum: player's poker num
    :return: pokeHash
    """
    assert (pokerNum >= 1)
    assert (pokerNum <= 52)
    salt = getSaltAfterEnd(gameId)
    pokeHash = abs(sha256(pokerNum) ^ sha256(salt))
    return pokeHash


def getReferral(toBeReferred):
    return Get(GetContext(), concatKey(PLAYER_REFERRAL_KEY, toBeReferred))
######################### for Player to invoke End #########################


######################### Utility Methods Start #########################
"""
https://github.com/ONT-Avocados/python-template/blob/master/libs/SafeMath.py
"""


def Add(a, b):
    """
    Adds two numbers, throws on overflow.
    """
    c = a + b
    assert (c >= a)
    return c


def Sub(a, b):
    """
    Substracts two numbers, throws on overflow (i.e. if subtrahend is greater than minuend).
    :param a: operand a
    :param b: operand b
    :return: a - b if a - b > 0 or revert the transaction.
    """
    assert(a>=b)
    return a-b


def Mul(a, b):
    """
    Multiplies two numbers, throws on overflow.
    :param a: operand a
    :param b: operand b
    :return: a - b if a - b > 0 or revert the transaction.
    """
    if a == 0:
        return 0
    c = a * b
    assert (c / a == b)
    return c


def Div(a, b):
    """
    Integer division of two numbers, truncating the quotient.
    """
    assert (b > 0)
    c = a / b
    return c


def concatKey(str1, str2):
    """
    connect str1 and str2 together as a key
    :param str1: string1
    :param str2:  string2
    :return: string1_string2
    """
    return concat(concat(str1, '_'), str2)


def RequireScriptHash(key):
    """
    Checks the bytearray parameter is script hash or not. Script Hash
    length should be equal to 20.
    :param key: bytearray parameter to check script hash format.
    :return: True if script hash or revert the transaction.
    """
    assert (len(key) == 20)
    return True
######################### Utility Methods End #########################
