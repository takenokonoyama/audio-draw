import numpy as np
import sys
#プロット関係のライブラリ
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import librosa

#音声関係のライブラリ
import pyaudio

# GUI関係のライブラリ
import pyautogui as pag
from PyQt6.QtGui import QFont

class PlotWindow():
  def __init__(self):
    # グラフ表示用のWidget作成
    self.graph = pg.GraphicsLayoutWidget()
    # ディスプレイサイズに合わせる
    scr_w, scr_h = pag.size()
    print(pag.size())
    self.graph.resize(scr_w, scr_h-90)

    # マイクインプット設定
    self.CHUNK=1024             #1度に読み取る音声のデータ幅
    self.RATE=44100             #サンプリング周波数
    self.audio=pyaudio.PyAudio()
    # streamを開く
    self.stream=self.audio.open(format=pyaudio.paInt16,
                                channels=1,
                                rate=self.RATE,
                                input=True,
                                frames_per_buffer=self.CHUNK)

    # -----------プロット初期設定---------------------
    # 波形のプロット初期設定
    # 縦の設定
    axis_left = pg.AxisItem(orientation="left",maxTickLength=-5)
    # メモリの文字の大きさを変える
    font = QFont()
    font.setPointSize(13)
    axis_left.setTickFont(font)
    
    # 横軸の設定
    axis_bottom = pg.AxisItem(orientation="bottom",maxTickLength=-5)
    # メモリの文字の大きさを変える
    font = QFont()
    font.setPointSize(13)
    axis_bottom.setTickFont(font)
    # 波形プロット用の描画領域追加
    self.plt=self.graph.addPlot(axisItems = {"left":axis_left, "bottom":axis_bottom}) #プロットのビジュアル関係
    self.plt.setTitle('<font size=\'10\'>'+ '音声波形' +'</font>')
    self.plt.setYRange(-32768.0, 32768.0)    #y軸の上限、下限の設定
    self.plt.setMouseEnabled(x=False,y=False) # マウス操作無効
    self.curve=self.plt.plot()  #プロットデータを入れる場所

    # -----------パワースペクトルプロットの初期設定-----------------
    # 縦軸の設定
    axis_left = pg.AxisItem(orientation="left",maxTickLength=-5)
    # メモリの文字の大きさを変える
    font = QFont()
    font.setPointSize(13)
    axis_left.setTickFont(font)
    
    # 横軸の設定
    axis_bottom = pg.AxisItem(orientation="bottom",maxTickLength=-5)
    # メモリの文字の大きさを変える
    font = QFont()
    font.setPointSize(13)
    axis_bottom.setTickFont(font)

    self.plt_power=self.graph.addPlot(axisItems = {"left":axis_left, "bottom":axis_bottom}) #プロットのビジュアル関係
    self.plt_power.setXRange(0, 22050)
    self.plt_power.setMouseEnabled(x=False,y=False)
    self.plt_power.setYRange(0,40)    #y軸の制限
    self.plt_power.setTitle('<font size=\'10\'>'+ '対数パワースペクトル' +'</font>')
    
    self.graph.nextRow() # 次のグラフの描画位置を下に
    # --------------スペクトログラムプロットの初期設定-------------
    # スペクトログラム算出用パラメータ
    self.frame_size = 1024 # フレームサイズ
    self.fft_size = self.frame_size # フレームサイズをfftの区間に(2^nがよい)
    self.frame_shift = 1024 # フレームシフト
    self.num_samples = 5*self.RATE # 解析区間(5秒)内の全データ点の数

    # 短時間フーリエ変換をしたときの5秒分の総フレーム数を計算
    self.num_frames = self.num_samples // self.frame_shift + 1
    
    # スペクトログラム用の行列を用意
    self.spectrogram = np.zeros((self.num_frames, int(self.fft_size/2)+1))
    self.iter      = 0
    
    # 縦軸の設定
    axis_left = pg.AxisItem(orientation="left",maxTickLength=-5)
    freq_axis = np.arange(np.int64(1024/2)+1)*self.RATE / 1024
    # 軸の表示間隔を設定
    yticks = {0:'0', 12:'500',47:'2000', 93:'4000', \
      233:'10000', 279:'12000',349:'15000',372:'16000',396:'17000', \
      418:'18000', 442:'19000', 465:'20000', 488:'21000', 512:'22000'}
    axis_left.setTicks([yticks.items()])
    # メモリの文字の大きさを変える
    font = QFont()
    font.setPointSize(13)
    axis_left.setTickFont(font)
    
    # 横軸の設定
    axis_bottom = pg.AxisItem(orientation="bottom",maxTickLength=-5)
    # メモリの文字の大きさを変える
    font = QFont()
    font.setPointSize(13)
    axis_bottom.setTickFont(font)

    # スペクトログラム描画グラフの追加
    self.specPlot = self.graph.addPlot(colspan=3, axisItems = {"left":axis_left, "bottom":axis_bottom})
    self.specPlot.setTitle('<font size=\'10\'>'+ 'スペクトログラム' +'</font>')
    # 横軸の設定

    # ImageItemの設定
    self.specImage = pg.ImageItem()
    self.specPlot.addItem(self.specImage)
    # カラーマップのセット
    self.cmap = pg.colormap.getFromMatplotlib("jet")
    self.specPlot.addColorBar(self.specImage, colorMap=self.cmap,interactive=True) # , interactive=True)

    # アスペクト比固定
    self.specPlot.setAspectLocked(lock=False)
    # マウス操作無効
    self.specPlot.setMouseEnabled(x=False,y=False)

    # ラベルのセット
    plt_left = '<font size = 10>' + '周波数[Hz]</font>'
    plt_bottom = '<font size = 10>' + 'フレーム</font>'
    self.specPlot.setLabel('left', plt_left)
    self.specPlot.setLabel('bottom', plt_bottom)

    # self.specPlot.disableAutoRange()

    #アップデート時間設定
    self.timer=QtCore.QTimer()
    self.timer.timeout.connect(self.update)
    self.timer.start(50)    #10msごとにupdateを呼び出し

    # ---------音声データの格納場所(プロットデータ)-------
    self.data=np.zeros(self.CHUNK)
    self.axis=np.fft.fftfreq(len(self.data), d=1.0/self.RATE)
    self.graph.show()

    self.graph.ci.layout.setRowStretchFactor(0, 2)
    self.graph.ci.layout.setRowStretchFactor(1, 3)
  # 描画をアップデートする関数
  def update(self):
    # 音声データを受け取る
    input_data = self.AudioInput()
    self.data=np.append(self.data, input_data)
    n = 5
    if len(self.data)/1024 > n:     #n*1024点を超えたら1024点を吐き出し
        self.data=self.data[1024:]
    self.curve.setData(self.data)   #プロットデータを格納

    # パワースペクトルプロット
    # fftデータに変換
    self.fft_data=self.FFT_AMP(self.data)
    # fftデータに対数をとる
    self.fft_data = 2*np.log(self.fft_data+1E-7)

    freq_axis = np.arange(np.int64(len(self.data)/2)+1)*self.RATE / len(self.data)

    self.plt_power.plot(x=freq_axis, y=self.fft_data, clear=True, pen="y")  #symbol="o", symbolPen="y", symbolBrush="b")    
    
    # スペクトログラムプロット
    # 最新をスペクトログラム格納するインデックス
    idx = self.iter % self.num_frames

    # 描画
    pos = idx + 1 if idx < self.num_frames else 0
    self.spectrogram[idx, :] = self.FFT_AMP(input_data)**2
    
    self.specImage.setImage(
    librosa.power_to_db(
        np.r_[self.spectrogram[pos:self.num_frames], 
        self.spectrogram[0:pos]]
    , ref=np.max)
    )

    self.iter += 1
  # 音声の読み取りをする関数
  def AudioInput(self):
    ret=self.stream.read(self.CHUNK)    #音声の読み取り(バイナリ)
    #バイナリ → 数値(int16)に変換
    ret=np.frombuffer(ret, dtype="int16") #32768.0=2^16で割って正規化(絶対値を1以下にすること)してもよい
    return ret

  # FFTを行う関数
  def FFT_AMP(self, data):
    data=np.hamming(len(data))*data
    data=np.fft.fft(data)
    # 半分のデータのみ用いる
    data = data[:np.int64(len(data)/2)+1]
    data=np.abs(data)
    return data

if __name__=="__main__":
    app = pg.mkQApp()
    plotwin=PlotWindow()
    app.exec()

