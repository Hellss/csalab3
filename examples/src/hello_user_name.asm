first_message:
  .word '18What is your name?'

second_message:
  .word '8 Hello, '

exclamation_point:
  .word '!'

first_message_pointer:
  .word first_message

second_message_pointer:
  .word second_message

read_name_pointer:
  .word name

write_name_pointer:
  .word name

ascii_one:
  .word 48

number_ten:
  .word 10

in_addr:
  .word 1

out_addr:
  .word 2

_start:
  write_first_message:  ; Пишем первое сообщение
        mov r0, (first_message_pointer)
        mov r1, ascii_one
        sub r0, r1
        mov r1, number_ten
        mul r0, r1
        mov r3, first_message_pointer
        inc r3
        mov first_message_pointer, r3
        mov r1, (first_message_pointer)
        mov r2, ascii_one
        sub r1, r2
        add r0, r1
        inc r3
        mov first_message_pointer, r3
    load_first_message_char:
        mov r1, (first_message_pointer)
        dec r0
        jg write_first_message_char
        jmp read_name

   write_first_message_char:
    mov (out_addr), r1
    mov r1, first_message_pointer
    inc r1
    mov first_message_pointer, r1
    jmp load_first_message_char

   read_name:
    read_name_char:
      mov r1, (in_addr)
      mov r2, r1
    store_name_char:
      dec r1
      jng write_second_message
      inc r1
      mov r0, (in_addr)
      mov (read_name_pointer), r0
      dec r1
      jng write_second_message
      mov r0, read_name_pointer
      inc r0
      mov read_name_pointer, r0
      jmp store_name_char

  write_second_message:  ; Пишем второе сообщение
        mov r0, (second_message_pointer)
        mov r1, ascii_one
        sub r0, r1
        mov r3, second_message_pointer
        inc r3
        mov second_message_pointer, r3
    load_second_message_char:
        mov r1, (second_message_pointer)
        dec r0
        jg write_second_message_char
        jmp write_name

   write_second_message_char:
    mov (out_addr), r1
    mov r1, second_message_pointer
    inc r1
    mov second_message_pointer, r1
    jmp load_second_message_char

  write_name:  ; Пишем имя
    load_name_char:
     mov r1, (write_name_pointer)
     jmp write_name_char

    write_name_char:
     mov (out_addr), r1
     mov r1, write_name_pointer
     inc r1
     mov write_name_pointer, r1
     dec r2
     jnz load_name_char
     jmp write_exclamation_point

  write_exclamation_point:  ; Пишем восклицательный знак
    mov r0, exclamation_point
    mov (out_addr), r0
    hlt

name:
  .word 0