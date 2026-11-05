.intel_syntax noprefix
.code16
.arch i8086
.section .text
.global _start
.macro SNAP
 mov cs:[got_ax],ax
 mov cs:[got_bx],bx
 mov cs:[got_cx],cx
 mov cs:[got_dx],dx
 mov cs:[got_si],si
 mov cs:[got_di],di
 mov cs:[got_bp],bp
 mov cs:[got_sp],sp
 mov ax,ds
 mov cs:[got_ds],ax
 mov ax,es
 mov cs:[got_es],ax
 mov ax,ss
 mov cs:[got_ss],ax
 mov ax,cs
 mov cs:[got_cs],ax
 pushf
 pop word ptr cs:[got_flags]
 push cs
 pop ds
 call verify
.endm
_start:
 push cs
 pop ds
 push cs
 pop es
 mov ax,cs
 mov [expected_ds],ax
 mov [expected_es],ax
 mov [expected_ss],ax
 mov [expected_cs],ax
 mov dx,offset title
 call print
 mov word ptr [stage],6
 mov word ptr [phase],0
phase_loop:
 mov word ptr [input],0
mode_loop:
 cld
 mov di,offset generated
 mov cx,48
 mov al,0xcc
 rep stosb
 call defaults
 mov ax,[input]
 mov [frame+34],al
 mov word ptr [expected_cx],0
 mov ax,[phase]
 mov cl,8
 shl ax,cl
 mov [expected_dx],ax
 mov word ptr [expected_flags],0x244
 mov word ptr [seed],0x202
 mov word ptr [flagmask],0xec5
 mov bx,[phase]
 mov al,[lengths+bx]
 xor ah,ah
 mov [emitted_len],ax
 mov word ptr [suffix_len],0
 cmp word ptr [phase],0
 je expected_ready
 mov ax,[input]
 and ax,12
 xor ax,12
 mov [suffix_condition],ax
 mov dx,0x200
 or ax,ax
 jnz expected_nonzero
 or dx,0x44
 jmp expected_flags_done
expected_nonzero:
 cmp ax,12
 jne expected_flags_done
 or dx,4
expected_flags_done:
 mov [expected_flags],dx
 mov ah,0xc0
 cmp word ptr [phase],5
 jb expected_ax_done
 mov ah,0xc8
expected_ax_done:
 mov [expected_ax],ax
 cmp word ptr [suffix_condition],0
 je expected_ready
 add word ptr [emitted_len],8
 mov word ptr [suffix_len],8
 mov word ptr [expected_si],offset suffix_source+8
expected_ready:
 mov ax,offset generated
 add ax,[emitted_len]
 mov [expected_di],ax
 call load_regs
 mov di,offset generated
 mov cs:[expected_sp],sp
 call emitter
 SNAP
 mov bx,[phase]
 shl bx,1
 mov si,[expected_code_ptrs+bx]
 mov bx,[phase]
 mov cl,[lengths+bx]
 xor ch,ch
 mov di,offset generated
 jcxz rotate_bytes_done
rotate_byte_loop:
 mov al,[si]
 cmp al,[di]
 jne fail
 inc si
 inc di
 loop rotate_byte_loop
rotate_bytes_done:
 mov cx,[suffix_len]
 mov si,offset suffix_source
 jcxz suffix_bytes_done
suffix_byte_loop:
 mov al,[si]
 cmp al,[di]
 jne fail
 inc si
 inc di
 loop suffix_byte_loop
suffix_bytes_done:
 cmp byte ptr [di],0xcc
 jne fail
 inc word ptr [input]
 cmp word ptr [input],256
 jb mode_loop
 inc word ptr [phase]
 cmp word ptr [phase],8
 jb phase_loop
 mov dx,offset all_pass
 call print
 mov ax,0x4c00
 int 0x21
defaults:
 mov word ptr [expected_ax],0xa55a
 mov word ptr [expected_bx],0xb66b
 mov word ptr [expected_cx],0xc77c
 mov word ptr [expected_dx],0xd88d
 mov word ptr [expected_si],0x1991
 mov word ptr [expected_di],0x2aa2
 mov word ptr [expected_bp],offset frame+42
 ret
load_regs:
 mov ax,[expected_ax]
 mov bx,[expected_bx]
 mov cx,[expected_cx]
 mov dx,[expected_dx]
 mov si,[expected_si]
 mov di,[expected_di]
 mov bp,[expected_bp]
 push word ptr [seed]
 popf
 ret
