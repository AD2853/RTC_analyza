#Tyto data byli anonymizovaná a úpravená pro výukové účely, a neodpovídají reálným měřením.
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import csv
import datetime as dt
import heapq
import tkinter
import tkinter, tkinter.messagebox
import traceback

import matplotlib
matplotlib.use('TkAgg')

def importCsv(filePath):
    """Import vstupního CSV souboru - data načtena do slovníku 'd', kde klíče jsou názvy sloupců ze vstupního CSV. Funkce vrátí vytvoření slovník 'd'. """
    d = {}
    with open(filePath, newline='', encoding='utf-8-sig') as csvFile:
        reader = csv.reader(csvFile)
        for i in list(reader)[0]:
            d[i] = []    

    with open(filePath, newline='', encoding='utf-8-sig') as csvFile:
        reader2 = csv.DictReader(csvFile)
        for row in reader2:
            for key in row:
                d[key].append(row[key])
    return(d)

def createDictionary(dataset, key):
    """ Vytvoří nový slovník, kde klíče odpovídají unikátním záznamům z jednotlivých listů v hodnotách slovníku d (tzn. unikátní hodnoty jednotlivých sloupců), přiřadí všem klíčům nulovou hodnotu"""
    s = set(dataset[key])
    dictionaryName = {}
    for item in s:
        dictionaryName[item] = 0
    return dictionaryName

def messageboxInfo(title, text):
    root = tkinter.Tk()
    root.withdraw()
    tkinter.messagebox.showinfo(title, text)
    root.destroy()

def messageboxError(title, text):
    root = tkinter.Tk()
    root.withdraw()
    tkinter.messagebox.showerror(title, text)
    root.destroy()

def messageboxWarning(title, text):
    root = tkinter.Tk()
    root.withdraw()
    tkinter.messagebox.showwarning(title, text)
    root.destroy()



# Jednotlivé analýzky: 
# Zadání1: 
def highSeverityWiWithLowPriority(dataset):
    """ Vrátí slovník - seznam všech WI, které mají vysokou severitu a zároveň nízkou prioritu, vrací hodnoty listOfWiWithTime, count, pomerZCelkovehoPoctuWI."""
    HighSeverity = ['Critical', 'Blocker']
    HighPriority = ['Urgent', 'High', 'Unassigned']
    count = 0
    listOfWiWithTime = {}

    for i, severity in enumerate(dataset['Severity']):
        if (severity in HighSeverity) and (d['Priority'][i] not in HighPriority):
            listOfWiWithTime[dataset['Work Item ID'][i]] = {'Work Item': dataset['Work Item'][i], 'Severity': dataset['Severity'][i], 'Priority': dataset['Priority'][i], 'URL': dataset['URL'][i]}
            count += 1
    pomerZCelkovehoPoctuWI = round((count * 100)/ len(d['Work Item ID']), 2)

    return listOfWiWithTime, count, pomerZCelkovehoPoctuWI

# Zadání2:
def NotRepro(dataset):
    """Vrátí informace o WI s 'Not Repro' výsledkem."""
    # 2.a - How many (and what percentage) of WIs could not be reproduced?
    pocetWI = len(dataset["Resolution"])
    pocetNotRepro = dataset["Resolution"].count("NotRepro")
    procentoOfNotRepro =  round(pocetNotRepro/pocetWI *100, 2)
    return pocetWI, pocetNotRepro, procentoOfNotRepro

def NotReproList(dataset):   
    #2.b How many of them were Critical/Blocker?
    HighSeverity = ['Critical', 'Blocker']
    pocet = 0
    listOfWiNotReproHighSeverity = {}

    for i, resolution in enumerate(dataset['Resolution']):
        if (resolution == "NotRepro") and (dataset['Severity'][i] in HighSeverity):
            listOfWiNotReproHighSeverity[dataset['Work Item ID'][i]] = {'Work Item': dataset['Work Item'][i], 'Resolution': dataset['Resolution'][i], 'Severity': dataset['Severity'][i], 'URL': dataset['URL'][i]}
            pocet += 1
    
    return listOfWiNotReproHighSeverity, pocet

# Zadání3: Zoradiť resolverov podľa toho, kto má priradených najviac Critical/Blocker WI? (to môže znamenať, že robí najviac chýb, ale aj že je najschopnejší ich opraviť)
def bestResolvers(dataset):
    """ Vrátí slovník o zadaném počtu resolverů s největším počtem přiřazených PBI s vysokou severitou."""
    HighSeverity = ['Critical', 'Blocker']

    # vytvoření slovníku, který obsahuje jako key jména všech resolverů
    resolvers = createDictionary(dataset, 'Resolver')
    for item in resolvers:
        resolvers[item] = {'countCritical': 0, 'countBlocker': 0, 'countTotal' :0} 

    # doplnění hodnot countCritical, countBlocker, countTotal do slovníku 
    for resolver in resolvers.keys():
        for i, item in enumerate(dataset['Resolver']):
            if (item == resolver) and (dataset['Severity'][i] in HighSeverity):
                if dataset['Severity'][i] == 'Critical':
                    resolvers[resolver]['countCritical'] += 1 
                else:
                    resolvers[resolver]['countBlocker'] += 1
                resolvers[resolver]['countTotal'] += 1
    return resolvers

