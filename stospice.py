#!/usr/bin/env python

def stospice(filename, name, f, s, z0):
    dim = 100
    nports = s.shape[1]
    if nports > dim - 2:
        raise SystemExit('too many ports')
    z0 = z0 if hasattr(z0, '__len__') else [ z0 ] * nports 
    line = []
    nodes = " ".join(str(i+1) for i in range(nports+1))
    line.append(f'.SUBCKT {name} {nodes}')
    for i in range(nports):
        line.append(f"R{i+1}N {    (i+1)} {dim*(i+1)  } { -z0[i].real}")
        line.append(f"R{i+1}P {dim*(i+1)} {dim*(i+1)+1} {2*z0[i].real}")
    line.append('')
    for i in range(nports):
        for j in range(nports):
            index = (i * nports) + j + 1
            k = dim * (i + 1) + j + 1
            out = nports + 1 if j == nports - 1 else k + 1
            line.append(f'A{k} %vd({dim*(j+1)} {nports+1}) %vd({k}, {out}) xfer{index}')
            line.append(f'.model xfer{index} xfer R_I=true table=[')
            for n in range(len(s)):
                line.append(f'+ {f[n]} {s[n,i,j].real} {s[n,i,j].imag}') 
            line.append('+ ]')
            line.append('')
    line.append('.ENDS\n')
    text = '\n'.join(line)
    with open(filename, 'w') as fd:
        fd.write(text) 


if __name__ == '__main__':
    import os
    import sys
    import skrf
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs=1, help='s-parameter file to validate against')
    args = parser.parse_args()
    filename = args.filename[0]
    rootname = os.path.splitext(filename)[0]
    incfile = f'{rootname}.inc'
    nw = skrf.Network(filename)
    stospice(incfile, nw.name, nw.f, nw.s, nw.z0[0])
    



