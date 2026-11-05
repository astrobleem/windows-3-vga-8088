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
 mov ax,cs
 mov [expected_cs],ax
 mov [expected_ss],ax
 add ax,0x2000
 mov [expected_ds],ax
 mov [ds_seg],ax
 mov es,ax
 mov di,0x4000
 mov cx,514
 mov al,0x99
 call fill_source
 mov ax,cs
 add ax,0x1000
 mov [expected_es],ax
 mov [es_seg],ax
 mov es,ax
 mov di,0x4000
 mov cx,514
 mov al,0x55
 call fill_source
 push cs
 pop es
 mov di,0x4000
 mov cx,514
 mov al,0x11
 call fill_source
 mov ax,[es_seg]
 mov es,ax
 mov dx,offset title
 call print
 mov word ptr [stage],5
 mov word ptr [site],0
site_loop:
 mov bx,[site]
 shl bx,1
 mov ax,[thunk_ptrs+bx]
 mov [current_entry],ax
 mov bx,[site]
 mov al,[widths+bx]
 xor ah,ah
 mov [width],ax
 mov al,[source_bases+bx]
 mov [source_base],al
 mov word ptr [input],0
count_loop:
 mov bx,[input]
 shl bx,1
 mov ax,[counts+bx]
 mov [count],ax
 mul word ptr [width]
 mov [byte_count],ax
 mov word ptr [pattern],0
pattern_loop:
 cld
 mov ax,[es_seg]
 mov es,ax
 mov di,0x4ff0
 mov cx,546
 mov al,0xcc
 rep stosb
 mov bx,[pattern]
 shl bx,1
 mov ax,[flag_seeds+bx]
 mov [seed],ax
 mov [expected_flags],ax
 mov word ptr [flagmask],0xed5
 call defaults
 mov word ptr [expected_cx],0
 mov word ptr [start_si],0x4000
 mov word ptr [start_di],0x5000
 mov word ptr [first_changed],0
 mov ax,[byte_count]
 mov [last_changed],ax
 test word ptr [seed],0x400
 jz forward
 mov word ptr [start_si],0x4200
 mov word ptr [start_di],0x5200
 mov ax,[width]
 add ax,512
 mov [last_changed],ax
 sub ax,[byte_count]
 mov [first_changed],ax
 mov ax,[start_si]
 sub ax,[byte_count]
 mov [expected_si],ax
 mov ax,[start_di]
 sub ax,[byte_count]
 mov [expected_di],ax
 jmp loaded_expected
forward:
 mov ax,[start_si]
 add ax,[byte_count]
 mov [expected_si],ax
 mov ax,[start_di]
 add ax,[byte_count]
 mov [expected_di],ax
loaded_expected:
 call load_regs
 mov cx,cs:[count]
 mov si,cs:[start_si]
 mov di,cs:[start_di]
 mov ax,cs:[ds_seg]
 mov ds,ax
 mov ax,0xa55a
 mov cs:[expected_sp],sp
 call word ptr cs:[current_entry]
 SNAP
 xor bx,bx
memory_loop:
 mov al,0xcc
 cmp bx,[first_changed]
 jb compare_byte
 cmp bx,[last_changed]
 jae compare_byte
 mov al,[source_base]
 add al,bl
compare_byte:
 cmp al,es:[bx+0x5000]
 jne fail
 inc bx
 cmp bx,514
 jb memory_loop
 mov bx,0
canary_loop:
 cmp byte ptr es:[bx+0x4ff0],0xcc
 jne fail
 cmp byte ptr es:[bx+0x5202],0xcc
 jne fail
 inc bx
 cmp bx,16
 jb canary_loop
 inc word ptr [pattern]
 cmp word ptr [pattern],256
 jb pattern_loop
 inc word ptr [input]
 cmp word ptr [input],8
 jb count_loop
 inc word ptr [site]
 cmp word ptr [site],10
 jb site_loop
 sti
 cld
 mov dx,offset all_pass
 call print
 mov ax,0x4c00
 int 0x21
fill_source:
 cld
