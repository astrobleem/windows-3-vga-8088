#define WINVER 0x0300
#include <windows.h>
#include <conio.h>
#include <string.h>
/* All drawing below goes through Win16 GDI. A000 reads are observation only. */
static HFILE logf;
static HDC dc,mem;
static HWND hwnd;
long FAR PASCAL ProbeWndProc(HWND w,WORD m,WORD p,LONG q){return DefWindowProc(w,m,p,q);}
static int failures,seq;
static BYTE chunk[4000],reference[4096],seen[256],dac[768];
static PALETTEENTRY expected[256];
static BYTE monoBits[32];
static struct { WORD version,count; PALETTEENTRY entry[256]; } pal;
static BYTE FAR *video=(BYTE FAR *)0xa0000000L;
static void line(char *key,long n){char b[100];wsprintf(b,"%s=%ld\r\n",(LPSTR)key,n);_lwrite(logf,b,lstrlen(b));}
static void check(char *key,int ok){line(key,ok);if(!ok)failures++;}
static void flush(void){_lclose(logf);logf=_lopen("C:\\V256QA.LOG",OF_WRITE);_llseek(logf,0L,2);}
static int distance(int a,int b){return a>b?a-b:b-a;}
static int samecolor(COLORREF c,PALETTEENTRY *p){return c!=0xffffffffL && distance(GetRValue(c),p->peRed)<=3 && distance(GetGValue(c),p->peGreen)<=3 && distance(GetBValue(c),p->peBlue)<=3;}
static int blt(HDC dst,int x,int y,int w,int h,HDC src,int sx,int sy){int ok=BitBlt(dst,x,y,w,h,src,sx,sy,SRCCOPY);if(!ok){line("BITBLT_FAILED",1);failures++;}return ok;}
static void grid(int cellw,int cellh){int i;HBRUSH b,old;for(i=0;i<256;i++){b=CreateSolidBrush(PALETTEINDEX(i));if(!b){failures++;continue;}old=SelectObject(dc,b);if(!PatBlt(dc,(i&15)*cellw,(i>>4)*cellh,cellw,cellh,PATCOPY))failures++;SelectObject(dc,old);DeleteObject(b);}}
static void capture(int x,int y){int r,c;for(r=0;r<64;r++)for(c=0;c<64;c++)reference[r*64+c]=video[(unsigned)(y+r)*320+x+c];}
static int compare(int x,int y,int w,int h,int rx,int ry){int r,c;long bad=0;for(r=0;r<h;r++)for(c=0;c<w;c++)if(video[(unsigned)(y+r)*320+x+c]!=reference[(ry+r)*64+rx+c])bad++;line("MISMATCH_PIXELS",bad);return bad==0;}
static void dump(char *stage){HFILE f;char name[24],b[100];unsigned at,n;int i,ok=1;
 wsprintf(b,"STAGE=%s\r\n",(LPSTR)stage);_lwrite(logf,b,lstrlen(b));line("FRAME",seq);
 wsprintf(name,"C:\\V%02d.BIN",seq);f=_lcreat(name,0);if(f==HFILE_ERROR)ok=0;else {for(at=0;at<64000U;at+=n){n=64000U-at;if(n>4000)n=4000;_fmemcpy((LPSTR)chunk,(LPSTR)(video+at),n);if(_lwrite(f,(LPSTR)chunk,n)!=n)ok=0;}_lclose(f);}
 outp(0x3c7,0);for(i=0;i<768;i++)dac[i]=(BYTE)inp(0x3c9);
 wsprintf(name,"C:\\V%02d.DAC",seq++);f=_lcreat(name,0);if(f==HFILE_ERROR)ok=0;else {if(_lwrite(f,(LPSTR)dac,768)!=768)ok=0;_lclose(f);}check("DUMP_IO",ok);flush();}
