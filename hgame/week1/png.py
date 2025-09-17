input = open('hky.png', 'rb')
input_all = input.read()
ss = input_all[::-1]
output = open('output.jpg', 'wb')
output.write(ss)
input.close()
output.close()
