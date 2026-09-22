OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
ry(0.83) q[0];
cx q[0],q[1];
ry(0.83) q[1];
