const fs = require('fs');

const text = fs.readFileSync('_ffl_part2.txt', 'utf8').split(/\r?\n/);

const consts = [];
let inConsts = false;
for (const line of text) {
  if (line.startsWith('_fk60s7 = ')) {
    inConsts = true;
    continue;
  }
  if (inConsts) {
    const m = line.match(/^  \[(\d+)\] (-?\d+)/);
    if (m) {
      consts[+m[1]] = +m[2];
      continue;
    }
    if (line.startsWith('_fbkq2f')) {
      inConsts = false;
    }
  }
}

const ops = [];
for (let i = 0; i < text.length; i++) {
  const m = text[i].match(/^  \[(\d+)\]/);
  if (!m) {
    continue;
  }
  const op = text[i + 2]?.match(/_fa9yk8 = (\d+)/)?.[1];
  const rawArgs = text[i + 3]?.match(/_fango5 = \[(.*)\]/)?.[1];
  if (op) {
    const args = rawArgs
      ? rawArgs.split(',').map((s) => s.trim()).filter(Boolean).map(Number)
      : [];
    ops[+m[1]] = { op: +op, args };
  }
}

function jint(x) {
  return x | 0;
}

function jbyte(x) {
  x &= 0xff;
  return x >= 128 ? x - 256 : x;
}

function newArray(type, length) {
  const arr = new Array(length).fill(0);
  arr.vmArrayType = type;
  return arr;
}

function truthUnary(v, mode) {
  switch (mode) {
    case 0: return v === 0;
    case 1: return v !== 0;
    case 2: return v < 0;
    case 3: return v >= 0;
    case 4: return v > 0;
    case 5: return v <= 0;
    default: return false;
  }
}

function truthCmp(a, b, mode) {
  switch (mode) {
    case 0: return a === b;
    case 1: return a !== b;
    case 2: return a < b;
    case 3: return a >= b;
    case 4: return a > b;
    case 5: return a <= b;
    default: return false;
  }
}

function run(inputBytes, { trace = false, maxSteps = 100000 } = {}) {
  const ilocals = new Array(16).fill(0);
  const olocals = new Array(16).fill(null);
  const stack = [];
  olocals[0] = inputBytes.map(jbyte);
  let pc = 0;
  let steps = 0;

  function popInt() {
    return jint(stack.pop());
  }

  function pushInt(v) {
    stack.push(jint(v));
  }

  function popObj() {
    return stack.pop();
  }

  while (pc >= 0 && pc < ops.length) {
    if (++steps > maxSteps) {
      throw new Error('VM step limit exceeded');
    }
    const ins = ops[pc];
    if (!ins) {
      throw new Error(`no instruction at ${pc}`);
    }
    const { op, args } = ins;
    if (trace) {
      const top = stack.slice(-6).map((v) => Array.isArray(v) ? `[${v.join(',')}]` : String(v)).join(' ');
      console.log(`${pc}: op ${op}(${args.join(',')}) stack=[${top}] iloc=${JSON.stringify(ilocals.slice(0, 8))}`);
    }
    pc++;
    switch (op) {
      case 13: {
        const a = popInt();
        const b = popInt();
        pushInt(b ^ a);
        break;
      }
      case 17: {
        pushInt(popObj().length);
        break;
      }
      case 18: {
        pushInt(consts[args[0]]);
        break;
      }
      case 20: {
        stack.push(olocals[args[0]]);
        break;
      }
      case 21: {
        const a = popInt();
        const b = popInt();
        pushInt(b | a);
        break;
      }
      case 26: {
        const top = popInt();
        const below = popInt();
        if (truthCmp(below, top, args[0])) {
          pc = args[1];
        }
        break;
      }
      case 28: {
        const shift = popInt() & 31;
        const value = popInt();
        pushInt(value >>> shift);
        break;
      }
      case 32: {
        const length = popInt();
        stack.push(newArray(args[0], length));
        break;
      }
      case 33: {
        pushInt(popInt() + consts[args[0]]);
        break;
      }
      case 35: {
        const value = popInt();
        if (truthUnary(value, args[0])) {
          pc = args[1];
        }
        break;
      }
      case 36: {
        pushInt(popInt() ^ consts[args[0]]);
        break;
      }
      case 39: {
        const type = args[0];
        if (type !== 1) {
          throw new Error(`unimplemented array store type ${type}`);
        }
        const value = popInt();
        const index = popInt();
        const arr = popObj();
        arr[index] = jint(value);
        break;
      }
      case 43: {
        const shift = popInt() & 31;
        const value = popInt();
        pushInt(value << shift);
        break;
      }
      case 47: {
        const a = popInt();
        const b = popInt();
        pushInt(b + a);
        break;
      }
      case 51: {
        pushInt(ilocals[args[0]]);
        break;
      }
      case 65: {
        ilocals[args[0]] = jint(ilocals[args[0]] + args[1]);
        break;
      }
      case 77: {
        pc = args[0];
        break;
      }
      case 79: {
        olocals[args[0]] = popObj();
        break;
      }
      case 80: {
        ilocals[args[0]] = popInt();
        break;
      }
      case 85: {
        const type = args[0];
        const index = popInt();
        const arr = popObj();
        if (type === 1) {
          pushInt(arr[index]);
        } else if (type === 6) {
          pushInt(jbyte(arr[index]));
        } else {
          throw new Error(`unimplemented array load type ${type}`);
        }
        break;
      }
      case 93: {
        pushInt(popInt() & consts[args[0]]);
        break;
      }
      case 104: {
        pushInt(ilocals[args[0]] + consts[args[1]]);
        break;
      }
      case 106: {
        return popInt();
      }
      default:
        throw new Error(`unimplemented op ${op} at ${pc - 1}`);
    }
  }
  throw new Error('fell off VM');
}

function formatOps() {
  return ops.map((ins, i) => `${i}: ${ins.op}(${ins.args.join(',')})`).join('\n');
}

if (require.main === module) {
  const arg = process.argv[2] || 'AAAAAAAAAAAAAAAA';
  const bytes = [...Buffer.from(arg, 'utf8')];
  console.log(run(bytes, { trace: process.argv.includes('--trace') }));
}

module.exports = { consts, ops, run, formatOps, jbyte, jint };
