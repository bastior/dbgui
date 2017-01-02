import pandas as pd
from dbHandler import *

class excelHandler():
    def __init__(self, dbHandler):
        self.db = dbHandler

    def getSheetNames(self, filePath):
        x1 = pd.ExcelFile(str(filePath))
        return [str(a) for a in x1.sheet_names]


    def importDataFromExcel(self, fileName, sheetName, createNewTable = True,
                            tableName = "abc"):

        excel = pd.ExcelFile(fileName)
        sheet = excel.parse(sheetName)

        mainColumnNames = self.db.checkTableColumns("main_table")

        subColumns = []

        for column in sheet.columns:
            if column not in mainColumnNames: subColumns.append(column)


        if createNewTable:
            tableName = sheetName
            columns = [str(a) for a in subColumns]
            #probably could be done better? dunno how
            types = ["text" for i in range(len(columns))]
            self.db.createTable(tableName, columns, types)

        for row in sheet.values:
            self.db.addDataToTable(tableName, sheet.columns, row)
