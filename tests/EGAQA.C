#define WINVER 0x0300
#include <windows.h>
#include <conio.h>
#include <string.h>
static int failures;static HFILE logf; static HDC dc,mem;static int w,h,seq;static BYTE chunk[4000];
static COLORREF col[16]={0L,0x800000L,0x008000L,0x808000L,0x000080L,0x800080L,0x008080L,0xc0c0c0L,0x808080L,0xff0000L,0x00ff00L,0xffff00L,0x0000ffL,0xff00ffL,0x00ffffL,0xffffffL};
static void line(char *k,long n){char b[100];wsprintf(b,"%s=%ld\r\n",(LPSTR)k,n);_lwrite(logf,b,lstrlen(b));}
static void flush(void){_lclose(logf);logf=_lopen("C:\\QA.LOG",OF_WRITE);_llseek(logf,0L,2);}
static BOOL qblt(HDC a,int x,int y,int ww,int hh,HDC z,int sx,int sy,DWORD rop){BOOL ok=BitBlt(a,x,y,ww,hh,z,sx,sy,rop);if(!ok){line("BLIT_FAIL",++failures);flush();}return ok;}
#define BitBlt qblt
static void abortqa(void){line("QA_ABORT",1);_lclose(logf);ExitWindows(0,0);}
static void clear(void){SelectClipRgn(dc,NULL);PatBlt(dc,0,0,w,h,WHITENESS);}
static void dump(char *stage){char name[24],b[100];int plane;unsigned at,n,total;HFILE f;BYTE FAR *v=(BYTE FAR *)0xa0000000L;
 wsprintf(b,"STAGE=%s\r\n",(LPSTR)stage);_lwrite(logf,b,lstrlen(b));line("FRAME",seq);
 wsprintf(name,"C:\\P%02d.BIN",seq++);f=_lcreat(name,0);total=(unsigned)(w/8)*h;
 for(plane=0;plane<4;plane++){outp(0x3ce,4);outp(0x3cf,plane);for(at=0;at<total;at+=n){n=total-at;if(n>4000)n=4000;_fmemcpy((LPSTR)chunk,(LPSTR)(v+at),n);_lwrite(f,(LPSTR)chunk,n);}}
 outp(0x3ce,4);outp(0x3cf,0);_lclose(f);flush();}
static void pattern(HDC d,int ww,int hh){int i;HBRUSH b,old;for(i=0;i<16;i++){b=CreateSolidBrush(col[i]);old=SelectObject(d,b);PatBlt(d,i*ww/16,0,(i+1)*ww/16-i*ww/16,hh,PATCOPY);SelectObject(d,old);DeleteObject(b);}}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){HBITMAP bm,oldbm;int i,s,d;HRGN clip;HPEN p,op;HBRUSH b,ob;DWORD rops[15]={BLACKNESS,NOTSRCERASE,NOTSRCCOPY,SRCERASE,DSTINVERT,PATINVERT,SRCINVERT,SRCAND,MERGEPAINT,MERGECOPY,SRCCOPY,SRCPAINT,PATCOPY,PATPAINT,WHITENESS};
 logf=_lcreat("C:\\QA.LOG",0);dc=GetDC(NULL);w=GetSystemMetrics(SM_CXSCREEN);h=GetSystemMetrics(SM_CYSCREEN);line("REAL_MODE",!(GetWinFlags()&WF_PMODE));line("WIDTH",w);line("HEIGHT",h);line("COLORS",GetDeviceCaps(dc,NUMCOLORS));flush();
 if(h!=480||w!=640){line("CONTROL_BOOT",GetDeviceCaps(dc,NUMCOLORS)==2 && w==640 && h==200 && !(GetWinFlags()&WF_PMODE));_lclose(logf);ReleaseDC(NULL,dc);ExitWindows(0,0);return 0;}
 if(GetDeviceCaps(dc,NUMCOLORS)!=16 || (GetWinFlags()&WF_PMODE)){abortqa();return 0;}
 ShowCursor(FALSE);SetCursor(NULL);clear();pattern(dc,w,h);dump("palette");
 mem=CreateCompatibleDC(dc);bm=CreateCompatibleBitmap(dc,160,80);oldbm=SelectObject(mem,bm);if(!mem||!bm||!oldbm){abortqa();return 0;}pattern(mem,160,80);
 clear();for(s=0;s<8;s++)for(d=0;d<8;d++)BitBlt(dc,d*72+d,s*40,64,32,mem,s,0,SRCCOPY);dump("phase_memory_screen");
 clear();for(i=0;i<15;i++){b=CreateSolidBrush(col[(i+3)&15]);ob=SelectObject(dc,b);BitBlt(dc,(i%5)*128,(i/5)*100,125,95,mem,3,1,rops[i]);SelectObject(dc,ob);DeleteObject(b);}dump("rop3_15");
 clear();for(i=1;i<=16;i++){SetROP2(dc,i);p=CreatePen(PS_SOLID,1,col[i&15]);op=SelectObject(dc,p);MoveTo(dc,4,i*20);LineTo(dc,630,i*20+14);Rectangle(dc,i*33,10,i*33+45,330);SelectObject(dc,op);DeleteObject(p);}SetROP2(dc,R2_COPYPEN);dump("rop2_16");
 clear();pattern(dc,w,h);BitBlt(dc,7,9,600,300,dc,0,0,SRCCOPY);BitBlt(dc,0,0,590,290,dc,13,17,SRCCOPY);BitBlt(dc,15,0,600,280,dc,0,0,SRCCOPY);BitBlt(dc,0,15,580,290,dc,9,0,SRCCOPY);dump("overlap_four_directions");
 clear();clip=CreateRectRgn(17,23,603,311);SelectClipRgn(dc,clip);BitBlt(dc,-11,7,160,80,mem,0,0,SRCCOPY);for(i=0;i<8;i++)BitBlt(dc,i*80-3,i*37-8,160,80,mem,7-i,0,SRCINVERT);SelectClipRgn(dc,NULL);DeleteObject(clip);dump("clipping");
 clear();SetBkMode(dc,OPAQUE);for(i=0;i<16;i++){SetTextColor(dc,col[i]);SetBkColor(dc,col[15-i]);TextOut(dc,3+i%8,i*20,"Windows 3.0 VGA 8088: Abc 0123456789",36);}dump("text");
 clear();pattern(dc,w,h);for(s=0;s<8;s++){BitBlt(mem,s,0,128,64,dc,s+7,s*30,SRCCOPY);BitBlt(dc,s*75,s*25,128,64,mem,s,0,SRCINVERT);}BitBlt(dc,503,409,128,64,mem,1,0,SRCCOPY);BitBlt(dc,0,465,160,32,mem,0,0,SRCINVERT);dump("screen_memory_screen");
 SelectObject(mem,oldbm);DeleteObject(bm);DeleteDC(mem);line("FAILURES",failures);line("COMPLETE",failures==0);_lclose(logf);ReleaseDC(NULL,dc);ShowCursor(TRUE);ExitWindows(0,0);return 0;
}
