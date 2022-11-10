from imghdr import tests
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

x= np.array([7, -7, -15, -20, -25]).reshape((-1,1))
y=np.array([5.61, 2.61, 2.39, 2.18, 2.01])

x_ = PolynomialFeatures(degree=2, include_bias=False).fit_transform(x)
model = LinearRegression().fit(x_, y)

input=8
test=np.array([input]).reshape((-1,1))
test_=PolynomialFeatures(degree=2, include_bias=False).fit(test).transform(test)

print
print(f"Ennuste: {model.predict(test_)}")