/* Ordinary RGB brushes exercise color matching independently of PALETTEINDEX. */
static void systemRGB(void){int n,i,x,y,idx,bad,cases=0,rawbad=0,dacbad=0,pixelbad=0,nearestbad=0;HBRUSH b,old;COLORREF rgb,pixel,nearest;
 outp(0x3c7,0);for(i=0;i<768;i++)dac[i]=(BYTE)inp(0x3c9);
 for(n=0;n<20;n++){i=n<10?n:n+236;rgb=RGB(expected[i].peRed,expected[i].peGreen,expected[i].peBlue);b=CreateSolidBrush(rgb);
 if(!b){line("RGB_BRUSH_CREATE_FAILED",i);failures++;continue;}old=SelectObject(dc,b);check("RGB_PATCH_PATBLT",PatBlt(dc,128,80,8,8,PATCOPY)!=0);SelectObject(dc,old);DeleteObject(b);bad=0;
 for(y=0;y<8;y++)for(x=0;x<8;x++){idx=video[(unsigned)(80+y)*320+128+x];if(idx!=i){rawbad++;bad=1;}if(distance(dac[idx*3]*4,expected[i].peRed)>3 || distance(dac[idx*3+1]*4,expected[i].peGreen)>3 || distance(dac[idx*3+2]*4,expected[i].peBlue)>3){dacbad++;bad=1;}}
 pixel=GetPixel(dc,132,84);nearest=GetNearestColor(dc,rgb);if(!samecolor(pixel,&expected[i])){pixelbad++;bad=1;}if(!samecolor(nearest,&expected[i])){nearestbad++;bad=1;}cases++;
 if(bad){line("RGB_FAILED_SYSTEM_INDEX",i);line("RGB_ACTUAL_CENTER_INDEX",video[84U*320+132]);line("RGB_REQUEST",rgb);line("RGB_GETPIXEL",pixel);line("RGB_GETNEARESTCOLOR",nearest);}}
 line("RGB_SYSTEM_CASES",cases);line("RGB_RAW_INDEX_MISMATCHES",rawbad);line("RGB_DAC_MISMATCHES",dacbad);line("RGB_GETPIXEL_MISMATCHES",pixelbad);line("RGB_NEAREST_MISMATCHES",nearestbad);
 check("RGB_ALL_20_SYSTEM_COLORS",cases==20 && rawbad==0 && dacbad==0 && pixelbad==0 && nearestbad==0);flush();}
