import pandas as pd

def sort_layout(input_layout):
    return sorted(input_layout, key=lambda k: (k['top'], k['left']))

class container():
    def __init__(self,parent=None,mel={'top':0,'left':0,'width':0,'height':0},rawlayout=[]):
        if pd.isnull(parent):
            self.type='master'
        self.split1='top'
        self.split2='left'
        self.parent = parent
        self.elements = []
        self.elids = []
        self.containers = []
        self.top = mel['top'];
        self.left = mel['left'];
        self.height = mel['height']
        self.width = mel['width']
        self.y2=self.top+self.height
        self.x2=self.width+self.left
        if len(rawlayout)>0:
            for el in sort_layout(rawlayout):
                self.add(el)
    def add(self,el):
        if len(self.elements)==0:
            self.top=el['top']
            self.left=el['left']
            self.width=el['width']
            self.height= el['height']
        self.y2=max(self.y2,el['top']+el['height'])
        self.x2=max(self.x2,el['left']+el['width'])
        self.width=self.x2-self.left
        self.elements.append(el)
        self.elids.append(el['name'])
    def incontainer(self,el):
        if not el['name'] in self.elids:
            return (el['top']>=self.top) and (el['top']+el['height']<=self.y2) and (el['left']>=self.left) and (el['left']+ el['width']<=self.x2)
        return False
    def check(self,el):
        return (getattr(self,self.split2)==el[self.split2]) or (len(self.elements)==0)
    def split_by_con(self):
        layout = sorted(self.elements, key=lambda k: (k[self.split1], k[self.split2]),reverse=True)
        while len(layout)>0:
            if self.type!='Row':
                con = row(parent=self)
            else:
                con = column(parent=self)
            #need 2 rounds
            for i in range(len(layout)-1,-1,-1):
                el=layout[i]
                if con.check(el):
                    con.add(el)
                    layout.pop(i)
            for i in range(len(layout)-1,-1,-1):
                el=layout[i]
                if con.incontainer(el):
                    con.add(el)
                    layout.pop(i)
            self.containers.append(con)
            if len(con.elements)>1:
                con.split_by_con();

    def print_elements(self,level=0,shift=0):
        lodict={}
        i=1;
        if len(self.containers)>0:
            for con in self.containers:
#                print (' '*shift+str(level*100+i)+' '+con.type+':'+str(con.elids))
                lodict[con.type+':'+str(level*100+i)+':'+str(con.width)+':col-md-'+str(int(12/(self.width/con.width)))]=con.print_elements(level*100+i,shift+1)
                i=i+1
            return lodict
        else:
            return self.elids[0]
    def set_relative_width(self):
        for e in self.containers:
            pass

class row(container):
    def __init__(self,parent):
        super(row,self).__init__(parent)
        self.split1='left'
        self.split2='top'
        self.type='Row'

class column(container):
    def __init__(self,parent):
        super(column,self).__init__(parent)
        self.split1='top'
        self.split2='left'
        self.type='Column'

#req={"settings":{"width":1200,"height":500,"NinRow":6,"gridwidth":200,"gridheight":100},"layout":[{"name":"Code","top":0,"height":1,"left":0,"width":1},{"name":"ClientName","top":0,"height":1,"left":1,"width":5},{"name":"Segment","top":1,"height":1,"left":0,"width":1},{"name":"Contact","top":1,"height":1,"left":1,"width":1},{"name":"ClientCode","top":1,"height":1,"left":2,"width":1},{"name":"StartDate","top":1,"height":3,"left":3,"width":3},{"name":"Description","top":4,"height":1,"left":0,"width":6},{"name":"VendorCode","top":2,"height":1,"left":0,"width":3},{"name":"From Create","top":3,"height":1,"left":0,"width":3}]}
#layout=req['layout']

#master=container(mel={'top':0,'left':0,'width':1200,'height':1200},rawlayout=layout)
#master.split_by_con()
#master.print_elements()
