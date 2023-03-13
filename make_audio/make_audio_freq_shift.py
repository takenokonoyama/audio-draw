import numpy as np
import matplotlib.pyplot as plt
import wave

readfilename = "Costco.wav"
writefilename = "freq_shift.wav"

def float2binary(data, sampwidth):
    data = (data*(2**(8*sampwidth-1)-1)).reshape(data.size, 1) # Normalize (float to int)
    if sampwidth==1:
        data = data+128
        frames = data.astype(np.uint8).tobytes()
    elif sampwidth==2:
        frames = data.astype(np.int16).tobytes()
    elif sampwidth==3:
        a32 = np.asarray(data, dtype = np.int32)
        a8 = (a32.reshape(a32.shape + (1,)) >> np.array([0, 8, 16])) & 255
        frames = a8.astype(np.uint8).tobytes()
    elif sampwidth==4:
        frames = data.astype(np.int32).tobytes()
    return frames

# Costcoの音声の設定をそのまま用いる(Aliceなど適宜変える)
with wave.open(readfilename, "rb") as wr:
    params = wr.getparams()
    ch_num, sampwidth, fr, frame_num, comptype, compname = params
    print(params)
wr.close()

L = int(frame_num / 5)*2 # 4つの周波数の段階があるので信号長を5分割
f = [10000, 12000, 15000, 17000, 19000] # 周波数のシフト
sf = fr # サンプリング周波数
audio_time = frame_num/fr # 作成する音声ファイルの時間(s)
print(int(audio_time))
y = []
t = np.arange(L) * (1/sf) # サンプル取得時間間隔

for i in range(len(f)):
    y.extend(np.array(0.05*np.sin(2*np.pi*f[i]*t))) # sin波取得
y = np.array(y)

file = wave.open(writefilename, "wb") # open file

# 出力音声のパラメータ設定
file.setnchannels(1)
file.setsampwidth(sampwidth)
file.setframerate(sf)
frames = float2binary(y, sampwidth) # float to binary
file.writeframes(frames)

file.close() # close f