#4. - 10 WI with the longest Planned Work
def longestPlannedWorkWi(dataset):
    """ Vrátí slovník se seznamem WI a plánovaný časem."""
    listOfWiWithPlannedWork = {}
    for i, item in enumerate(dataset['Work Item ID']):
        listOfWiWithPlannedWork[dataset['Work Item ID'][i]] = {'Work Item': dataset['Work Item'][i], 'Planned Work': dataset['Planned Work'][i], 'URL': dataset['URL'][i]}

    for key in listOfWiWithPlannedWork:
        listOfWiWithPlannedWork[key]['Planned Work'] = int(listOfWiWithPlannedWork[key]['Planned Work'].replace(",", ""))
    return listOfWiWithPlannedWork


#Zadání5: 10 WI with the longest time it took to resolve
def longestTimeRequiredWI(dataset):
    """ Vrátí slovník se seznamem WI a časem, který byl potřeba k uzavření WI."""

    # definice proměnných
    countResolved = 0
    countOpen = 0
    dataFormatENG = '%m/%d/%y %I:%M %p'
    endScript = False

    listOfWiWithTime = {}
    listOfWiWithWrongDateFormat = []

    # výpočet času potřebného k uzavření WI - prochází jednotlivé záznamy a vypočítává pro každý záznam výsledný čas rozdílem ResolvedDate - CreationDate
    for i, resolvedDate in enumerate(dataset['Resolved Date']):
        # pokud je pole resolvedDate prázdné (tzn. WI nebylo uzavřeno) - navýšení hodnoty countOpen (počet neuzavřených WI)
        if resolvedDate == '':
            countOpen += 1
        # pokud není pole resolvedDate prázdné (tzn. WI bylo uzavřeno) - navýšení hodnoty countResolved (počet neuzavřených WI) a výpočet celkového času potřebného k uzavření WI
        else:
            countResolved +=1
            # Zpracovává očekávaný formát data, pokud by ve vstupu byl nevalidní formát, načtě záznam s chybným formátem do seznamu listOfWiWithWrongDateFormat
            try:
                time = (dt.datetime.strptime(resolvedDate, dataFormatENG)) - (dt.datetime.strptime(dataset['Creation Date'][i], dataFormatENG))
                # vypočtena hodnota time pro daný záznam se načte do slovníku k příslušenému WI
                listOfWiWithTime[dataset['Work Item ID'][i]] = {'Work Item': dataset['Work Item'][i], 'TimeToResolve': time, 'URL': dataset['URL'][i]}
            except ValueError:
                listOfWiWithWrongDateFormat.append([dataset['Work Item ID'][i]])
                endScript = True
    
    # ukončení skriptu v případě, že vstupní soubor obsahuje chybný formát dat - vrátí seznam WI s chybným formátem dat
    if endScript == True:
        return listOfWiWithWrongDateFormat, endScript

    # výstup: slovník se seznamem uzavřených WI a časem
    return listOfWiWithTime, endScript

# Zadánív6. - Which + how many Blocking/Critical WIs were delayed?
def delayedWiWithHighSeverity(dataset):
    HighSeverity = ['Critical', 'Blocker']
    DelayedResolution = 'Delayed'
    count = 0
    listOfDelayedWi = {}

    for i, item in enumerate(dataset['Severity']):
        if (item in HighSeverity) and (dataset['Resolution'][i] == DelayedResolution):
            listOfDelayedWi[dataset['Work Item ID'][i]] = {'Work Item': dataset['Work Item'][i], 'Severity': dataset['Severity'][i], 'Resolution': dataset['Resolution'][i], 'URL': dataset['URL'][i]}
            count += 1
    return listOfDelayedWi, count


# Zadání7:
def sortSWPartsByNumberOfHighSeverityWI(dataset):
    """ Vrátí slovník pro swParts s informací o množství WI s vysoukou severitou pro danou sw part."""
    HighSeverity = ['Critical', 'Blocker']
    # vytvoření slovníku obsahující všechny typy SW Part
    swPart = createDictionary(dataset, 'SW Part (Custom) (xT)')
    for key in swPart.keys():
        swPart[key] = {'countCritical': 0, 'countBlocker': 0, 'countTotal' :0}
    # doplnění hodnot do vytvořeného slovníku SWPart
    for typeOfSwPart in swPart.keys():
        for i, item in enumerate(dataset['SW Part (Custom) (xT)']):
            if item == typeOfSwPart:
                if dataset['Severity'][i] in HighSeverity:
                    if dataset['Severity'][i] == 'Critical':
                        swPart[typeOfSwPart]['countCritical'] += 1
                    else:
                        swPart[typeOfSwPart]['countBlocker'] += 1
                    swPart[typeOfSwPart]['countTotal'] += 1             
    return swPart
 

# Zadání 8. - Which Owners selected Resolution=Later on WIs with Severity=Critical+Blocker?
def ownersWhichSelectedResolutionLaterOnHighSeverityWi(dataset):
    HighSeverity = ['Critical', 'Blocker']
    LaterResolution = 'Later'
    count = 0
    listOfOwners = {}
    for i, item in enumerate(d['Severity']):
        if (item in HighSeverity) and (d['Resolution'][i] == LaterResolution):
            listOfOwners[dataset['Owner'][i]] = {'Work Item': dataset['Work Item'][i], 'Severity': dataset['Severity'][i], 'Resolution': dataset['Resolution'][i], 'URL': dataset['URL'][i]}
            count += 1
    return listOfOwners, count

# definice funkcí zobrazení výsptupu:
def oddelovac():
    print(100*'-')

