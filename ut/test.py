import pandas as pd

class container():
    def __init__(self,parent=None,el={'top':0,'left':0,'width':0,'height':0},rawlayout=[]):
        if pd.isnull(parent):
            self.type='master'
        self.split1='top'
        self.split2='left'
        self.parent = parent
        self.elements = []
        self.elids = []
        self.containers = []
        self.top = el['top'];
        self.left = el['left'];
        self.height = el['height']
        self.width = el['width']
        self.y2=self.top+self.height
        self.x2=self.width+self.left
        if len(rawlayout)>0:
            for el in rawlayout:
                self.add(el)
    def add(self,el):
        if len(self.elements)==0:
            self.top=el['top']
            self.left=el['left']
            self.width=el['width']
            self.height= el['height']
        self.y2=max(self.y2,el['top']+el['height'])
        self.x2=max(self.x2,el['left']+el['width'])
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
            if self.type!='row':
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
                print (' '*shift+str(level*100+i)+' '+con.type+':'+str(con.elids))
                lodict[con.type+':'+str(level*100+i)]=con.print_elements(level*100+i,shift+1)
                i=i+1
            return lodict
        else:
            return self.elids

class row(container):
    def __init__(self,parent=None,el={'top':0,'left':0,'width':0,'height':0}):
        super(row,self).__init__(parent,el)
        self.split1='left'
        self.split2='top'
        self.type='row'

class column(container):
    def __init__(self,parent,el={'top':0,'left':0,'width':0,'height':0}):
        super(column,self).__init__(parent,el)
        self.split1='top'
        self.split2='left'
        self.type='column'

layout=[{'name': 'wrapper1', 'top': 0, 'height': 50, 'left': 0, 'width': 100},
        {'name': 'wrapper2', 'top': 0, 'height': 100, 'left': 300, 'width': 100},
        {'name': 'wrapper3', 'top': 0, 'height': 50, 'left': 500, 'width': 100},
        {'name': 'wrapper4', 'top': 0, 'height': 50, 'left': 600, 'width': 100},
        {'name': 'wrapper5', 'top': 50, 'height': 50, 'left': 0, 'width': 100},
        {'name': 'wrapper6', 'top': 150, 'height': 50, 'left': 0, 'width': 100},
        {'name': 'wrapper7', 'top': 150, 'height': 50, 'left': 100, 'width': 100},
        {'name': 'wrapper8', 'top': 150, 'height': 50, 'left': 200, 'width': 100},
        {'name': 'wrapper9', 'top': 200, 'height': 50, 'left': 0, 'width': 100},
        {'name': 'wrapper10', 'top': 200, 'height': 150, 'left': 300, 'width': 100},
        {'name': 'wrapper12', 'top': 200, 'height': 200, 'left': 400, 'width': 100},
        {'name': 'wrapper11', 'top': 400, 'height': 50, 'left': 1000, 'width': 100}
        ]
master=container(el={'top':0,'left':0,'width':1200,'height':1200},rawlayout=layout)
master.split_by_con()
master.print_elements()
