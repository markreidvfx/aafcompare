import pyExcelerator as excel

fnt = excel.Font()
fnt.name = 'Arial'
fnt.colour_index = 4
fnt.bold = True

borders = excel.Borders()
borders.left = 6
borders.right = 6
borders.top = 6
borders.bottom = 6

style = excel.XFStyle()
style.font = fnt
style.borders = borders


def make_rows(page,data,row,level,headers):
    row +=1
    black = 0 
    red = 2
    green = 3
    blue = 4
    
    color = black
    
    
    if data.has_key('status'):
        
        status = data['status']
        if status == 'Missing':
            color = red
        elif status == 'New':
            color = green
            
        elif status == 'Modified':
            color = blue
    
    fnt = excel.Font()
    #fnt.name = 'Arial'
    fnt.colour_index = color
    #fnt.bold = True
    style = excel.XFStyle()
    style.font = fnt
    
    for col,item in enumerate(headers):
        
        if data.has_key(item):
            
            page.write(row,col,str(data[item]),style)
        
        
    page.row(row).level= level
    
    if data.has_key('children'):
        for item in data['children']:
            row = make_rows(page,item,row,level+1,headers)
 
    return row
            



def make_page(page,data):
    
    info = data[0]
    print info
    
    
    
    headers = info['headers']
    
    
    row = 0
    
    for col,item in enumerate(headers):
        page.write(0,col,str(item))
    
    newlist = sorted(data[1:],key=lambda k: k['name'])
    
    for item in newlist:
        
        row = make_rows(page,item,row,0,headers)
        
        
        
        
    


def save_xls(data,path):
    
    print path
    wb = excel.Workbook()
 
    for page in ['summary','missing','new','shifted','modified','original','Editorial','DS Online']:
        
        ws = wb.add_sheet(page)
        
        make_page(ws,data[page])
        
        
        
    #info = data.pop(0)
    
    
    #print info
    
    
    wb.save(path)
