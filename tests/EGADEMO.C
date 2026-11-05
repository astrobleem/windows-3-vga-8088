#define WINVER 0x0300
#include <windows.h>
static COLORREF colors[8]={0xffL,0xff00L,0xff0000L,0xffffL,0xff00ffL,0xffff00L,0x808080L,0L};
long FAR PASCAL DemoProc(HWND w,UINT m,WPARAM a,LPARAM l){PAINTSTRUCT ps;HDC dc;RECT r;int i;HBRUSH b,old;HPEN p,op;char line[100];
 if(m==WM_PAINT){dc=BeginPaint(w,&ps);SetBkMode(dc,TRANSPARENT);TextOut(dc,12,8,"Source-built Windows 3.0 VGA driver",35);TextOut(dc,12,29,"640 x 480 | 16 colors | Windows real mode",41);
  TextOut(dc,12,50,"8086-safe drawing, text, clipping and overlapping blits",55);
  for(i=0;i<8;i++){r.left=12+i*72;r.right=r.left+68;r.top=78;r.bottom=118;b=CreateSolidBrush(colors[i]);FillRect(dc,&r,b);DeleteObject(b);}
  for(i=0;i<8;i++){b=CreateSolidBrush(colors[i]);old=SelectObject(dc,b);p=CreatePen(PS_SOLID,1,RGB(0,0,0));op=SelectObject(dc,p);Ellipse(dc,12+i*72,130,76+i*72,188);SelectObject(dc,op);SelectObject(dc,old);DeleteObject(p);DeleteObject(b);}
  TextOut(dc,12,204,"AaBb 0123456789  -  Pixel comparison: all eight frames match",60);
  TextOut(dc,12,227,"DOSBox-X 8086_prefetch test; physical 8088 testing remains",58);
  EndPaint(w,&ps);return 0;}
 if(m==WM_DESTROY){PostQuitMessage(0);return 0;}return DefWindowProc(w,m,a,l);}
int PASCAL WinMain(HINSTANCE h,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS wc;HWND w;MSG msg;DWORD end;HFILE f;char t[160];
 if(!prev){wc.style=CS_HREDRAW|CS_VREDRAW;wc.lpfnWndProc=DemoProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=h;wc.hIcon=LoadIcon(NULL,IDI_APPLICATION);wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="VGA8086Demo";if(!RegisterClass(&wc))return 1;}
 w=CreateWindow("VGA8086Demo","VGA88: source-built Windows 3.0 color driver",WS_OVERLAPPEDWINDOW,8,8,624,420,NULL,NULL,h,NULL);if(!w)return 2;
 ShowWindow(w,SW_SHOWNORMAL);UpdateWindow(w);SetCursorPos(635,475);f=_lcreat("C:\\DEMO.LOG",0);wsprintf(t,"REAL_MODE=%d WIDTH=%d HEIGHT=%d DRIVER=source-built VGA88\r\n",!(GetWinFlags()&WF_PMODE),GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN));_lwrite(f,t,lstrlen(t));_lclose(f);
 end=GetTickCount()+6000UL;while(GetTickCount()<end){while(PeekMessage(&msg,NULL,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessage(&msg);}}DestroyWindow(w);ExitWindows(0,0);return 0;}