/* A monochrome zero bit expands to destination text color, one to background. */
static int monoBit(int x,int y){return ((x*5+y*3+(x>>2))&7)<3;}
static void monoPhases(HPALETTE hp){HDC src, dst;HBITMAP mb, cb, om, oc;HPALETTE op;int x,y,phase,width,swap,fg,bg,bad,cases;BYTE fi,bi,want;long mismatches=0;
 memset(monoBits,0,sizeof(monoBits));for(y=0;y<8;y++)for(x=0;x<32;x++)if(monoBit(x,y))monoBits[y*4+x/8]|=(BYTE)(0x80>>(x&7));
 src=CreateCompatibleDC(dc);dst=CreateCompatibleDC(dc);mb=CreateBitmap(32,8,1,1,(LPSTR)monoBits);cb=CreateCompatibleBitmap(dc,32,8);
 check("MONO_DC_CREATE",src!=NULL && dst!=NULL);check("MONO_BITMAP_CREATE",mb!=NULL && cb!=NULL);
 if(!src || !dst || !mb || !cb){if(src)DeleteDC(src);if(dst)DeleteDC(dst);if(mb)DeleteObject(mb);if(cb)DeleteObject(cb);return;}
 om=SelectObject(src,mb);oc=SelectObject(dst,cb);op=SelectPalette(dst,hp,FALSE);RealizePalette(dst);grid(4,4);cases=0;
 for(swap=0;swap<2;swap++){fg=swap?213:12;bg=swap?12:213;fi=video[(unsigned)((fg>>4)*4+1)*320+(fg&15)*4+1];bi=video[(unsigned)((bg>>4)*4+1)*320+(bg&15)*4+1];check("MONO_FG_BG_DISTINCT",fi!=bi);
 SetTextColor(dc,PALETTEINDEX(fg));SetBkColor(dc,PALETTEINDEX(bg));SetTextColor(dst,PALETTEINDEX(fg));SetBkColor(dst,PALETTEINDEX(bg));
 for(phase=0;phase<8;phase++)for(width=1;width<=17;width++){bad=0;blt(dc,90,70,width,8,src,phase,0);blt(dst,0,0,width,8,src,phase,0);blt(dc,160,70,width,8,dst,0,0);
 for(y=0;y<8;y++)for(x=0;x<width;x++){want=monoBit(phase+x,y)?bi:fi;if(video[(unsigned)(70+y)*320+90+x]!=want)bad++;if(video[(unsigned)(70+y)*320+160+x]!=want)bad++;}
 cases++;if(bad && mismatches==0){line("MONO_FIRST_SWAP",swap);line("MONO_FIRST_PHASE",phase);line("MONO_FIRST_WIDTH",width);line("MONO_FIRST_MISMATCHES",bad);}mismatches+=bad;}}
 line("MONO_PHASE_CASES",cases);line("MONO_MISMATCH_PIXELS",mismatches);check("MONO_SCREEN_AND_MEMORY",mismatches==0 && cases==272);
 SelectPalette(dst,op,FALSE);SelectObject(src,om);SelectObject(dst,oc);DeleteObject(mb);DeleteObject(cb);DeleteDC(src);DeleteDC(dst);flush();}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){HPALETTE hp,oldpal,oldmem;HBITMAP bm,oldbm;int i,j,idx,ok,unique;long changed;UINT realized; WNDCLASS wc;
 logf=_lcreat("C:\\V256QA.LOG",0);if(logf==HFILE_ERROR){ExitWindows(0,0);return 0;}memset(&wc,0,sizeof(wc));wc.lpfnWndProc=ProbeWndProc;wc.hInstance=inst;wc.hbrBackground=GetStockObject(BLACK_BRUSH);wc.lpszClassName="V256PROBE";RegisterClass(&wc);hwnd=CreateWindow("V256PROBE","VGA256",WS_POPUP,0,0,320,200,NULL,NULL,inst,NULL);if(!hwnd){line("NO_WINDOW",1);_lclose(logf);ExitWindows(0,0);return 0;}ShowWindow(hwnd,SW_SHOW);UpdateWindow(hwnd);SetActiveWindow(hwnd);dc=GetDC(hwnd);if(!dc){line("NO_SCREEN_DC",1);_lclose(logf);ExitWindows(0,0);return 0;}
 line("WIDTH",GetDeviceCaps(dc,HORZRES));line("HEIGHT",GetDeviceCaps(dc,VERTRES));line("BITSPIXEL",GetDeviceCaps(dc,BITSPIXEL));line("PLANES",GetDeviceCaps(dc,PLANES));line("SIZEPALETTE",GetDeviceCaps(dc,SIZEPALETTE));line("RASTERCAPS",GetDeviceCaps(dc,RASTERCAPS));line("NUMCOLORS",GetDeviceCaps(dc,NUMCOLORS));line("WINFLAGS",GetWinFlags());line("APP_GETVERSION",GetVersion());
 check("REAL_MODE",!(GetWinFlags()&WF_PMODE));check("CAPS_320X200",GetDeviceCaps(dc,HORZRES)==320 && GetDeviceCaps(dc,VERTRES)==200);check("CAPS_PACKED8",GetDeviceCaps(dc,BITSPIXEL)==8 && GetDeviceCaps(dc,PLANES)==1);check("CAPS_PALETTE256",GetDeviceCaps(dc,SIZEPALETTE)==256);check("CAPS_RC_PALETTE",(GetDeviceCaps(dc,RASTERCAPS)&RC_PALETTE)!=0);flush();if(failures)goto done;
 check("SYSTEM_PALETTE_READ",GetSystemPaletteEntries(dc,0,256,expected)==256);if(failures)goto done;
 pal.version=0x300;pal.count=256;for(i=0;i<256;i++){if(i<10 || i>=246){pal.entry[i].peRed=(BYTE)i;pal.entry[i].peGreen=0;pal.entry[i].peBlue=0;pal.entry[i].peFlags=PC_EXPLICIT;}else {j=i-10;expected[i].peRed=(BYTE)((j%6)*40+8);expected[i].peGreen=(BYTE)(((j/6)%6)*40+8);expected[i].peBlue=(BYTE)((j/36)*32+8);pal.entry[i]=expected[i];pal.entry[i].peFlags=PC_NOCOLLAPSE;}}
 hp=CreatePalette((LOGPALETTE FAR *)&pal);check("CREATE_PALETTE",hp!=NULL);if(!hp)goto done;oldpal=SelectPalette(dc,hp,FALSE);realized=RealizePalette(dc);line("REALIZE_PALETTE_CHANGED",realized);check("REALIZE_NOT_ERROR",realized!=(UINT)-1);
 ShowCursor(FALSE);SetCursor(NULL);PatBlt(dc,0,0,320,200,BLACKNESS);grid(20,12);dump("palette_256");
 memset(seen,0,sizeof(seen));ok=1;for(i=0;i<256;i++){idx=video[(unsigned)((i>>4)*12+6)*320+(i&15)*20+10];seen[idx]=1;if(!samecolor(GetPixel(dc,(i&15)*20+10,(i>>4)*12+6),&expected[i]))ok=0;if(distance(dac[idx*3]*4,expected[i].peRed)>3 || distance(dac[idx*3+1]*4,expected[i].peGreen)>3 || distance(dac[idx*3+2]*4,expected[i].peBlue)>3)ok=0;}
 unique=0;for(i=0;i<256;i++)unique+=seen[i]!=0;line("DISTINCT_PIXEL_INDICES",unique);check("ALL_256_INDICES",unique==256);check("PALETTE_RGB_MATCH",ok);
 systemRGB();
 mem=CreateCompatibleDC(dc);bm=CreateCompatibleBitmap(dc,64,64);check("CREATE_MEMORY_DC",mem!=NULL);check("CREATE_BITMAP",bm!=NULL);if(mem && bm){oldbm=SelectObject(mem,bm);oldmem=SelectPalette(mem,hp,FALSE);RealizePalette(mem);grid(4,4);capture(0,0);blt(mem,0,0,64,64,dc,0,0);PatBlt(dc,0,0,64,64,BLACKNESS);blt(dc,128,96,64,64,mem,0,0);check("SCREEN_MEMORY_SCREEN",compare(128,96,64,64,0,0));SelectPalette(mem,oldmem,FALSE);SelectObject(mem,oldbm);}
 if(bm)DeleteObject(bm);if(mem)DeleteDC(mem);
 monoPhases(hp);
 grid(4,4);capture(0,0);blt(dc,7,0,57,64,dc,0,0);check("OVERLAP_RIGHT",compare(7,0,57,64,0,0));
 grid(4,4);capture(0,0);blt(dc,0,0,57,64,dc,7,0);check("OVERLAP_LEFT",compare(0,0,57,64,7,0));
 grid(4,4);capture(0,0);blt(dc,0,9,64,55,dc,0,0);check("OVERLAP_DOWN",compare(0,9,64,55,0,0));
 grid(4,4);capture(0,0);blt(dc,0,0,64,55,dc,0,9);check("OVERLAP_UP",compare(0,0,64,55,0,9));dump("overlap");
 PatBlt(dc,0,0,320,200,BLACKNESS);SetBkMode(dc,TRANSPARENT);SetTextColor(dc,PALETTEINDEX(255));capture(0,0);check("TEXTOUT_RETURN",TextOut(dc,1,1,"Win3 VGA256",11));changed=0;for(i=0;i<64;i++)for(j=0;j<64;j++)if(video[(unsigned)i*320+j]!=reference[i*64+j])changed++;line("TEXT_CHANGED_PIXELS",changed);check("TEXT_VISIBLE",changed>10);dump("text");
 grid(20,12);dump("final_palette_256");SelectPalette(dc,oldpal,FALSE);DeleteObject(hp);ShowCursor(TRUE);
 done:line("FAILURES",failures);line("COMPLETE",failures==0);_lclose(logf);ReleaseDC(hwnd,dc);DestroyWindow(hwnd);ExitWindows(0,0);return 0;
}
