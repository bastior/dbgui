import sys
import numpy as np
from PyQt4 import QtCore, QtGui, QtSql


from test_ui import Ui_MainWindow
from dbHandler import *
from excelHandler import *
from topsis import topsis
from rsm import rsm
from weightedSum import weightedSum


class MyForm(QtGui.QMainWindow):
    def __init__(self, parent=None):

        QtGui.QWidget.__init__(self, parent)
        self.db = dbHandler()
        self.excel = excelHandler(self.db)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # hardcoded local credentials for debugging.

        self.ui.dbHost.setText("localhost")
        self.ui.dbName.setText("basis")
        self.ui.dbUserName.setText("root")
        self.ui.dbPassword.setText("root")

        self.lineEditList = []
        self.comboList = []

        self.ui.pushButton.pressed.connect(self.dbConnect)
        self.ui.dropTableButton.pressed.connect(self.dropTable)
        self.ui.generateTables.pressed.connect(self.createTableView)
        self.ui.tableComboBox.currentIndexChanged.connect(self.showTableData)
        self.ui.addRow.pressed.connect(self.addRow)
        self.ui.commitButton.pressed.connect(self.commitChanges)
        self.ui.deleteButton.pressed.connect(self.deleteRow)

        self.ui.fileButton.pressed.connect(self.fileButtonPressed)

        self.ui.importDataButton.pressed.connect(self.importData)

        self.ui.exportButton.pressed.connect(self.exportToExcel)

        #Create Tab which allows to create new table in DB
        self.layoutCreateTab()
        self.layoutModifyTab()
        self.createMCDATab()

    def exportToExcel(self):
        header = [str(self.model.record(0).field(i).name()) for i in range(self.model.columnCount())]
        df = pd.DataFrame(data=np.zeros((0,len(header))), columns=header)
        for i in range(self.model.rowCount()):
            df.loc[i] = [str(self.model.record(i).field(j).value().toString().toUtf8()) for j in range(self.model.columnCount())]
        del df['idtable1']
        del df['main_table_idtable1']

        df.to_excel("abcd.xlsx", index=False)


    def importData(self):
        self.excel.importDataFromExcel(str(self.ui.filePath.text()), str(self.ui.sheetList.currentText()))

    def fileButtonPressed(self):
        self.ui.filePath.setText(QtGui.QFileDialog.getOpenFileName())
        for a in self.excel.getSheetNames(self.ui.filePath.text()):
            self.ui.sheetList.addItem(a)


    def deleteRow(self):
        box = QtGui.QMessageBox()
        box.setIcon(QtGui.QMessageBox.Question)
        box.setText("Are you sure you want to delete row?")
        box.setInformativeText("This can not be reverted. Changes will be permanent")
        box.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)


        if len(self.ui.tableView2.selectedIndexes()) == 0:
            retVal = box.exec_()
            if retVal == QtGui.QMessageBox.Yes:
                rowIndex = self.ui.tableView2.selectedIndexes()[0].row()
                val = self.model.record(rowIndex).field(0).value().toString()
                if self.db.deleteRow(self.ui.tableComboBox.currentText(), int(val)):
                    #update model
                    self.showTableData()

    def addRow(self):
        self.model.insertRow(self.model.rowCount())
        self.ui.addRow.setEnabled(False)

    def commitChanges(self):
        fieldNames = []
        fieldValues = []
        for i in xrange(self.model.columnCount()):
            field = self.model.record(self.model.rowCount() - 1).field(i)

            fieldNames.append(field.name())
            fieldValues.append(field.value().toString())
        #TODO check if we added row successfully then enable adding new row
        if self.db.addRowToTable(self.ui.tableComboBox.currentText(), fieldNames, fieldValues):
            self.ui.addRow.setEnabled(True)
            self.showTableData()


    def showTableData(self):
        self.model = self.db.subtableModel(self.ui.tableComboBox.currentText())
        self.ui.tableView2.setModel(self.model)
        #filter out columns with ids to make table easier to read
        for i in range(self.model.columnCount()):
            columnName = self.model.headerData(i, QtCore.Qt.Horizontal).toString()
            #TODO yea, those names shouldnt be hardcoded aswell. Will do for now
            if "idtable1" in columnName or "idtopics" in columnName:
                self.ui.tableView2.hideColumn(i)


    #this function creates layout for create Table tab. It changed dynamicly, so we can not generate
    #it with qt creator. In Qt creator this tab looks empty, and do not change that.
    #I also know -> this tab should go as another class. To lazy right now for it

    def layoutModifyTab(self):
        self.ui.actionBox.addItem("")
        self.ui.actionBox.addItem("add New Column")
        self.ui.actionBox.addItem("change column name")

        self.columnType = self.comboBoxFabric()
        self.columnType2 = self.comboBoxFabric()

        self.columnType.setEnabled(False)
        self.columnType2.setEnabled(False)

        self.ui.verticalLayout_8.addWidget(self.columnType)
        self.ui.verticalLayout_9.addWidget(self.columnType2)

        self.ui.actionBox.currentIndexChanged.connect(self.manageModifyTab)
        self.ui.tableListComboBox2.currentIndexChanged.connect(self.manageModifyTab)

        self.ui.modifyTable.pressed.connect(self.modifyTable)



    def dropTable(self):
        tableName = str(self.ui.tableListComboBox.currentText())
        box = QtGui.QMessageBox()
        box.setIcon(QtGui.QMessageBox.Question)
        box.setText("Are you sure you want to drop " + tableName + " table?")
        box.setInformativeText("This can not be reverted. Changes will be permanent. It will also drop all data in this table")
        box.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)

        retVal = box.exec_()

        if retVal == QtGui.QMessageBox.Yes:
            self.db.dropTable(tableName)
            self.reloadTables()
        else:
            #do nothing
            pass


    def modifyTable(self):
        if self.ui.actionBox.currentIndex() == 1:
            tableName = str(self.ui.tableListComboBox2.currentText())
            columnName = str(self.ui.columnName.text())
            columnType = str(self.columnType.currentText())

            self.db.addColumn(tableName, columnName, columnType)

        if self.ui.actionBox.currentIndex() == 2:
            tableName = str(self.ui.tableListComboBox2.currentText())
            columnName = str(self.ui.column1.currentText())
            newColumnName = str(self.ui.columnName2.text())
            newColumnType = str(self.columnType2.currentText())
            if newColumnName == "":
                self.db.removeColumn(tableName, columnName)
            else:
                self.db.renameColumn(tableName, columnName, newColumnName, newColumnType)

        tableColumns = self.db.checkTableColumns(self.ui.tableListComboBox2.currentText())
        self.ui.column1.clear()
        for column in tableColumns:
            self.ui.column1.addItem(column)



    #how to manage tab allowing table modyfication
    def manageModifyTab(self):
        self.ui.columnName.setEnabled(False)
        self.ui.column1.setEnabled(False)
        self.ui.columnName2.setEnabled(False)
        self.columnType.setEnabled(False)
        self.columnType2.setEnabled(False)


        if self.ui.actionBox.currentIndex() == 1:
            self.ui.columnName.setEnabled(True)
            self.columnType.setEnabled(True)

        if self.ui.actionBox.currentIndex() == 2:
            self.ui.column1.setEnabled(True)
            self.ui.columnName2.setEnabled(True)
            self.columnType2.setEnabled(True)

        tableColumns = self.db.checkTableColumns(self.ui.tableListComboBox2.currentText())

        self.ui.column1.clear()
        for column in tableColumns:
            self.ui.column1.addItem(column)

    #creates MCDA TAB manually
    def createMCDATab(self):

        #number to control no of columns in table already created
        self.noOfColumnsMCDA = 0
        self.noOfRefMCDA = 0

        #main tab layout
        self.MCDAMainLayout = QtGui.QVBoxLayout()
        #set this layout to tab
        self.ui.MCDATab.setLayout(self.MCDAMainLayout)
        self.MCDAMainLayout.setAlignment(QtCore.Qt.AlignTop)


        layout1 = QtGui.QHBoxLayout()
        label1 = QtGui.QLabel("MCDA Method")
        self.MCDAMethod = QtGui.QComboBox()
        self.MCDAMethod.addItem("TOPSIS")
        self.MCDAMethod.addItem("Weighted Sum")
        self.MCDAMethod.addItem("RSM")
        layout1.addWidget(label1)
        layout1.addWidget(self.MCDAMethod)

        self.MCDAMainLayout.addLayout(layout1)


        #second layout with labels
        layout2 = QtGui.QHBoxLayout()
        label2 = QtGui.QLabel("Programs' type")
        self.MCDATableNames = QtGui.QComboBox()
        layout2.addWidget(label2)
        layout2.addWidget(self.MCDATableNames)

        self.MCDAMainLayout.addLayout(layout2)


        layout3 = QtGui.QHBoxLayout()
        label3 = QtGui.QLabel("Number Of Criteria")
        self.MCDACritNo = QtGui.QSpinBox()
        self.MCDACritNo.setEnabled(False)
        layout3.addWidget(label3)
        layout3.addWidget(self.MCDACritNo)

        self.MCDAMainLayout.addLayout(layout3)


        layout5 = QtGui.QHBoxLayout()
        label5 = QtGui.QLabel("Number Of Reference Points (rsm only)")
        self.MCDARefNo = QtGui.QSpinBox()
        self.MCDARefNo.setEnabled(True)
        layout5.addWidget(label5)
        layout5.addWidget(self.MCDARefNo)

        self.MCDAMainLayout.addLayout(layout5)


        layout4 = QtGui.QHBoxLayout()
        l1 = QtGui.QLabel("Criteria")
        l2 = QtGui.QLabel("Criteria's weight")
        l3 = QtGui.QLabel("Min or Max")
        layout4.addWidget(l1)
        layout4.addWidget(l2)
        layout4.addWidget(l3)
        self.MCDAMainLayout.addLayout(layout4)

        self.MCDAMinMax = []
        self.MCDACriterias = []
        self.MCDAWeigths = []
        self.MCDARefs = []
        self.didRSMonce = False

        self.MCDACritNo.valueChanged.connect(self.recreateMCDAForm)
        self.MCDARefNo.valueChanged.connect(self.recreateRefForm)
        self.MCDATableNames.currentIndexChanged.connect(self.findCriteriaPosibilities)


        MCDAButton = QtGui.QPushButton()
        MCDAButton.pressed.connect(self.calculateMCDA)
        self.MCDAMainLayout.addWidget(MCDAButton)

    #Find coulmns of selected subtable + columns of main table to show all possible criterias in
    #sertain subtable. Show only main table columns if main table is chosen. Also remove all
    #existing tabs for criteria to ensure that everyhing is clean and stuff
    def calculateMCDA(self):
        ids = self.db.getIndicesOfSubTable(self.MCDATableNames.currentText())
        minMax = []
        weights = []
        arrays = []
        refs = []

        for val in self.MCDAMinMax:
            minMax.append(str(val.currentText()))
        for val in self.MCDAWeigths:
            weights.append(val.value())
        for val in self.MCDARefs:
            refs.append([str(val[0].currentText())] + [x.value() for x in val[1:]])

        for val in self.MCDACriterias:
            valsToRemove = []
            if str(val.currentText()) in self.mainCrits:
                indices, values = self.db.getValuesFromColumn("main_table", val.currentText())
                for i in indices:
                    if i not in ids:
                        valsToRemove.append(indices.index(i))
                for index in sorted(valsToRemove, reverse=True):
                    del values[index]
            else:
                values = self.db.getValuesFromColumn(self.MCDATableNames.currentText(), val.currentText())

            fVals = []
            try:
                for val in values:
                    fVals.append(float(val))
            except ValueError:
                print "not a float"

            arr = np.array(fVals)
            arrays.append(arr)

        performanceTable = np.vstack(arrays)
        performanceTable = performanceTable.transpose()
        results = []
        if str(self.MCDAMethod.currentText()) == "TOPSIS":
            results = topsis(performanceTable, weights, minMax)
        elif str(self.MCDAMethod.currentText()) == "Weighted Sum":
            results = weightedSum(performanceTable, weights, minMax)
        elif str(self.MCDAMethod.currentText()) == "RSM":
            results = rsm(performanceTable, weights, minMax, refs)
        self.ui.MCDAResults.clear()


        self.MCDAResultModel = self.db.subtableModel(self.MCDATableNames.currentText())

        header = [str(self.MCDAResultModel.record(0).field(i).name()) for i in range(self.MCDAResultModel.columnCount())]
        self.ui.MCDAResults.setColumnCount(len(header))
        self.ui.MCDAResults.insertColumn(1)
        header.insert(1, "MCDA Result")
        self.ui.MCDAResults.setHorizontalHeaderLabels(header)
        for i in range(self.MCDAResultModel.rowCount()):
            index = self.ui.MCDAResults.rowCount()
            if self.ui.MCDAResults.rowCount() <= i:
                self.ui.MCDAResults.insertRow(index)
            added = 0
            for j in range(self.MCDAResultModel.columnCount() + 1):
                if j == 1:
                    added = 1
                    self.ui.MCDAResults.setItem(i, j, QtGui.QTableWidgetItem(str(results[i])))
                else:
                    qstring = self.MCDAResultModel.record(i).field(j - added).value().toString()
                    self.ui.MCDAResults.setItem(i, j, QtGui.QTableWidgetItem(qstring))
        self.ui.MCDAResults.sortItems(1, 1)


    def findCriteriaPosibilities(self):
        self.MCDACritNo.setValue(0)
        self.recreateMCDAForm()

        self.mainCrits = self.db.checkTableColumns("main_table")
        self.subCrits = []
        if self.MCDATableNames.currentText() != "main_table":
            self.subCrits = self.db.checkTableColumns(self.MCDATableNames.currentText())[1:]


    def recreateMCDAForm(self):
        #check if we need to add new column
        #while needed if someone types value by hand
        while self.noOfColumnsMCDA != self.MCDACritNo.value():
            #We need to add more columns
            if self.noOfColumnsMCDA < self.MCDACritNo.value():

                layout = QtGui.QHBoxLayout()

                widget1 = QtGui.QComboBox()

                for crit in self.mainCrits + self.subCrits:
                    widget1.addItem(crit)

                widget2 = QtGui.QDoubleSpinBox()
                widget2.setSingleStep(0.1)
                widget2.setValue(1)


                widget3 = QtGui.QComboBox()
                widget3.addItem("max")
                widget3.addItem("min")

                self.MCDACriterias.append(widget1)
                self.MCDAWeigths.append(widget2)
                self.MCDAMinMax.append(widget3)

                layout.addWidget(widget1)
                layout.addWidget(widget2)
                layout.addWidget(widget3)
                #Replace button so it is always on the bottom
                #self.createLayout.removeWidget(self.createTableButton)

                if not self.didRSMonce:
                    self.MCDAMainLayout.insertLayout(len(self.MCDAMainLayout) - self.noOfRefMCDA, layout)
                else:
                    self.MCDAMainLayout.insertLayout(len(self.MCDAMainLayout) - self.noOfRefMCDA - 1, layout)
                #self.createLayout.addWidget(self.createTableButton)

                self.noOfColumnsMCDA += 1

            #We need to remove some columns
            elif self.noOfColumnsMCDA > self.MCDACritNo.value() and self.noOfColumnsMCDA > 0:

                #self.createLayout.removeWidget(self.createTableButton)
                if not self.didRSMonce:
                    self.MCDAMainLayout.removeItem(self.MCDAMainLayout.itemAt(len(self.MCDAMainLayout) - self.noOfRefMCDA - 1))
                else:
                    self.MCDAMainLayout.removeItem(self.MCDAMainLayout.itemAt(len(self.MCDAMainLayout) - self.noOfRefMCDA - 2))
                #self.createLayout.addWidget(self.createTableButton)

                self.MCDACriterias[-1].deleteLater()
                self.MCDAWeigths[-1].deleteLater()
                self.MCDAMinMax[-1].deleteLater()

                self.MCDACriterias.pop()
                self.MCDAWeigths.pop()
                self.MCDAMinMax.pop()

                self.noOfColumnsMCDA -= 1


    def recreateRefForm(self):
        # add label
        if not self.didRSMonce:
            self.RSMlabels = []
            layout6 = QtGui.QHBoxLayout()
            l1 = QtGui.QLabel("Type")
            layout6.addWidget(l1)
