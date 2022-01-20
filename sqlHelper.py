from ast import arg
from flask_mysqldb import MySQL
#from app import mysql 
from blockchain import Block, BlockChain

mysql = MySQL()

class InvalidTransactionException(Exception):
    pass

class InsufficientFundsException(Exception):
    pass

class Table():
    def __init__(self, table_name, *args):
        self.table = table_name
        self.columns = "(%s)" %",".join(args)
        self.columnList = args

        if isNewTable(table_name):
            create_data = ""
            for column in self.columnList:
                create_data += "%s varchar(100)," %column    
                
            cur = mysql.connection.cursor()
            cur.execute("CREATE TABLE %s(%s)" %(self.table, create_data[:len(create_data) - 1]))
            cur.close()


    def getAll(self):
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM %s" % (self.table))
        mysql.connection.commit()
        data = cur.fetchall(); return data

    def getOne(self, search, value):
        data = {}
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM %s WHERE %s = \"%s\"" % (self.table, search, value))
        if result > 0:
            data = cur.fetchone()
            cur.close()
            return data

    def deleteOne(self, search, value):
        cur = mysql.connection.cursor()
        result = cur.execute("DELETE FROM %s WHERE %s = \"%s\"" % self.table, search, value)
        mysql.connection.commit()
        cur.close()


    def deleteAll(self):
        self.drop()
        self.__init__(self.table, *self.columnList)

    def drop(self):
        cur = mysql.connection.cursor()
        cur.execute("DROP TABLE %s" %(self.table))
        cur.close()

    def insert(self, *args):
        data = ""
        for arg in args:
            data += "\"%s\"," % (arg)

        cur = mysql.connection.cursor()    
        cur.execute("INSERT INTO %s%s VALUES(%s)" % (self.table, self.columns, data[:len(data) - 1]))
        mysql.connection.commit()
        cur.close()



def sql_raw(execution):
        cur = mysql.connection.cursor()    
        cur.execute(execution)
        mysql.connection.commit()
        cur.close()

def isNewTable(tableName):
    cur = mysql.connection.cursor()
    try:
        result = cur.execute("SELECT * FROM %s" %tableName)
        cur.close()
    except:
        return True
    else:
        return False


def isNewUser(username):
    users = Table("users", "name", "email", "username", "password")
    data = users.getAll()
    usernames = []
    for user in data:
        usernames = user.get('username')

    if username in usernames:
        return False
    else:
        return True


def send_money(sender, recipient, amount):
    try:
        amount = float(amount)
    except ValueError:
        raise InvalidTransactionException('Invalid Transaction.')

    if amount > getBalance(sender) and sender != 'BANK':
        raise InsufficientFundsException('Insufficient Funds')
    elif sender == recipient or amount <= 0.00:
        raise InvalidTransactionException('Invalid Transaction')
    elif isNewUser(recipient):
        raise InvalidTransactionException('User does not exist')
    
    blockchain = getBlockChain()
    number = len(blockchain.chain) + 1
    data = "%s-->%s-->%s" %(sender, recipient, amount)
    blockchain.mine(Block(number, data=data))
    syncBlockChain(blockchain)


def getBalance(username):
    balance = 0.00
    blockchain = getBlockChain()
    for block in blockchain.chain:
        data = block.data.split('-->')
        if username == data[0]:
            balance -= float(data[2])
        elif username == data[1]:
            balance += float(data[2])

    return balance



def getBlockChain():
    blockchain = BlockChain()
    blockChain_sql = Table('blockchain', 'number', 'hash','previous_hash','data' ,'nonce')
    for b in blockChain_sql.getAll():
        blockchain.add(Block(int(b.get('number')), b.get('previous'), b.get('data'), int(b.get('nonce'))))

    return blockchain


def syncBlockChain(blockchain):
    blockChain_sql = Table('blockchain', 'number', 'hash','previous','data' ,'nonce')
    blockChain_sql.deleteAll()

    for block in blockchain.chain:
        blockChain_sql.insert(str(block.number), block.hash(), block.previous_hash, block.data, block.nonce)    



def testBlockchain():
    blockChain_sql = Table('blockchain', 'number', 'hash','previous','data' ,'nonce')
    blockChain_sql.deleteAll()