fill_source_loop:
 stosb
 inc al
 loop fill_source_loop
 ret
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
thunk0:
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
current_entry: .word 0
ds_seg: .word 0
es_seg: .word 0
width: .word 0
count: .word 0
byte_count: .word 0
first_changed: .word 0
last_changed: .word 0
start_si: .word 0
start_di: .word 0
source_base: .byte 0
frame: .space 64
title: .ascii "VGA exact REP+segment trampoline semantics; 8086-prefetch\r\n$"
all_pass: .ascii "ALL PASS: 10 sites x 8 counts x 256 flag seeds = 20480 cases; full registers, flags, copy bytes, guard bytes\r\n$"
failmsg: .ascii "FAIL stage=$"
inputmsg: .ascii " count_index=$"
patternmsg: .ascii " pattern=$"
phasemsg: .ascii " phase=$"
sitemsg: .ascii " site=$"
flagsmsg: .ascii " flags=$"
expectedmsg: .ascii " expected=$"
newline: .ascii "\r\n$"
widths:
.byte 0x1,0x1,0x1,0x1,0x1,0x2,0x2,0x2,0x1,0x2
source_bases:
.byte 0x55,0x55,0x55,0x55,0x55,0x11,0x11,0x11,0x11,0x11
counts: .word 0,1,2,3,7,255,256,257
flag_seeds: .word 0x2,0x3,0x6,0x7,0x12,0x13,0x16,0x17,0x42,0x43,0x46,0x47,0x52,0x53,0x56,0x57,0x82,0x83,0x86,0x87,0x92,0x93,0x96,0x97,0xc2,0xc3,0xc6,0xc7,0xd2,0xd3,0xd6,0xd7,0x202,0x203,0x206,0x207,0x212,0x213,0x216,0x217,0x242,0x243,0x246,0x247,0x252,0x253,0x256,0x257,0x282,0x283,0x286,0x287,0x292,0x293,0x296,0x297,0x2c2,0x2c3,0x2c6,0x2c7,0x2d2,0x2d3,0x2d6,0x2d7,0x402,0x403,0x406,0x407,0x412,0x413,0x416,0x417,0x442,0x443,0x446,0x447,0x452,0x453,0x456,0x457,0x482,0x483,0x486,0x487,0x492,0x493,0x496,0x497,0x4c2,0x4c3,0x4c6,0x4c7,0x4d2,0x4d3,0x4d6,0x4d7,0x602,0x603,0x606,0x607,0x612,0x613,0x616,0x617,0x642,0x643,0x646,0x647,0x652,0x653,0x656,0x657,0x682,0x683,0x686,0x687,0x692,0x693,0x696,0x697,0x6c2,0x6c3,0x6c6,0x6c7,0x6d2,0x6d3,0x6d6,0x6d7,0x802,0x803,0x806,0x807,0x812,0x813,0x816,0x817,0x842,0x843,0x846,0x847,0x852,0x853,0x856,0x857,0x882,0x883,0x886,0x887,0x892,0x893,0x896,0x897,0x8c2,0x8c3,0x8c6,0x8c7,0x8d2,0x8d3,0x8d6,0x8d7,0xa02,0xa03,0xa06,0xa07,0xa12,0xa13,0xa16,0xa17,0xa42,0xa43,0xa46,0xa47,0xa52,0xa53,0xa56,0xa57,0xa82,0xa83,0xa86,0xa87,0xa92,0xa93,0xa96,0xa97,0xac2,0xac3,0xac6,0xac7,0xad2,0xad3,0xad6,0xad7,0xc02,0xc03,0xc06,0xc07,0xc12,0xc13,0xc16,0xc17,0xc42,0xc43,0xc46,0xc47,0xc52,0xc53,0xc56,0xc57,0xc82,0xc83,0xc86,0xc87,0xc92,0xc93,0xc96,0xc97,0xcc2,0xcc3,0xcc6,0xcc7,0xcd2,0xcd3,0xcd6,0xcd7,0xe02,0xe03,0xe06,0xe07,0xe12,0xe13,0xe16,0xe17,0xe42,0xe43,0xe46,0xe47,0xe52,0xe53,0xe56,0xe57,0xe82,0xe83,0xe86,0xe87,0xe92,0xe93,0xe96,0xe97,0xec2,0xec3,0xec6,0xec7,0xed2,0xed3,0xed6,0xed7
thunk_ptrs: .word thunk0,thunk1,thunk2,thunk3,thunk4,thunk5,thunk6,thunk7,thunk8,thunk9