<<<<<<< HEAD
            self.RSMlabels.append(l1)
            for t in [x for x in self.subCrits if x in [str(v.currentText()) for v in self.MCDACriterias]]:
                l = QtGui.QLabel(t)
                layout6.addWidget(l)
                self.RSMlabels.append(l)
=======
            #for t in self.subCrits:
            #    l = QtGui.QLabel(t)
            #    layout6.addWidget(l)
>>>>>>> 3772e54... Fixed karakanie

            self.MCDAMainLayout.addLayout(layout6)
            self.didRSMonce = True

        # check if we need to add new column
        # while needed if someone types value by hand
        while self.noOfRefMCDA != self.MCDARefNo.value():
            # We need to add more columns
            if self.noOfRefMCDA < self.MCDARefNo.value():
                wdg = []
                layout = QtGui.QHBoxLayout()

                widget1 = QtGui.QComboBox()
                widget1.addItem("aspiration")
                widget1.addItem("statusquo")
                layout.addWidget(widget1)
                wdg.append(widget1)

<<<<<<< HEAD
                chosenCriteria = [str(v.currentText()) for v in self.MCDACriterias]
                for crit in [x for x in self.subCrits if x in chosenCriteria]:
=======

                for crit in range(self.noOfColumnsMCDA):
>>>>>>> 3772e54... Fixed karakanie
                    widget = QtGui.QDoubleSpinBox()
                    widget.setSingleStep(0.1)
                    layout.addWidget(widget)
                    wdg.append(widget)

                self.MCDARefs.append(wdg)
                self.MCDAMainLayout.addLayout(layout)

                self.noOfRefMCDA += 1

            # We need to remove some columns
            elif self.noOfRefMCDA > self.MCDARefNo.value() and self.noOfRefMCDA > 0:
                # self.createLayout.removeWidget(self.createTableButton)
                self.MCDAMainLayout.removeItem(self.MCDAMainLayout.itemAt(len(self.MCDAMainLayout) - 1))
                # self.createLayout.addWidget(self.createTableButton)
                for wdg in self.MCDARefs[-1]:
                    wdg.deleteLater()

                self.MCDARefs.pop()

                self.noOfRefMCDA -= 1
                if self.noOfRefMCDA == 0:
                    self.MCDAMainLayout.removeItem(self.MCDAMainLayout.itemAt(len(self.MCDAMainLayout) - 1))
                    for x in self.RSMlabels:
                        x.deleteLater()
                    self.didRSMonce = False


    def layoutCreateTab(self):

        #number to control no of columns in table already created
        self.noOfColumns = 0

        #main tab layout
        self.createLayout = QtGui.QVBoxLayout()
        #set this layout to tab
        self.ui.createTableTab.setLayout(self.createLayout)

        #Layout with Labels
        layout1 = QtGui.QHBoxLayout()
        title1 = QtGui.QLabel("Column Name")
        title2 = QtGui.QLabel("Column Type")
        layout1.addWidget(title1)
        layout1.addWidget(title2)

        #second layout with labels
        layout2 = QtGui.QHBoxLayout()
        title3 = QtGui.QLabel("Table Name")
        title4 = QtGui.QLabel("Number of Columns")
        layout2.addWidget(title3)
        layout2.addWidget(title4)

        self.spinBox = QtGui.QSpinBox()
        self.lineEdit = QtGui.QLineEdit()
        self.createTableButton = QtGui.QPushButton()
        self.createTableButton.pressed.connect(self.createTable)

        lo = QtGui.QHBoxLayout()

        lo.addWidget(self.lineEdit)
        lo.addWidget(self.spinBox)

        self.spinBox.valueChanged.connect(self.recreateForm)


        self.createLayout.setAlignment(QtCore.Qt.AlignTop)
        self.createLayout.addLayout(layout2)
        self.createLayout.addLayout(lo)

        self.createLayout.addLayout(layout1)
         
        self.createLayout.addWidget(self.createTableButton)

    #after pressing spinBox in create table tab
    #we need to adjust number of rows to number in spinbox
    #I know its confusing - but rows in QT table are actully columns in mysql table in this case

    def createTable(self):
        tableName = self.lineEdit.text()

        types = [str(a.currentText()) for a in self.comboList]
        columns = [str(a.text()) for a in self.lineEditList]

        self.db.createTable(tableName, columns, types)

        #reload tables everywhere
        self.reloadTables()



    def recreateForm(self):
        #check if we need to add new column
        #while needed if someone types value by hand
        while self.noOfColumns != self.spinBox.value():
            #We need to add more columns
            if self.noOfColumns < self.spinBox.value():

                layout2 = QtGui.QHBoxLayout()

                widget1 = QtGui.QLineEdit()
                widget2 = self.comboBoxFabric()

                self.lineEditList.append(widget1)
                self.comboList.append(widget2)

                layout2.addWidget(widget1)
                layout2.addWidget(widget2)
                #Replace button so it is always on the bottom
                self.createLayout.removeWidget(self.createTableButton)

                self.createLayout.addLayout(layout2)
                self.createLayout.addWidget(self.createTableButton)

                self.noOfColumns = self.noOfColumns + 1

            #We need to remove some columns
            elif self.noOfColumns > self.spinBox.value() and self.noOfColumns > 0:
                self.createLayout.removeWidget(self.createTableButton)
                self.createLayout.removeItem(self.createLayout.itemAt(len(self.createLayout) - 1))
                #Replace button so it is always on the bottom
                self.createLayout.addWidget(self.createTableButton)
                self.comboList[-1].deleteLater()
                self.lineEditList[-1].deleteLater()
                self.comboList.pop()
                self.lineEditList.pop()
                self.noOfColumns = self.noOfColumns - 1



    def reloadTables(self):
        self.ui.tableListComboBox.clear()
        self.ui.tableListComboBox2.clear()
        self.ui.tableComboBox.clear()
        self.MCDATableNames.clear()

        #fill combobox in View Table tab with table names
        for table in self.db.initModel():
            self.ui.tableListComboBox.addItem(table)
            self.ui.tableListComboBox2.addItem(table)
            self.ui.tableComboBox.addItem(table)
            self.MCDATableNames.addItem(table)


        #remove default tables so noone is hurt
        for i in range(self.ui.tableComboBox.count()):
            #yea, fixing table names is horrble idea. Will do for now however
            #probably should be some kind of propery of this class. 
            if self.ui.tableComboBox.itemText(i) == "main_table" or self.ui.tableComboBox.itemText(i) == "topics":
                self.ui.tableComboBox.removeItem(i)


    def dbConnect(self):
        if self.db.setDatabaseInfo(self.ui.dbHost.text(), self.ui.dbName.text(), self.ui.dbUserName.text(), self.ui.dbPassword.text()):
            self.ui.connectionStatusInfo.setText("connection status: connected")
            self.db.setutf()
        else:
            self.ui.connectionStatusInfo.setText("connection status: not connected")

        self.reloadTables()
        #TODO it should be done after we are sure we have connection tho
        self.MCDACritNo.setEnabled(True)


    def createTableView(self):
        model = self.db.tableModel(self.ui.tableListComboBox.currentText())

        self.ui.tableView.setModel(model)


    #create combo box with possible mySql column types. add new Item if needed
    def comboBoxFabric(self):
        box = QtGui.QComboBox(self.ui.createTableTab)
        box.addItem("")
        box.addItem("Text")
        box.addItem("Int")
        box.addItem("Float")
        return box


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())
