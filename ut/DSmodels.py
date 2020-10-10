import os
import io
import numpy
from pandas import DataFrame
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

def readFiles(path):
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            path = os.path.join(root, filename)

            inBody = False
            lines = []
            f = io.open(path, 'r', encoding='latin1')
            for line in f:
                if inBody:
                    lines.append(line)
                elif line == '\n':
                    inBody = True
            f.close()
            message = '\n'.join(lines)
            yield path, message


def dataFrameFromDirectory(path, classification):
    rows = []
    index = []
    for filename, message in readFiles(path):
        rows.append({'message': message, 'class': classification})
        index.append(filename)

    return DataFrame(rows, index=index)

data = DataFrame({'message': [], 'class': []})

data = data.append(dataFrameFromDirectory(r'C:\DataScience-Python3\emails\spam', 'spam'))
data = data.append(dataFrameFromDirectory(r'C:\DataScience-Python3\emails\ham', 'ham'))

### Naive Bayes
from sklearn.model_selection import train_test_split

train,test = train_test_split(data,test_size=.2)

## train
vectorizer = CountVectorizer()
counts = vectorizer.fit_transform(train['message'].values)
classifier = MultinomialNB()
targets = train['class'].values
classifier.fit(counts, targets)

test_counts=vectorizer.transform(test['message'])
predictions = classifier.predict(test_counts)
#predictions[:5]

from sklearn.metrics import accuracy_score

accuracy_score(test['class'], predictions)


### SVM --> SVC
import pandas as pd
from sklearn.model_selection import train_test_split
ds=pd.DataFrame({'x':X[:,0],'y':X[:,1],'res':y})
train, test = train_test_split(ds)

from sklearn import svm, datasets

C = 10
model_svc=svm.SVC(kernel='linear',gamma='scale', C=C)
model_linearsvc=svm.LinearSVC(C=C,max_iter=10000,dual=True)

svc=model_svc.fit(train[['x','y']].to_numpy(), train['res'])
linearsvc=model_linearsvc.fit(train[['x','y']].to_numpy(), train['res'])

predictions_svc = svc.predict(test[['x','y']].to_numpy())
#predictions_linearsvc = linearsvc.predict(test[['x','y']].to_numpy())

from sklearn.metrics import accuracy_score
print ('svc',accuracy_score(test['res'], predictions_svc))
#print ('linearsvc',accuracy_score(test['res'], predictions_linearsvc))

### K - neigbourns
from sklearn.neighbors import KNeighborsClassifier as KNN
from sklearn import datasets
iris = datasets.load_iris()

import pandas as pd
df=pd.DataFrame(iris.data,columns=iris['feature_names'])
iris['feature_names']

from sklearn.model_selection import train_test_split
X_train,X_test, y_train, y_test = train_test_split(df,iris['target'])

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(X_train)

X_train = scaler.transform(X_train)
X_test = scaler.transform(X_test)

from sklearn.neighbors import KNeighborsClassifier
classifier = KNeighborsClassifier(n_neighbors=5)
classifier.fit(X_train, y_train)

y_pred=classifier.predict(X_test)

from sklearn.metrics import classification_report, confusion_matrix
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))

print ('score_test',classifier.score(X_test,y_test))
print ('score_train',classifier.score(X_train,y_train))

### linear regression

