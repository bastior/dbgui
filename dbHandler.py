import sys
from PyQt4.QtSql import *


class dbHandler():
    def __init__(self):
        self.db = QSqlDatabase.addDatabase("QMYSQL")

        self.dbHost = None
        self.dbName = None
        self.dbUserName = None
        self.dbPassword = None

        self.model = None


    def deleteRow(self, tableName, idToDelete):
        query = QSqlQuery()
        queryString = "Delete from " + tableName + " where main_table_idtable1 = :1 limit 1"
        query.prepare(queryString)
        query.bindValue(":1", idToDelete)

        suc = query.exec_()

        queryString = "Delete from main_table where idtable1 = :1 limit 1"
        query.prepare(queryString)
        query.bindValue(":1", idToDelete)

        suc1 = query.exec_()

        return suc and suc1

    def getIndicesOfSubTable(self, tableName):
        q = QSqlQuery("SELECT main_table_idtable1 from " + tableName)
        indices = []
        while q.next():
            indices.append(str(q.value(0).toString()))
        return indices

    def getValuesFromColumn(self, tableName, columnName):
        if tableName != "main_table":
            columnList = []
            q = QSqlQuery("SELECT " + columnName + " FROM " + tableName)
            while q.next():
                columnList.append(str(q.value(0).toString()))
            return columnList
        else:
            q = QSqlQuery("SELECT idtable1, " + columnName + " FROM " + tableName)
            columnList = []
            ids = []
            while q.next():
                ids.append(str(q.value(0).toString()))
                columnList.append(str(q.value(1).toString()))
            return ids, columnList

    def addDataToTable(self, tableName, fieldNames, fieldValues):
        q = QSqlQuery("DESCRIBE main_table")
        columnList = []
        while q.next():
            columnList.append(str(q.value(0).toString()))
        mainColumn = []
        mainColumnValues = []
        subColumn = []
        subColumnValues = []

        for a, b in zip(fieldNames, fieldValues):
            if a in columnList:
                mainColumn.append(a)
                mainColumnValues.append(b)
            else:
                subColumn.append(a)
                subColumnValues.append(b)

        query = QSqlQuery()
        prepareString = "INSERT INTO main_table VALUES (DEFAULT"
        for i in range(len(mainColumn)):
            prepareString += ", "
            prepareString += ":"
            prepareString += str(i)
        prepareString += ")"

        query.prepare(prepareString)

        for i in range(len(mainColumn)):
            string = ":" + str(i)
            query.bindValue(string, mainColumnValues[i])
        suc = query.exec_()

        prepareString = "INSERT INTO " + tableName + " VALUES  (DEFAULT, LAST_INSERT_ID()"
        for i in range(len(subColumnValues)):
            prepareString += ", :"
            prepareString += str(i)

        prepareString += ")"
        query.prepare(prepareString)
        for i in range(len(subColumnValues)):
            string = ":" + str(i)
            query.bindValue(string, subColumnValues[i])
        suc1 = query.exec_()
        return suc and suc1

    def addRowToTable(self, tableName, fieldNames, fieldValues):
        #get main_table columns
        q = QSqlQuery("DESCRIBE main_table")
        columnList = []
        while q.next():
            columnList.append(str(q.value(0).toString()))
        index = len(columnList)
        query = QSqlQuery()
        prepareString = "INSERT INTO main_table VALUES (DEFAULT, "
        for i in range(index - 1):
            prepareString += ":"
            prepareString += str(i)
            prepareString += ", "
        prepareString = prepareString[:-2] #remove last ,
        prepareString += ")"

        query.prepare(prepareString)
        for i in range(0, index - 1):
            string = ":" + str(i)
            query.bindValue(string, fieldValues[i + 1])
        suc = query.exec_()

        prepareString = "INSERT INTO " + tableName + " VALUES  (DEFAULT, LAST_INSERT_ID()"
        for i in range( len(fieldValues) - index - 2):
            prepareString += ", :"
            prepareString += str(i)

        prepareString += ")"
        query.prepare(prepareString)
        for i in range(len(fieldValues) - index - 2):
            string = ":" + str(i)
            query.bindValue(string, fieldValues[i + index + 2])
        suc1 = query.exec_()
        return suc and suc1

    def dropTable(self, tableName):
        sqlQuery = "DROP TABLE :1"

        query = QSqlQuery()
        query.prepare(sqlQuery)
        query.bindValue(":1", tableName)

    def addColumn(self, tableName, columnName, columnType):
        #TODO change to prepare query istead of concatenate strings
        sqlQuery = "ALTER TABLE " + tableName + " ADD " + columnName + " " + columnType
        query = QSqlQuery(sqlQuery)

    def renameColumn(self, tableName, columnName, newColumnName, newColumnType):
        #TODO change to prepare query istead of concatenate strings
        query = QSqlQuery("ALTER TABLE " + tableName + " change column " + columnName + " " + newColumnName + " " + newColumnType)

    def removeColumn(self, tableName, columnName):
        #TODO change to prepare query istead of concatenate strings
        query = QSqlQuery("ALTER TABLE " + tableName + " DROP COLUMN " + columnName)

    def checkTableColumns(self, tableName):
        #TODO change to prepare query istead of concatenate strings
        query = QSqlQuery("DESCRIBE " + tableName)
        columnList = []
        typeList = []
        while query.next():
            columnList.append(str(query.value(0).toString()))
            typeList.append(str(query.value(1).toString()))
        #remove all default columns so noone hurts himself

        columnList = columnList[1:]
        typeList = typeList[1:]
        return columnList#, typeList


    def initModel(self):
        #TODO change to prepare query istead of concatenate strings
        query = QSqlQuery("select * from information_schema.tables WHERE TABLE_SCHEMA='" + self.dbName + "'")
        tableList = []
        while query.next():
            tableList.append(query.value(2).toString())

        return tableList

    #join subtable with main table. select with * to reverse order of column
    def subtableModel(self, tableName):
        #TODO change to prepare query istead of concatenate strings
        model = QSqlTableModel()
        strQuery = "select main_table.*, " + tableName + ".* from " + tableName + " join main_table on " + tableName + ".main_table_idtable1=main_table.idtable1"
        query = QSqlQuery(strQuery)
        #example query generated for table abcdef below
        #select main_table.*, abcdef.* from abcdef join main_table on abcdef.main_table_idtable1=main_table.idtable1;

        model.setQuery(query)
        return model


    def tableModel(self, tableName):
        #TODO change to prepare query istead of concatenate strings
        model = QSqlTableModel()
        # for some reason setting query with string does not work. Create query object to avoid this
        query = QSqlQuery("DESCRIBE " + str(tableName))
        model.setQuery(query)
        return model

    def setutf(self):
        query = QSqlQuery("SET NAMES 'utf8'")
        query = QSqlQuery("SET CHARACTER SET utf8")


    def setDatabaseInfo(self, a, b, c, d):
        #save db info for later
        self.dbHost = a
        self.dbName = b
        self.dbUserName = c
        self.dbPassword = d
        #set db info for connection porpuse
        self.db.setHostName(a)
        self.db.setDatabaseName(b)
        self.db.setUserName(c)
        self.db.setPassword(d)
        return self.db.open()

    def createTable(self, tableName, columns, types):
        #TODO change to prepare query istead of concatenate strings
        header = ("CREATE TABLE IF NOT EXISTS `" + self.dbName + "`.`" + tableName + "` (" +
          "`id" + tableName + "` INT NOT NULL AUTO_INCREMENT," +
          "`main_table_idtable1` INT NOT NULL, ")


        body = ""
        for column, typo in zip(columns, types):
            body = body + "`" + column[:60].strip() + "` " + typo + " NULL,"

        footer = ("PRIMARY KEY (`id" + tableName + "`, `main_table_idtable1`), " +
          "INDEX `fk_" + tableName + "_main_table1_idx` (`main_table_idtable1` ASC)," +
          "CONSTRAINT `fk_" + tableName + "_main_table1`" +
            "FOREIGN KEY (`main_table_idtable1`)" +
            "REFERENCES `" + self.dbName + "`.`main_table` (`idtable1`)" +
            " ON DELETE NO ACTION" +
            " ON UPDATE NO ACTION)")
        query = QSqlQuery(header + body + footer)
        print header + body + footer
