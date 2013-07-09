# -*- coding: cp1252 -*-
'''Cleans up the html generated by the Dossier Etudiant of Polytechnique'''
'''Depends on BeautifulSoup for xml tree manipulation'''

from bs4 import BeautifulSoup
import colorsys
import re
import urllib

def getSpacedRGB(nbCols, lih = 0.7, sat = 0.8):
    ret = []
    for n in xrange(nbCols):
        h = float(n)/nbCols
        ret.append(tuple(int(c*255) for c in colorsys.hls_to_rgb(h, lih, sat)))
    return ret
    
def writeTables(tables):
    '''Save html content of elements in tables to html file'''
    output = file('result.html', 'w')
    
    output.write('''<html><head>
<link rel="stylesheet" type="text/css" href="result.css" />
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>Horaire Personnel</title></head>''')
    output.write('<center>')
    for table in tables:
        s = table.prettify()
        output.write(s.encode("iso-8859-1"))
        output.write('<br>')
    output.write('</center>')
    output.write('</html>')
    output.close()

def insertBR(matchobj):
    txt = matchobj.group(1)
    #Detect if the match is a room number
    if txt[0] in 'ABCML' and txt[1] == '-':
        return txt
    return txt + '<br />'

#File to be formatted
#Parse command arguments for the file to be formatted
if len(sys.argv) != 2:
    print "Invalid number of arguments. Looking for one filename"
    sys.exit(2)

filePath = sys.argv[1]

if not os.path.isfile(filePath):
    print "Invalid file passed as parameter"
    sys.exit(2)

txt = open(filePath).read()

#Preparser formatting
txt = txt.replace('<br>','<br />').replace('� d�terminer','')
txt = re.sub('</?center>','',txt)
txt = re.sub('</?font.*?>','',txt)

#insert new line after course name
genieRe = '[A-Z]{1,4}-?([A-Z]{3})?'
numRe = '[0-9]{3,4}[A-Z]?'
sigleRe = '(' + genieRe + numRe + ')'
txt = re.sub(sigleRe, insertBR,txt)

soup = BeautifulSoup(txt) #Parse html
tables = soup.find_all('table') #Extract tables

#remove all table formatting
for table in tables:
    table.attrs.clear() #Clear attributes

#Remove all td attributes other than colspan
for td in soup.find_all('td'):
    for key in td.attrs.keys():
        if key != 'colspan':
            del td.attrs[key]

#format text from shedule
for txt in soup.findAll(text=True):
    s = re.sub('\([0-9]{2}\)','', txt) # remove group numbers
    s = s.replace(' Hebdo.','').replace('Lab. ','Lab').replace('Lab.','Lab').replace('2 sem. ','')
    txt.replaceWith(s)

#convert shedule DOM to 2D array
shedule = tables[5]
rows = shedule.findAll('tr')
arr = []
for i, tr in enumerate(rows):
    arr.append([])
    cols = tr.findAll('td')
    for td in cols:
        arr[i].append(td)

arr.pop(0) #remove empty dim
arr = zip(*arr) #transpose shedule

#add rowspan attributes and mark cells to remove
for i in range(0,len(arr)): #row
    for j in xrange(0,len(arr[i])-1): #col index of first cell
        for k in xrange(j+1,len(arr[i])): #col index of second cell
            if len(arr[i][j].text) > 1 and arr[i][j].text == arr[i][k].text:
                arr[i][k]['dirt']= True
                if arr[i][j].get('rowspan') == None:
                    arr[i][j]['rowspan'] = 2
                else:
                    arr[i][j]['rowspan'] += 1
            else:
                break #No match, exit current second cell loop

#find and remove marked cells
dirty = shedule.findAll(dirt=True)
for d in dirty:
    d.extract()

#add Class Name to cells
tds = [t.parent for t in soup.findAll(text=re.compile(sigleRe))] #get td with sigle
courses = set()
for td in tds:
    course = str(td.contents[0])
    courses.add(course)
    td['class'] = course
#print courses

cols = getSpacedRGB(len(courses))
fstr = '.{} {{ background-color:rgb{};}}'
colCSSarr = [fstr.format(course,str(col)) for course, col in zip(courses, cols)]
colCSS = '\n'.join(colCSSarr)
#print colCSS

#genCSS
css = '''td,th
{
border:1px solid black;
text-align:center;
padding: 5px;
font-family:Arial,Helvetica,sans-serif;
/*Make chrome print the background color*/
-webkit-print-color-adjust:exact;
}

table
{
border:1px solid black;
border-collapse:collapse;
width: 815px;
}
'''+colCSS
with open('result.css','w') as out_file:
    out_file.write(css)

#save result
writeTables((tables[1], tables[3], shedule))