def printResultsSkript1(dictionary, count, pomer):
    print('Skript1 results:')
    for i, (k, v) in enumerate(sorted(dictionary.items(), key = lambda x : x[0])):
        print(f'{i + 1}. {k}, {v}')
    print(f'Celkový počet: {count}')
    print(f'Procento z celkového počtu WI: {round(pomer, 2)}%')
    oddelovac()

def printResultsSkript2a(countTotal, countNotRepro, pomer):
    print('Skript2 results:')
    print("Number of all WI:", countTotal)
    print("Number of WI NotRepro:", countNotRepro)
    print(f"Percentage of NotRepro WIs:, {pomer} %")

def printResultsSkript2b(dictionary, count):
    print('Seznam WI s resolution NotRepro a vysokou severitou:')
    for i, (k, v) in enumerate(sorted(dictionary.items(), key = lambda x : x[0])):
        print(f'{i + 1}. {k}, {v}')
    print((f'Celkový počet WI s vysokou severitou: {count}'))
    oddelovac()
    
def printResultsSkript3(dictionary, limit):
    print('Skript3 results:')
    for i, (k, v) in enumerate(sorted(dictionary.items(), key=lambda e: e[1]['countTotal'], reverse=True)):
        if i < limit:
            print(f'{i + 1}. {k}, {v}')
    oddelovac()

def printResultsSkript4(dictionary, limit):
    print('Skript4 results:')
    for i, (k, v) in enumerate(sorted(dictionary.items(), key=lambda e: e[1]['Planned Work'], reverse=True)):
        if i < limit:
            print(f'{i + 1}. {k}, {v}')
    oddelovac()

def printResultsSkript5(dictionary, formatCheck, limit):
    print('Skript5 results:')
    if formatCheck == False:
        for i, (k, v) in enumerate(sorted(dictionary.items(), key=lambda e: e[1]['TimeToResolve'], reverse=True)):
            if i < limit:
                print(f'{i + 1}. {k}, {v}')
    else:
        print('Chybný formát data! WI číslo:')
        print(dictionary)
    oddelovac()

def printResultsSkript6(dictionary, count):
    print('Skript6 results:')
    for i, (k, v) in enumerate(sorted(dictionary.items(), key=lambda e: e[0], reverse=True)):
        print(f'{i + 1}. {k}, {v}')
    print(f'Celkový počet: {count}')
    oddelovac()

def printResultsSkript7(dictionary, limit):
    print('Skript7 results:')
    for i, (k, v) in enumerate(sorted(dictionary.items(), key=lambda e: e[1]['countTotal'], reverse=True)):
        if i < limit:
            print(f'{i + 1}. {k}, {v}')
    oddelovac()

def printResultsSkript8(dictionary, count):
    print('Skript8 results:')
    for i, (k, v) in enumerate(sorted(dictionary.items(), key=lambda e: e[0], reverse=True)):
        print(f'{i + 1}. {k}, {v}')
    print(f'Number of Blocking/Critical WI with resolution set to "Later": {count}')
    oddelovac()

# definice funkcí pro export výsledku do CSV souboru:
today = dt.datetime.now().strftime('%Y-%m-%d')
fileName = 'skript'

def exportResults_type1(dictionary, fileName, aktDate):
    """ Export celého slovníku bez limitu na počet záznamů, seřazeno podle prvního klíče ve vstupním slovníku."""
    fieldnames = ['Work Item ID']
    for i, v in enumerate(dictionary.values()):
        if i == 0:
            for key in v.keys():
                fieldnames.append(key)

    with open(f'{fileName}_{aktDate}.csv', mode='w', newline='', encoding='utf-8-sig') as csvFile:
        writer = csv.DictWriter(csvFile, delimiter=',', fieldnames=fieldnames)
        dictionary = sorted(dictionary.items(), key = lambda x : x[0])

        writer.writeheader()
        for iDic, key in enumerate(dictionary):
            dct = {fieldnames[0]: key[0]}
            for i, item in enumerate(fieldnames):
                if i > 0:
                    dct[item] = dictionary[iDic][1][item]
            writer.writerow(dct)

def exportResults_type2(dictionary, fileName, aktDate, orderBy, limit):
    """ Export zadaného počtu záznamů (proměnná limit), výsledek řazený podle hodnoty z proměnné orderBy"""
    fieldnames = ['Work Item ID']
    for i, v in enumerate(dictionary.values()):
        if i == 0:
            for key in v.keys():
                fieldnames.append(key)

    with open(f'{fileName}_{aktDate}.csv', mode='w', newline='', encoding='utf-8-sig') as csvFile:
        writer = csv.DictWriter(csvFile, delimiter=',', fieldnames=fieldnames)
        dictionary = sorted(dictionary.items(), key=lambda e: e[1][orderBy], reverse=True)

        writer.writeheader()
        for iDic, key in enumerate(dictionary):
            dct = {fieldnames[0]: key[0]}
            if iDic < limit:
                for i, item in enumerate(fieldnames):
                    if i > 0:
                        dct[item] = dictionary[iDic][1][item]
                writer.writerow(dct)

