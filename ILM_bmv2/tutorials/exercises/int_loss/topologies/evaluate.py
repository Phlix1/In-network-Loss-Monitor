import sys
def evaluate(right_file, estimate_file):
    right = {}
    estimate = {}
    n=0
    err = 0.0
    fn=0
    fp=0
    with open(right_file, "r") as f:
        line = f.readline()
        while line:
            line = line[:-1]
            tmp = line.split(' ')
            right[(tmp[0],tmp[1])] = float(tmp[2])/100.0
            line=f.readline()
    with open(estimate_file, "r") as f:
         line = f.readline()
         while line:
             line = line[:-1]
             tmp = line.split(' ')
             estimate[(tmp[0],tmp[1])] = float(tmp[2])
             line=f.readline()
    for k in right.keys():
        is_find = False
        for m in estimate.keys():
            if (m[0]==k[0] and m[1]==k[1]) or (m[0]==k[1] and m[1]==k[0]):
                err += (estimate[m]-right[k])**2
                n += 1
                is_find = True
                break
        if is_find==False:
            err += (right[k])**2
            n += 1
            print(k)
            fn += 1
    print("False Negtive:", fn)
    for m in estimate.keys():
        is_find = False
        for k in right.keys():
            if (m[0]==k[0] and m[1]==k[1]) or (m[0]==k[1] and m[1]==k[0]):
                is_find = True
                break
        if is_find==False:
            err += (estimate[m])**2
            n += 1
            print(m)
            fp += 1
    print("False Postive:", fp)
    print("Error:", err)

if __name__ == '__main__':
    right_file = sys.argv[1]
    estimate_file = sys.argv[2]
    evaluate(right_file, estimate_file)
