
import sys
import os
import tempfile
import unittest
import subprocess
import numpy as np
from stospice import stospice


def run_ngspice(text):
    name = tempfile.mktemp(dir='')
    with open(name, "wb") as f:
        f.write(text.encode()) 
    command = [ 'ngspice', '-b', name ]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()
    result = proc.stdout.read().decode().rstrip()
    error = proc.stderr.read().decode().rstrip()
    proc.stdout.close()
    proc.stderr.close()
    os.unlink(name)
    return result, error


def read_subcir(filename):
    with open(filename) as fd:
        text = fd.read()
    data = {}
    lines = text.splitlines()
    for ln in lines:
        token = ln.split()
        if len(token) > 3 and token[0].lower() == '.subckt':
            name = token[1]
            ports = token[2:]
            data[name] = len(ports)
    return data


def sparameters(filename, name, nports, f, z0):
    z0 = z0 * np.ones(nports)
    points = len(f)
    res = np.zeros((points, nports, nports), dtype=complex)
    for n in range(nports):
        text = []
        text.append('circuit')
        text.append(f'v{n+1} 100 0 dc 0 ac 2') # 2 volts
        text.append(f'r{n+1} 100 v{n+1} {z0[n].real}')
        for m in range(nports):
            if m != n: 
                text.append(f'r{m+1} v{m+1} 0 {z0[m].real}')
        nodes = " ".join(f'v{i+1}' for i in range(nports))
        text.append(f'x1 {nodes} 0 {name}')
        text = '\n'.join(text)
        tempname = tempfile.mktemp(dir='')
        csvfile = f'{tempname}.csv'
        text += f"""
            .control
            set wr_singlescale
            set numdgt=16
            ac lin {points} {f[0]:e} {f[-1]:e}
            wrdata {csvfile} {nodes}
            .endc
            .include {filename}
            .end"""
        run_ngspice(text)
        with open(csvfile) as fd:
            data = [ [ float(d) for d in ln.split() ] for ln in fd.readlines() ] 
        os.unlink(csvfile)
        data = np.array(data)
        g = data[:,1::2] + data[:,2::2] * 1j
        g[:,n] -= 1
        res[:,:,n] = g
    return res


def analyze(filename, name, f, z0, individual=False):
    subcir = read_subcir(filename)
    nports = subcir[name] - 1
    if individual:
        points = len(f) 
        res = np.zeros((points, nports, nports), dtype=complex)
        for i in range(points):
            print(f'sweeping point {i+1} / {points} at {f[i]/1e6:.3f} MHz')
            res[i,:,:] = sparameters(filename, name, nports, f[i:i+1], z0)
    else:
        res = sparameters(filename, name, nports, f, z0)
    return res


def test_random_smatrix(nports=None):
    nports = nports or np.random.randint(1, 10)
    points = 4
    shape = (points, nports, nports)
    s = np.random.rand(*shape) + 1j * np.random.rand(*shape)
    s = 10 * s
    f = np.linspace(1e6, 100e6, points)
    z0 = 100 * abs(np.random.rand(nports))
    print(f'simulating a {points} point {nports}x{nports} sparameter matrix')
    print('z0 =', z0)
    name = tempfile.mktemp(dir='')
    incfile = f'{name}.inc'
    stospice(incfile, name, f, s, z0)
    res = analyze(incfile, name, f, z0)
    os.unlink(incfile)
    error = (res - s) * np.logical_not(np.isclose(res, s))
    print('error difference =')
    print(error)
    return error
 
 
###

class TestStospice(unittest.TestCase):
    def test_stospice(self):
        error = test_random_smatrix()
        self.assertTrue(np.all(error == 0))


if __name__ == '__main__':
    import skrf
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='?', help='s-parameter file to validate against')
    parser.add_argument('--ports', type=int, help='number of ports to simulate against')
    args = parser.parse_args()
    if args.filename:
        filename = args.filename
        name = os.path.splitext(filename)[0]
        nw = skrf.Network(filename)
        incfile = f'{name}.inc'
        s = nw.s
        z0 = nw.z0[0]
        stospice(incfile, name, nw.f, s, z0)
        res = analyze(incfile, name, nw.f, z0, individual=True)
        os.unlink(incfile)
        error = (res - s) * np.logical_not(np.isclose(res, s))
        print('error difference =')
        print(error)
    else:
        error = test_random_smatrix(args.ports)


   
