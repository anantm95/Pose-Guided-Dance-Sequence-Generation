import matplotlib.pyplot as plt

fname = '/Users/nivedha.sivakumar94/Desktop/DL/FinalProject/log_vgg.txt'
with open(fname) as f:
    content = f.readlines()

# Get loss from log.txt
loss_list = []
for line in content:
    if line.startswith('INFO:__main__:loss: '):
        line_parts = line.split('INFO:__main__:loss: ')
        loss = line_parts[1].split('\n')[0]
        loss_list.append(float(loss))

# Plot loss
plt.plot(loss_list)
plt.title('Training loss')
plt.ylabel('Generator Loss')
plt.xlabel('Training Iterations')
plt.show()
plt.close()
