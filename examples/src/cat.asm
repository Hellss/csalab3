in_addr:
  .word 1

out_addr:
  .word 2

_start:
  mov r0, (in_addr)
  mov r1, r0
 loop:
  dec r1
  jng exit
  inc r1
  mov r2, (in_addr)
  dec r1
  jg write
  hlt

write:
  mov (out_addr), r2
  jmp loop

exit:
    hlt