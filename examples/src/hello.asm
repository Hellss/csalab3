  message:
    .word '12Hello world!' ; Наше сообщение

  ; Указатель на следующий символ для печати
  pointer:
    .word message

  number_ten:
   .word 10

  ascii_one:
   .word 48

  out_addr:
    .word 2

  _start:
    mov r0, (pointer)
    mov r1, ascii_one
    sub r0, r1
    mov r1, number_ten
    mul r0, r1
    mov r3, pointer
    inc r3
    mov pointer, r3
    mov r1, (pointer)
    mov r2, ascii_one
    sub r1, r2
    add r0, r1
    inc r3
    mov pointer, r3
   loop:
    mov r1, (pointer)
    dec r0
    jg write
    hlt

  write:
    mov (out_addr), r1
    mov r1, pointer
    inc r1
    mov pointer, r1
    jmp loop