verify:
 mov si,offset expected_ax
 mov di,offset got_ax
 mov cx,12
verify_reg:
 mov ax,[si]
 cmp ax,[di]
 jne fail
 inc si
 inc si
 inc di
 inc di
 loop verify_reg
 mov ax,[got_flags]
 xor ax,[expected_flags]
 and ax,[flagmask]
 jnz fail
 ret
callee:
 mov cs:[callee_sp],sp
 pushf
 pop word ptr cs:[callee_flags]
 ret
print:
 push ax
 cld
 mov ah,9
 int 0x21
 pop ax
 ret
printhex:
 push ax
 push bx
 push cx
 push dx
 mov bx,ax
 mov cx,4
hexloop:
 push cx
 mov cl,4
 rol bx,cl
 pop cx
 mov dl,bl
 and dl,15
 add dl,48
 cmp dl,57
 jbe decimal
 add dl,7
decimal:
 mov ah,2
 int 0x21
 loop hexloop
 pop dx
 pop cx
 pop bx
 pop ax
 ret
fail:
 push cs
 pop ds
 cld
 sti
 mov dx,offset failmsg
 call print
 mov ax,[stage]
 call printhex
 mov dx,offset inputmsg
 call print
 mov ax,[input]
 call printhex
 mov dx,offset patternmsg
 call print
 mov ax,[pattern]
 call printhex
 mov dx,offset phasemsg
 call print
 mov ax,[phase]
 call printhex
 mov dx,offset sitemsg
 call print
 mov ax,[site]
 call printhex
 mov dx,offset flagsmsg
 call print
 mov ax,[got_flags]
 call printhex
 mov dx,offset expectedmsg
 call print
 mov ax,[expected_flags]
 call printhex
 mov dx,offset newline
 call print
 mov ax,0x4c01
 int 0x21
emitter:
 .byte 0xc3
expected_ax: .word 0
expected_bx: .word 0
expected_cx: .word 0
expected_dx: .word 0
expected_si: .word 0
expected_di: .word 0
expected_bp: .word 0
expected_sp: .word 0
expected_ds: .word 0
expected_es: .word 0
expected_ss: .word 0
expected_cs: .word 0
got_ax: .word 0
got_bx: .word 0
got_cx: .word 0
got_dx: .word 0
got_si: .word 0
got_di: .word 0
got_bp: .word 0
got_sp: .word 0
got_ds: .word 0
got_es: .word 0
got_ss: .word 0
got_cs: .word 0
expected_flags: .word 0
got_flags: .word 0
flagmask: .word 0
seed: .word 0
stage: .word 0
input: .word 0
pattern: .word 0
phase: .word 0
site: .word 0
callee_sp: .word 0
callee_flags: .word 0
suffix_len: .word 0
suffix_condition: .word 0
emitted_len: .word 0
frame: .space 64
generated: .space 48
title: .ascii "VGA emitter full suffix semantics; relocated embedded address and CALL only\r\n$"
all_pass: .ascii "ALL PASS: 8 phases x 256 mode bytes = 2048 emitter cases; output, lengths, registers, defined flags\r\n$"
failmsg: .ascii "FAIL stage=$"
inputmsg: .ascii " mode=$"
patternmsg: .ascii " pattern=$"
phasemsg: .ascii " phase=$"
sitemsg: .ascii " site=$"
flagsmsg: .ascii " flags=$"
expectedmsg: .ascii " expected=$"
newline: .ascii "\r\n$"
lengths:
.byte 0x0,0x2,0x4,0x6,0x8,0x6,0x4,0x2
expected_code_ptrs: .word expected_code0,expected_code1,expected_code2,expected_code3,expected_code4,expected_code5,expected_code6,expected_code7
expected_code0:
.byte 0
expected_code1:
.byte 0xd0,0xc0
expected_code2:
.byte 0xd0,0xc0,0xd0,0xc0
expected_code3:
.byte 0xd0,0xc0,0xd0,0xc0,0xd0,0xc0
expected_code4:
.byte 0xd0,0xc0,0xd0,0xc0,0xd0,0xc0,0xd0,0xc0
expected_code5:
.byte 0xd0,0xc8,0xd0,0xc8,0xd0,0xc8
expected_code6:
.byte 0xd0,0xc8,0xd0,0xc8
expected_code7:
.byte 0xd0,0xc8
