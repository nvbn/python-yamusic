# -*- coding: utf-8 -*-
# load js code from yandex
import urllib
data = urllib.urlopen('http://music.yandex.ru/_h5.js').read()
start = data.find('var z=String.fromCharCode;')
end = data.find('var i=C(Z)+C(Y)+C(X)+C(W);')
JS = data[start:][:end - start] + """
    var i = C(Z) + C(Y) + C(X) + C(W);
    i;
"""
