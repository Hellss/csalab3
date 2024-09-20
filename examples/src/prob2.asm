max_limit:
  .word 4000000    ; Максимальное значение для чисел Фибоначчи (4 миллиона)
a:
  .word 1          ; Первое число Фибоначчи
b:
  .word 1          ; Второе число Фибоначчи
sum_even:
  .word 0          ; Сумма четных чисел Фибоначчи
out_addr:
  .word 3          ; Адрес для вывода суммы
div2:
  .word 2

_start:
  loop:
    mov r0, b            ; Загрузка значения b в r0
    mov r1, max_limit    ; Загрузка значения max_limit в r1
    sub r1, r0           ; Вычитание r0 из r1 (r1 = max_limit - b)
    jng output           ; Если b >= max_limit, переход к метке output

    mov r2, r0           ; r2 = b
    mov r3, div2         ; r3 = 2
    mod r2, r3           ; r2 = b % 2
    jnz next_fib         ; Если b нечетное, переход к метке next_fib

    mov r3, sum_even     ; Загрузка значения sum_even в r3
    add r3, r0           ; r3 = sum_even + b
    mov sum_even, r3     ; Сохранение r3 в sum_even

  next_fib:
    mov r2, a            ; Загрузка значения a в r2
    add r2, r0           ; r2 = a + b
    mov a, r0            ; Сохранение текущего b в a
    mov b, r2            ; Сохранение нового значения b (a + b)
    jmp loop             ; Переход к началу цикла loop

  output:
    mov r0, sum_even     ; Загрузка значения sum_even в r0
    mov (out_addr), r0   ; Сохранение r0 в памяти по адресу out_addr
    hlt                  ; Остановка программы