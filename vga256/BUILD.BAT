@echo off
SET INCLUDE=R:\INC;R:\SRC
SET LIB=R:\LIB
R:
CD \SRC
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T bitblt.ASM,bitblt.OBJ,bitblt.LST; > bitblt.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T bmc_eti.ASM,bmc_eti.OBJ,bmc_eti.LST; > bmc_eti.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T bmc_ite.ASM,bmc_ite.OBJ,bmc_ite.LST; > bmc_ite.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T bmc_main.ASM,bmc_main.OBJ,bmc_main.LST; > bmc_main.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T buildstr.ASM,buildstr.OBJ,buildstr.LST; > buildstr.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T cblt.ASM,cblt.OBJ,cblt.LST; > cblt.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T charwdth.ASM,charwdth.OBJ,charwdth.LST; > charwdth.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T chkstk.ASM,chkstk.OBJ,chkstk.LST; > chkstk.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T colorinf.ASM,colorinf.OBJ,colorinf.LST; > colorinf.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T control.ASM,control.OBJ,control.LST; > control.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T cursor.ASM,cursor.OBJ,cursor.LST; > cursor.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T cursors.ASM,cursors.OBJ,cursors.LST; > cursors.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T disable.ASM,disable.OBJ,disable.LST; > disable.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T discreen.ASM,discreen.OBJ,discreen.LST; > discreen.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T -DHIRES dither.ASM,dither.OBJ,dither.LST; > dither.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T egainit.ASM,egainit.OBJ,egainit.LST; > egainit.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T enable.ASM,enable.OBJ,enable.LST; > enable.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T enum.ASM,enum.OBJ,enum.LST; > enum.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T fb.ASM,fb.OBJ,fb.LST; > fb.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T getrle.ASM,getrle.OBJ,getrle.LST; > getrle.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T inquire.ASM,inquire.OBJ,inquire.LST; > inquire.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T pixel.ASM,pixel.OBJ,pixel.LST; > pixel.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T output.ASM,output.OBJ,output.LST; > output.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T polyline.ASM,polyline.OBJ,polyline.LST; > polyline.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T rgb2ipc.ASM,rgb2ipc.OBJ,rgb2ipc.LST; > rgb2ipc.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T rlecom.ASM,rlecom.OBJ,rlecom.LST; > rlecom.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T rledat.ASM,rledat.OBJ,rledat.LST; > rledat.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T robject.ASM,robject.OBJ,robject.LST; > robject.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T scanline.ASM,scanline.OBJ,scanline.LST; > scanline.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T scanlr.ASM,scanlr.OBJ,scanlr.LST; > scanlr.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T setmode.ASM,setmode.OBJ,setmode.LST; > setmode.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T smartpro.ASM,smartpro.OBJ,smartpro.LST; > smartpro.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T sswitch.ASM,sswitch.OBJ,sswitch.LST; > sswitch.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T strblt.ASM,strblt.OBJ,strblt.LST; > strblt.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T setrle.ASM,setrle.OBJ,setrle.LST; > setrle.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T tracer.ASM,tracer.OBJ,tracer.LST; > tracer.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T trn_pal.ASM,trn_pal.OBJ,trn_pal.LST; > trn_pal.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T vgastate.ASM,vgastate.OBJ,vgastate.LST; > vgastate.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T vga.ASM,vga.OBJ,vga.LST; > vga.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T 3xswitch.ASM,3xswitch.OBJ,3xswitch.LST; > 3xswitch.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T stretch.ASM,stretch.OBJ,stretch.LST; > stretch.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -I. -DPUBDEFS -DVGA200 -DPALETTES -D?QUIET -ML -W2 -T -DHIRES dithers.ASM,dithers.OBJ,dithers.LST; > dithers.LOG
if errorlevel 1 goto FAILED
R:\BIN\LINK4 @VGA256.LNK > LINK.LOG
if errorlevel 1 goto FAILED
CD \RES
R:\BIN\MASM -LA -T CONFIG.ASM,CONFIG.OBJ,CONFIG.LST; > CONFIG.LOG
if errorlevel 1 goto FAILED
R:\BIN\LINK4 CONFIG.OBJ,CONFIG.EXE,NUL,,; >> CONFIG.LOG
if errorlevel 1 goto FAILED
R:\BIN\EXE2BIN CONFIG.EXE CONFIG.BIN >> CONFIG.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -T COLORTAB.ASM,COLORTAB.OBJ,COLORTAB.LST; > COLORTAB.LOG
if errorlevel 1 goto FAILED
R:\BIN\LINK4 COLORTAB.OBJ,COLORTAB.EXE,NUL,,; >> COLORTAB.LOG
if errorlevel 1 goto FAILED
R:\BIN\EXE2BIN COLORTAB.EXE COLORTAB.BIN >> COLORTAB.LOG
if errorlevel 1 goto FAILED
R:\BIN\MASM -LA -T FONTS.ASM,FONTS.OBJ,FONTS.LST; > FONTS.LOG
if errorlevel 1 goto FAILED
R:\BIN\LINK4 FONTS.OBJ,FONTS.EXE,NUL,,; >> FONTS.LOG
if errorlevel 1 goto FAILED
R:\BIN\EXE2BIN FONTS.EXE FONTS.BIN >> FONTS.LOG
if errorlevel 1 goto FAILED
echo Finished > DONE.TXT
goto END
:FAILED
echo Build failed. Check the compiler logs.
:END
exit
