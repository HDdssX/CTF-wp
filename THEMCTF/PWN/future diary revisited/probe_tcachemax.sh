#!/usr/bin/env bash
set -euo pipefail

cat >/tmp/tcachemax.c <<'C'
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
  for (size_t r = 0x3f0; r <= 0x800; r += 0x80) {
    void *p = malloc(r);
    void *guard = malloc(0x20);
    free(p);
    uint64_t *q = (uint64_t *)p;
    printf("req=%#zx p=%p guard=%p q0=%#lx q1=%#lx\n", r, p, guard, q[0], q[1]);
    free(guard);
  }
  return 0;
}
C

gcc /tmp/tcachemax.c -o /tmp/tcachemax
/tmp/tcachemax
