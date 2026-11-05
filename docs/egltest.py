import ctypes as C, os
gbm=C.CDLL("libgbm.so.1"); egl=C.CDLL("libEGL.so.1"); gl=C.CDLL("libGLESv2.so.2")
gbm.gbm_create_device.restype=C.c_void_p; gbm.gbm_create_device.argtypes=[C.c_int]
egl.eglGetProcAddress.restype=C.c_void_p; egl.eglGetProcAddress.argtypes=[C.c_char_p]
fd=os.open("/dev/dri/renderD128",os.O_RDWR)
dev=gbm.gbm_create_device(fd)
GetPD=C.CFUNCTYPE(C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p)(egl.eglGetProcAddress(b"eglGetPlatformDisplayEXT"))
d=GetPD(0x31D7,dev,None)
ma,mi=C.c_int(),C.c_int()
egl.eglInitialize.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
print("init",egl.eglInitialize(d,C.byref(ma),C.byref(mi)))
egl.eglBindAPI(0x30A0)
egl.eglCreateContext.restype=C.c_void_p; egl.eglCreateContext.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
attrs=(C.c_int*3)(0x3098,2,0x3038)
ctx=egl.eglCreateContext(d,None,None,attrs)
egl.eglMakeCurrent.argtypes=[C.c_void_p]*4
print("current",egl.eglMakeCurrent(d,None,None,ctx))
gl.glGetString.restype=C.c_char_p
print("renderer",gl.glGetString(0x1F01))