# Při spuštění analýzy:
def runAnalysisAccordingSettings(ui):
    """Provede vybrané analýzy podle uživatelského nastavení."""

    #import vstupního soboboru:
    try:
        global d
        d = importCsv(ui.absPathCurrent)
    except (AttributeError, FileNotFoundError) as e:
        messageboxError('Error', f'Error occured:\nNepodařilo se provést import dat ze vstupního souboru - neplatná cesta ke vstupnímu souboru!\n\nPodrobnosti:\n{e}')
        # ukončit funkci
        return
    except Exception: 
        messageboxError('Error', f'Unexpected error occured:\nVstupní data pravděpodobně neodpovídají očekávanému formátu.\n\nPodrobnosti:\n{traceback.format_exc()}')
        # ukončit funkci
        return

    # nastavení formy výstupu - konzole nebo CSV importu - u CSV importu kontrola zadání složky
    exportSettingsIndex = ui.ChooseExportTo.currentIndex()
    if exportSettingsIndex == 0:
        try:
            fileNameExport = (ui.absPathOutput)
        except (AttributeError) as e:
            messageboxError('Error', f'Error occured:\nNebyla zadaná platná cesta pro uložení CSV souborů!\n\nPodrobnosti:\n{e}')
            return
        except Exception: 
            messageboxError('Error', f'Unexpected error occured:\n\nPodrobnosti:\n{traceback.format_exc()}')
            # ukončit funkci
            return

    # volání jednotlivých analýz podle nastavení checků
    try:
        if ui.Zadani1.isChecked():
            myDict1, count1, pomer1 = highSeverityWiWithLowPriority(d)  
            if exportSettingsIndex == 0:
                exportResults_type1(myDict1, f'{fileNameExport}//Skript1', today)
            else:
                printResultsSkript1(myDict1, count1, pomer1)

        if ui.Zadani2.isChecked():
            countTotal, countNotRepro, pomer2 = NotRepro(d)
            myDict2, count2 = NotReproList(d)
            if exportSettingsIndex == 0:
                exportResults_type1(myDict2, f'{fileNameExport}//Skript2', today)
            else:   
                printResultsSkript2a(countTotal, countNotRepro ,pomer2)
                printResultsSkript2b(myDict2, count2)   

        if ui.Zadani3.isChecked():
            myDict3 = bestResolvers(d) 
            lim3 = ui.NumberOfValuesToFilter3.value()
            if exportSettingsIndex == 0:
                exportResults_type2(myDict3, f'{fileNameExport}//Skript3', today, 'countTotal', lim3) 
            else: 
                printResultsSkript3(myDict3, lim3)  

        if ui.Zadani4.isChecked():
            myDict4 = longestPlannedWorkWi(d)
            lim4 = ui.NumberOfValuesToFilter4.value()
            if exportSettingsIndex == 0:
                exportResults_type2(myDict4, f'{fileNameExport}//Skript4', today, 'Planned Work', lim4)
            else:   
                printResultsSkript4(myDict4, lim4)  

        if ui.Zadani5.isChecked():
            myDict5, wrongFormat = longestTimeRequiredWI(d)
            lim5 = ui.NumberOfValuesToFilter5.value()
            if exportSettingsIndex == 0:
                if wrongFormat == False:
                    exportResults_type2(myDict5, f'{fileNameExport}//Skript5', today, 'TimeToResolve', lim5)
                else: 
                    messageboxWarning('Warning', 'Analýza 5 "WIs Longest Planned Work" nebyla provedena - chybný formát dat. Seznam WI s chybným formátem data lze zobrazit přes Terminal.')
            else:    
                printResultsSkript5(myDict5, wrongFormat, lim5) 

        if ui.Zadani6.isChecked():
            
            myDict6, count6 = delayedWiWithHighSeverity(d)
            if exportSettingsIndex == 0:
                exportResults_type1(myDict6, f'{fileNameExport}//Skript6', today)
            else:      
                printResultsSkript6(myDict6, count6)

        if ui.Zadani7.isChecked():
            myDict7 = sortSWPartsByNumberOfHighSeverityWI(d)
            lim7 = ui.NumberOfValuesToFilter5.value()
            if exportSettingsIndex == 0:
                exportResults_type2(myDict7, f'{fileNameExport}//Skript7', today, 'countTotal', lim7)
            else:     
                printResultsSkript7(myDict7, lim7) 

        if ui.Zadani8.isChecked():
            myDict8, count8 = ownersWhichSelectedResolutionLaterOnHighSeverityWi(d)
            if exportSettingsIndex == 0:
                exportResults_type1(myDict8, f'{fileNameExport}//Skript8', today)
            else:      
                printResultsSkript8(myDict8, count8)
        # informace při úspěšném dokončení:
        messageboxInfo('Information', 'Analýza úspěšně dokončena.')

    # Error hlášky, pokud analýza nedoběhne:
    except FileNotFoundError as e:
        messageboxError('Error', f'Error occured:\nNebyla zadaná platná cesta pro uložení CSV souborů!\n\nPodrobnosti:\n{e}')
        return
    except Exception as e:
        messageboxError('Error', f'Unexpected error occured:\n\nPodrobnosti:\n{traceback.format_exc()}')
        return




