def next_epoch(this_epoch, numepo):
    if this_epoch < numepo:
        this_epoch += 1      
    return this_epoch

def prev_epoch(this_epoch):
    if this_epoch > 0:
        this_epoch -= 1   
    return this_epoch 