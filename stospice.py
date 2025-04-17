#!/usr/bin/env python



def extract_comments(infilename):
    comments = []
    with open(infilename, "r") as ifd:
        lines = ifd.read().splitlines()
    for line in lines:
        line = line.strip()
        if not line.startswith("!"):
            continue
        comments.append(f"* {line[1:]}")
    return comments


def stospice(filename, name, f, s, z0, comments=None):
    dim = 100
    nports = s.shape[1]
    if nports > dim - 2:
        raise SystemExit('too many ports')
    z0 = z0 if hasattr(z0, '__len__') else [ z0 ] * nports 
    lines = []
    ports = list(range(1, nports+1))
    nodes = " ".join(f"{p}" for p in ports)
    nodes += " gnd_node"
    lines.append(f"*\n*** Example use in SPICE:")
    port_names = " ".join(f"Port{p}" for p in ports)
    lines.append(f"**  X<inst> {name} {port_names} GND")
    lines.append("")
    lines.append(f'.SUBCKT {name} {nodes}')
    lines.append(f"Vgnd_node_{nports+1} {nports+1} gnd_node 0")
    for i in range(nports):
        lines.append(f"R{i+1}N {    (i+1)} {dim*(i+1)  } { -z0[i].real}")
        lines.append(f"R{i+1}P {dim*(i+1)} {dim*(i+1)+1} {2*z0[i].real}")
    lines.append('')
    for i in range(nports):
        for j in range(nports):
            index = (i * nports) + j + 1
            k = dim * (i + 1) + j + 1
            out = nports + 1 if j == nports - 1 else k + 1
            lines.append(f'A{k} %vd({dim*(j+1)} {nports+1}) %vd({k}, {out}) xfer{index}')
            lines.append(f'.model xfer{index} xfer R_I=true table=[')
            for n in range(len(s)):
                lines.append(f'+ {f[n]} {s[n,i,j].real} {s[n,i,j].imag}') 
            lines.append('+ ]')
            lines.append('')
    lines.append('.ENDS\n')
    text = ""
    if comments:
        text += "\n".join(comments)
        text += "\n"
    text += '\n'.join(lines)
    with open(filename, 'w+') as fd:
        fd.write(text) 

if __name__ == '__main__':
    from pathlib import Path
    import skrf
    import argparse
    parser = argparse.ArgumentParser(
        description="stospice:  A program that converts S-Parameter (*.S[234]P) files into a spice netlist .inc file")
    parser.add_argument('filename', type=str, help='s-parameter file to convert to SPICE netlist')
    parser.add_argument('-o', dest="overwrite",  action="store_true", help="Force overwrite exsting output", default=False)
    args = parser.parse_args()
    filename = Path(args.filename)
    incfile = filename.with_suffix('.inc')
    if incfile.exists and not args.overwrite:
        raise IOError("Output file {incfile} exists, use -o to overwrite")
    nw = skrf.Network(filename)
    comments = extract_comments(filename)
    name = nw.name
    stospice(incfile, name, nw.f, nw.s, nw.z0[0], comments)
    print(f"Converted {filename} to {incfile} and created SPICE sub-circuit {name}")


    