# šílená část kódu z většiny vygenerovaná přes PyQt designera:
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(824, 880)
        MainWindow.setMinimumSize(QtCore.QSize(824, 880))
        MainWindow.setMaximumSize(QtCore.QSize(824, 880))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/newPrefix/Downloads/thermo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setAutoFillBackground(False)
        MainWindow.setStyleSheet("background-color: rgb(255, 255, 255);\n"
"")
        MainWindow.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.logoTFpng = QtWidgets.QLabel(self.centralwidget)
        self.logoTFpng.setGeometry(QtCore.QRect(610, 10, 161, 111))
        self.logoTFpng.setMaximumSize(QtCore.QSize(500, 500))
        self.logoTFpng.setText("")
        self.logoTFpng.setPixmap(QtGui.QPixmap("projektPng/tf.png"))
        self.logoTFpng.setScaledContents(True)
        self.logoTFpng.setObjectName("logoTFpng")
        self.RunAnalysisPushButton = QtWidgets.QCommandLinkButton(self.centralwidget)
        self.RunAnalysisPushButton.setGeometry(QtCore.QRect(580, 800, 187, 55))
        self.RunAnalysisPushButton.setMaximumSize(QtCore.QSize(193, 16777215))
        self.RunAnalysisPushButton.setStyleSheet("font: 14pt \".AppleSystemUIFont\";\n"
"background-color: rgb(234, 230, 236);\n"
"\n"
"")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("projektPng/run.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.RunAnalysisPushButton.setIcon(icon1)
        self.RunAnalysisPushButton.setIconSize(QtCore.QSize(35, 35))
        self.RunAnalysisPushButton.setCheckable(False)
        self.RunAnalysisPushButton.setObjectName("RunAnalysisPushButton")
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(70, 50, 671, 751))
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.celyLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.celyLayout.setContentsMargins(0, 0, 0, 0)
        self.celyLayout.setObjectName("celyLayout")
        self.label_insertFile = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        font = QtGui.QFont()
        font.setFamily("Arial")
        self.label_insertFile.setFont(font)
        self.label_insertFile.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.label_insertFile.setObjectName("label_insertFile")
        self.celyLayout.addWidget(self.label_insertFile)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.celyLayout.addItem(spacerItem)
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.inputFileName1 = QtWidgets.QLineEdit(self.verticalLayoutWidget_3)
        self.inputFileName1.setMinimumSize(QtCore.QSize(370, 0))
        self.inputFileName1.setFrame(True)
        self.inputFileName1.setReadOnly(True)
        self.inputFileName1.setObjectName("inputFileName1")
        self.gridLayout_4.addWidget(self.inputFileName1, 1, 1, 1, 1)
        self.InsertFile1 = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.InsertFile1.setObjectName("InsertFile1")
        self.gridLayout_4.addWidget(self.InsertFile1, 1, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_4.addItem(spacerItem1, 1, 3, 1, 1)
        self.insertFile1Button = QtWidgets.QToolButton(self.verticalLayoutWidget_3)
        self.insertFile1Button.setMaximumSize(QtCore.QSize(20, 20))
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("projektPng/addfile.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.insertFile1Button.setIcon(icon2)
        self.insertFile1Button.setIconSize(QtCore.QSize(40, 40))
        self.insertFile1Button.setObjectName("insertFile1Button")
        self.gridLayout_4.addWidget(self.insertFile1Button, 1, 2, 1, 1)
        self.celyLayout.addLayout(self.gridLayout_4)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.celyLayout.addItem(spacerItem2)
        self.label_chooseAnalysis = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        font = QtGui.QFont()
        font.setFamily("Arial")
        self.label_chooseAnalysis.setFont(font)
        self.label_chooseAnalysis.setObjectName("label_chooseAnalysis")
        self.celyLayout.addWidget(self.label_chooseAnalysis)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.celyLayout.addItem(spacerItem3)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.Zadani1 = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.Zadani1.setMaximumSize(QtCore.QSize(300, 16777215))
        self.Zadani1.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Zadani1.setTabletTracking(False)
        self.Zadani1.setIconSize(QtCore.QSize(20, 20))
        self.Zadani1.setCheckable(True)
        self.Zadani1.setChecked(True)
        self.Zadani1.setTristate(False)
        self.Zadani1.setObjectName("Zadani1")
        self.horizontalLayout_7.addWidget(self.Zadani1)
        self.help1_png = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.help1_png.setMaximumSize(QtCore.QSize(20, 20))
        self.help1_png.setMouseTracking(True)
        self.help1_png.setText("")
        self.help1_png.setPixmap(QtGui.QPixmap("projektPng/questionmark.png"))
        self.help1_png.setScaledContents(True)
        self.help1_png.setObjectName("help1_png")
        self.horizontalLayout_7.addWidget(self.help1_png)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_7.addItem(spacerItem4)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem5)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.Zadani2 = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.Zadani2.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Zadani2.setTabletTracking(False)
        self.Zadani2.setIconSize(QtCore.QSize(16, 16))
        self.Zadani2.setCheckable(True)
        self.Zadani2.setChecked(True)
        self.Zadani2.setTristate(False)
        self.Zadani2.setObjectName("Zadani2")
        self.horizontalLayout_9.addWidget(self.Zadani2)
        self.help2_png = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.help2_png.setMaximumSize(QtCore.QSize(20, 20))
        self.help2_png.setMouseTracking(True)
        self.help2_png.setText("")
        self.help2_png.setPixmap(QtGui.QPixmap("projektPng/questionmark.png"))
        self.help2_png.setScaledContents(True)
        self.help2_png.setObjectName("help2_png")
        self.horizontalLayout_9.addWidget(self.help2_png)
        spacerItem6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem6)
        self.verticalLayout.addLayout(self.horizontalLayout_9)
        spacerItem7 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem7)
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.Zadani3 = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.Zadani3.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Zadani3.setTabletTracking(False)
        self.Zadani3.setCheckable(True)
        self.Zadani3.setChecked(True)
        self.Zadani3.setTristate(False)
        self.Zadani3.setObjectName("Zadani3")
        self.horizontalLayout_10.addWidget(self.Zadani3)
        self.help3_png = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.help3_png.setMaximumSize(QtCore.QSize(20, 20))
        self.help3_png.setMouseTracking(True)
        self.help3_png.setText("")
        self.help3_png.setPixmap(QtGui.QPixmap("projektPng/questionmark.png"))
        self.help3_png.setScaledContents(True)
        self.help3_png.setObjectName("help3_png")
        self.horizontalLayout_10.addWidget(self.help3_png)
        spacerItem8 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_10.addItem(spacerItem8)
        self.verticalLayout.addLayout(self.horizontalLayout_10)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem9 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem9)
        self.label_HowMany3 = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.label_HowMany3.setObjectName("label_HowMany3")
        self.horizontalLayout_2.addWidget(self.label_HowMany3)
        self.NumberOfValuesToFilter3 = QtWidgets.QSpinBox(self.verticalLayoutWidget_3)
        self.NumberOfValuesToFilter3.setMinimum(1)
        self.NumberOfValuesToFilter3.setMaximum(999)
        self.NumberOfValuesToFilter3.setProperty("value", 10)
        self.NumberOfValuesToFilter3.setObjectName("NumberOfValuesToFilter3")
        self.horizontalLayout_2.addWidget(self.NumberOfValuesToFilter3)
        spacerItem10 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem10)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        spacerItem11 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem11)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.Zadani4 = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.Zadani4.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Zadani4.setTabletTracking(False)
        self.Zadani4.setCheckable(True)
        self.Zadani4.setChecked(True)
        self.Zadani4.setTristate(False)
        self.Zadani4.setObjectName("Zadani4")
        self.horizontalLayout_11.addWidget(self.Zadani4)
        self.help4_png = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.help4_png.setMaximumSize(QtCore.QSize(20, 20))
        self.help4_png.setMouseTracking(True)
        self.help4_png.setText("")
        self.help4_png.setPixmap(QtGui.QPixmap("projektPng/questionmark.png"))
        self.help4_png.setScaledContents(True)
        self.help4_png.setObjectName("help4_png")
        self.horizontalLayout_11.addWidget(self.help4_png)
        spacerItem12 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_11.addItem(spacerItem12)
        self.verticalLayout.addLayout(self.horizontalLayout_11)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        spacerItem13 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem13)
        self.label_HowMany4 = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.label_HowMany4.setObjectName("label_HowMany4")
        self.horizontalLayout_4.addWidget(self.label_HowMany4)
        self.NumberOfValuesToFilter4 = QtWidgets.QSpinBox(self.verticalLayoutWidget_3)
        self.NumberOfValuesToFilter4.setMinimum(1)
        self.NumberOfValuesToFilter4.setMaximum(999)
        self.NumberOfValuesToFilter4.setProperty("value", 10)
        self.NumberOfValuesToFilter4.setObjectName("NumberOfValuesToFilter4")
        self.horizontalLayout_4.addWidget(self.NumberOfValuesToFilter4)
        spacerItem14 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem14)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        spacerItem15 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem15)
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.Zadani5 = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.Zadani5.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Zadani5.setTabletTracking(False)
        self.Zadani5.setCheckable(True)
        self.Zadani5.setChecked(True)
        self.Zadani5.setTristate(False)
        self.Zadani5.setObjectName("Zadani5")
        self.horizontalLayout_12.addWidget(self.Zadani5)
        self.help5_png = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.help5_png.setMaximumSize(QtCore.QSize(20, 20))
        self.help5_png.setMouseTracking(True)
        self.help5_png.setText("")
        self.help5_png.setPixmap(QtGui.QPixmap("projektPng/questionmark.png"))
        self.help5_png.setScaledContents(True)
        self.help5_png.setObjectName("help5_png")
        self.horizontalLayout_12.addWidget(self.help5_png)
        spacerItem16 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem16)
        self.verticalLayout.addLayout(self.horizontalLayout_12)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        spacerItem17 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem17)
        self.label_HowMany5 = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.label_HowMany5.setObjectName("label_HowMany5")
        self.horizontalLayout_5.addWidget(self.label_HowMany5)
        self.NumberOfValuesToFilter5 = QtWidgets.QSpinBox(self.verticalLayoutWidget_3)
        self.NumberOfValuesToFilter5.setMinimum(1)
        self.NumberOfValuesToFilter5.setMaximum(999)
        self.NumberOfValuesToFilter5.setProperty("value", 10)
        self.NumberOfValuesToFilter5.setObjectName("NumberOfValuesToFilter5")
        self.horizontalLayout_5.addWidget(self.NumberOfValuesToFilter5)
        spacerItem18 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem18)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        spacerItem19 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem19)
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.Zadani6 = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.Zadani6.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Zadani6.setTabletTracking(False)
        self.Zadani6.setCheckable(True)
        self.Zadani6.setChecked(True)
        self.Zadani6.setTristate(False)
        self.Zadani6.setObjectName("Zadani6")
        self.horizontalLayout_13.addWidget(self.Zadani6)
        self.help6_png = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.help6_png.setMaximumSize(QtCore.QSize(20, 20))
        self.help6_png.setMouseTracking(True)
        self.help6_png.setText("")
        self.help6_png.setPixmap(QtGui.QPixmap("projektPng/questionmark.png"))
        self.help6_png.setScaledContents(True)
        self.help6_png.setObjectName("help6_png")
        self.horizontalLayout_13.addWidget(self.help6_png)
        spacerItem20 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_13.addItem(spacerItem20)
        self.verticalLayout.addLayout(self.horizontalLayout_13)
        spacerItem21 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem21)
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.Zadani7 = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.Zadani7.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Zadani7.setTabletTracking(False)
        self.Zadani7.setCheckable(True)
        self.Zadani7.setChecked(True)
        self.Zadani7.setTristate(False)
        self.Zadani7.setObjectName("Zadani7")
        self.horizontalLayout_14.addWidget(self.Zadani7)
        self.help7_png = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.help7_png.setMaximumSize(QtCore.QSize(20, 20))
        self.help7_png.setMouseTracking(True)
        self.help7_png.setText("")
        self.help7_png.setPixmap(QtGui.QPixmap("projektPng/questionmark.png"))
        self.help7_png.setScaledContents(True)
        self.help7_png.setObjectName("help7_png")
        self.horizontalLayout_14.addWidget(self.help7_png)
        spacerItem22 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_14.addItem(spacerItem22)
        self.verticalLayout.addLayout(self.horizontalLayout_14)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        spacerItem23 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem23)
        self.label_HowMany7 = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.label_HowMany7.setObjectName("label_HowMany7")
        self.horizontalLayout_6.addWidget(self.label_HowMany7)
        self.NumberOfValuesToFilter7_2 = QtWidgets.QSpinBox(self.verticalLayoutWidget_3)
        self.NumberOfValuesToFilter7_2.setMinimum(1)
        self.NumberOfValuesToFilter7_2.setMaximum(999)
        self.NumberOfValuesToFilter7_2.setProperty("value", 10)
        self.NumberOfValuesToFilter7_2.setObjectName("NumberOfValuesToFilter7_2")
        self.horizontalLayout_6.addWidget(self.NumberOfValuesToFilter7_2)
        spacerItem24 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem24)
        self.verticalLayout.addLayout(self.horizontalLayout_6)
        spacerItem25 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem25)
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.Zadani8 = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.Zadani8.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Zadani8.setTabletTracking(False)
        self.Zadani8.setCheckable(True)
        self.Zadani8.setChecked(True)
        self.Zadani8.setTristate(False)
        self.Zadani8.setObjectName("Zadani8")
        self.horizontalLayout_15.addWidget(self.Zadani8)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_15.addLayout(self.verticalLayout_2)
        self.help8_png = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.help8_png.setMaximumSize(QtCore.QSize(20, 20))
        self.help8_png.setMouseTracking(True)
        self.help8_png.setText("")
        self.help8_png.setPixmap(QtGui.QPixmap("projektPng/questionmark.png"))
        self.help8_png.setScaledContents(True)
        self.help8_png.setObjectName("help8_png")
        self.horizontalLayout_15.addWidget(self.help8_png)
        spacerItem26 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_15.addItem(spacerItem26)
        self.verticalLayout.addLayout(self.horizontalLayout_15)
        self.celyLayout.addLayout(self.verticalLayout)
        spacerItem27 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.celyLayout.addItem(spacerItem27)
        self.label_export = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.label_export.setObjectName("label_export")
        self.celyLayout.addWidget(self.label_export)
        spacerItem28 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.celyLayout.addItem(spacerItem28)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_exporTo = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.label_exporTo.setObjectName("label_exporTo")
        self.gridLayout_2.addWidget(self.label_exporTo, 0, 0, 1, 1)
        spacerItem29 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem29, 0, 3, 1, 1)
        self.ChooseExportTo = QtWidgets.QComboBox(self.verticalLayoutWidget_3)
        self.ChooseExportTo.setEditable(False)
        self.ChooseExportTo.setObjectName("ChooseExportTo")
        self.ChooseExportTo.addItem("")
        self.ChooseExportTo.addItem("")
        self.gridLayout_2.addWidget(self.ChooseExportTo, 0, 1, 1, 1)
        self.gridLayout_ = QtWidgets.QGridLayout()
        self.gridLayout_.setObjectName("gridLayout_")
        self.label_saveTo = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.label_saveTo.setObjectName("label_saveTo")
        self.gridLayout_.addWidget(self.label_saveTo, 0, 0, 1, 1)
        self.saveToButton = QtWidgets.QToolButton(self.verticalLayoutWidget_3)
        self.saveToButton.setStatusTip("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("projektPng/addfilesicon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.saveToButton.setIcon(icon3)
        self.saveToButton.setIconSize(QtCore.QSize(22, 22))
        self.saveToButton.setPopupMode(QtWidgets.QToolButton.DelayedPopup)
        self.saveToButton.setObjectName("saveToButton")
        self.gridLayout_.addWidget(self.saveToButton, 0, 2, 1, 1)
        self.output = QtWidgets.QLineEdit(self.verticalLayoutWidget_3)
        self.output.setMinimumSize(QtCore.QSize(350, 0))
        self.output.setStatusTip("")
        self.output.setWhatsThis("")
        self.output.setAccessibleName("")
        self.output.setAccessibleDescription("")
        self.output.setInputMask("")
        self.output.setText("")
        self.output.setReadOnly(True)
        self.output.setObjectName("output")
        self.gridLayout_.addWidget(self.output, 0, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout_, 0, 4, 1, 1)
        self.celyLayout.addLayout(self.gridLayout_2)
        self.RunAnalysisPushButton.raise_()
        self.verticalLayoutWidget_3.raise_()
        self.logoTFpng.raise_()
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.actionRunAnalysis = QtWidgets.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/newPrefix/Downloads/run.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRunAnalysis.setIcon(icon4)
        self.actionRunAnalysis.setObjectName("actionRunAnalysis")

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # Vytvoření dialogu pro výběr souboru pro import:  
        self.insertFile1Button.clicked.connect(self.selectFileImport)
        # Vytvoření dialogu pro výběr složky pro export souborů: 
        self.saveToButton.clicked.connect(self.selectFileExport)
        # napojení tlačítka "RunAnalysisPushButton" na funkci "runAnalysisAccordingSettings"
        self.RunAnalysisPushButton.clicked.connect(lambda: runAnalysisAccordingSettings(self))

    # napojení tlačítka
    def selectFileImport(self):
        self.absPathCurrent = QtWidgets.QFileDialog.getOpenFileName()[0]
        self.inputFileName1.setText(self.absPathCurrent)
    # Potřeba změnit na výběr folderu a ne filu
    def selectFileExport(self):
        self.absPathOutput = QtWidgets.QFileDialog.getExistingDirectory()
        self.output.setText(self.absPathOutput)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "RTC Data Analysis"))
        self.RunAnalysisPushButton.setToolTip(_translate("MainWindow", "Run chosen analysis F5"))
        self.RunAnalysisPushButton.setText(_translate("MainWindow", "RUN ANALYSIS"))
        self.RunAnalysisPushButton.setShortcut(_translate("MainWindow", "F5"))
        self.label_insertFile.setText(_translate("MainWindow", "<html><head/><body><p><span style=\" font-size:18pt;\">1. INSERT FILE</span></p></body></html>"))
        self.InsertFile1.setText(_translate("MainWindow", "Insert file:"))
        self.insertFile1Button.setToolTip(_translate("MainWindow", "Insert file"))
        self.insertFile1Button.setText(_translate("MainWindow", "Add file"))
        self.label_chooseAnalysis.setText(_translate("MainWindow", "<html><head/><body><p><span style=\" font-size:18pt;\">2. CHOOSE ANALYSIS</span></p></body></html>"))
        self.Zadani1.setToolTip(_translate("MainWindow", "pomocka"))
        self.Zadani1.setText(_translate("MainWindow", "1. Severity and Priority check"))
        self.help1_png.setToolTip(_translate("MainWindow", "Returns WIs with Severity Blocker/Critical, but with Priority less than High."))
        self.Zadani2.setText(_translate("MainWindow", "2. Critical or Blocker not reproduced WIs "))
        self.help2_png.setToolTip(_translate("MainWindow", "How many (and what percentage) of WIs could not be reproduced? \n"
"How many of them were Critical/Blocker? Which SW Part has the most of these?"))
        self.Zadani3.setText(_translate("MainWindow", "3. Resolvers sorted by number of Critical/Blocker WI"))
        self.help3_png.setToolTip(_translate("MainWindow", "Sorts resolvers by number of Critical/Blocker WIs.\n"
"Returns chosen number of Resolvers with the most of Critical/Blocker WIs."))
        self.label_HowMany3.setText(_translate("MainWindow", "Return first"))
        self.Zadani4.setText(_translate("MainWindow", "4. WIs with Longest Planned Work"))
        self.help4_png.setToolTip(_translate("MainWindow", "Returns chosen number of WIs with the longest Planned Work."))
        self.label_HowMany4.setText(_translate("MainWindow", "Return first"))
        self.Zadani5.setText(_translate("MainWindow", "5. WIs with Longest Resolution Time"))
        self.help5_png.setToolTip(_translate("MainWindow", "Returns chosen number of WI with the longest Resolution time. \n"
"Note: Resolution time = ResolvedDate - CreationDate"))
        self.label_HowMany5.setText(_translate("MainWindow", "Return first"))
        self.Zadani6.setText(_translate("MainWindow", "6. Delayed Blocker or Critical WIs"))
        self.help6_png.setToolTip(_translate("MainWindow", "Returns WIs with Severity Critical/Blocker and Delayed resolution."))
        self.Zadani7.setText(_translate("MainWindow", "7. Sort Blocker/Critical WIs by SW Part"))
        self.help7_png.setToolTip(_translate("MainWindow", "Sorts \'Sw Part\' (Teams) by number of Blocking/Critical issues. Returns teams which have the most Blocker/Critical issues."))
        self.label_HowMany7.setText(_translate("MainWindow", "Return first"))
        self.Zadani8.setText(_translate("MainWindow", "8. Blocker/Critical WIs with Resolution \'Later\'"))
        self.help8_png.setToolTip(_translate("MainWindow", "Returns owners which selected Resolution \'Later\' on WIs with Severity Critical/Blocker."))
        self.label_export.setText(_translate("MainWindow", "<html><head/><body><p><span style=\" font-size:18pt;\">3. EXPORT</span></p></body></html>"))
        self.label_exporTo.setText(_translate("MainWindow", "Export to:"))
        self.ChooseExportTo.setCurrentText(_translate("MainWindow", "CSV"))
        self.ChooseExportTo.setItemText(0, _translate("MainWindow", "CSV"))
        self.ChooseExportTo.setItemText(1, _translate("MainWindow", "Terminal"))
        self.label_saveTo.setText(_translate("MainWindow", "Save to:"))
        self.saveToButton.setToolTip(_translate("MainWindow", "Add folder"))
        self.saveToButton.setText(_translate("MainWindow", "Add folder"))
        self.actionRunAnalysis.setText(_translate("MainWindow", "RunAnalysis"))
        self.actionRunAnalysis.setToolTip(_translate("MainWindow", "RunChoosenAnalysis"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
